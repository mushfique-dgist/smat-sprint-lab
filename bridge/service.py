"""Single-writer bootstrap bridge. No getUpdates in send-only mode."""
import fcntl, json, os, subprocess, sys, time
from datetime import datetime, timezone
from smatsprint.needs import NEEDS, ROOT, atomic_json, validate
from ops.fallback import dgist_send
from smatsprint.needs import create
from bridge import drop, full

GH="/home/aurnab/.local/share/smatsprint/bin/gh"
def now(): return datetime.now(timezone.utc).isoformat()
def record(n,cause):
    p=NEEDS/"events.jsonl"
    with p.open("a",encoding="utf8") as out:
        out.write(json.dumps({"at":now(),"need_id":n["need_id"],"status":n["status"],"version":n["version"],"cause":cause})+"\n")
        out.flush(); os.fsync(out.fileno())
def save(n,cause):
    atomic_json(NEEDS/(n["need_id"]+".json"),n)
    record(n,cause)
def gh_auth():
    env={"PATH":"/usr/local/bin:/usr/bin:/bin","HOME":"/home/aurnab",
         "GH_CONFIG_DIR":"/home/aurnab/.config/smatsprint/gh","GH_PROMPT_DISABLED":"1"}
    try:
        u=subprocess.run([GH,"api","user","--jq",".login"],env=env,capture_output=True,text=True,timeout=30)
        s=subprocess.run([GH,"auth","status"],env=env,capture_output=True,text=True,timeout=30)
        ok=u.returncode==0 and u.stdout.strip()=="mushfique-dgist" and s.returncode==0 and "repo" in s.stderr+s.stdout and "workflow" in s.stderr+s.stdout
        return ok
    except (OSError,subprocess.TimeoutExpired): return False
def message(n):
    lines=["[SMAT-Sprint build] "+("Phone" if n["kind"]=="phone" else "PC only")+": "+n["title"],n["what"]+" "+n["why"]]
    lines += [str(i)+". "+s.replace("{need_id}",n["need_id"]) for i,s in enumerate(n["steps_phone"],1)]
    if n.get("blocking"): lines.append("Everything else is continuing; only "+", ".join(n["blocking"])+" waits.")
    if n.get("steps_pc"):
        lines.append("PC fallback: "+"; ".join(n["steps_pc"]))
    lines += ["Need "+n["need_id"][-4:],"Do not reply to the DGIST bot; that chat belongs to the course service."]
    text="\n".join(lines)
    if len(text)>1500: raise ValueError("message length")
    return text
def send(n):
    text=message(n)
    mode=json.loads(full.MODE.read_text()).get("mode","send_only") if full.MODE.exists() else "send_only"
    if mode=="full":
        try:
            mid,nonce=full.send_need(n,text)
            n["telegram"]["message_ids"].append(mid)
            n["telegram"]["nonce"]=nonce
            n["telegram"]["last_text"]=text
            channel="programme_bot"
        except Exception:
            dgist_send.send_email("SMAT-Sprint: action needed on your phone",text); channel="gmail"
    else:
        try: dgist_send.send_telegram(text); channel="dgist"
        except Exception:
            dgist_send.send_email("SMAT-Sprint: action needed on your phone",text); channel="gmail"
    n["telegram"]["last_sent_at"]=now()
    n["telegram"]["sent_count"]+=1
    n["telegram"]["channel"]=channel
    n["version"]+=1
    save(n,"sent:"+channel)
def process(req):
    nid=req["need_id"]
    p=NEEDS/(nid+".json")
    if req["op"]=="create":
        if p.exists(): return
        s=req["spec"]; validate(s)
        n=dict(s)
        n.update({"schema_version":1,"need_id":nid,"created_at":now(),"status":"open",
                  "version":1,"snoozed_until":None,"pending_action":None,"resolution":None,
                  "telegram":{"message_ids":[],"nonce":None,"last_sent_at":None,"sent_count":0}})
        save(n,"created")
        return
    if not p.exists(): raise ValueError("unknown need")
    n=json.loads(p.read_text(encoding="utf8"))
    if n["status"]!="open" or n["version"]!=req["expected_version"]: raise ValueError("stale request")
    if req["op"]=="cancel":
        n["status"]="cancelled"
        n["resolution"]={"how":"cancel","at":now(),"detail":req.get("reason","")}
    elif req["op"]=="set_drop_kind":
        if n["title"]!="Create SMAT Sprint bot, part 1" or req.get("drop_kind")!="telegram-bot-token": raise ValueError("wrong need")
        n["drop_kind"]="telegram-bot-token"
    elif req["op"]=="check_now":
        if not n.get("check"): raise ValueError("no check")
        n["next_check_at"]=now()
    else: raise ValueError("unknown operation")
    n["version"]+=1; save(n,req["op"])
last_issue_check=0

def tick():
    global last_issue_check
    for p in sorted((NEEDS/"requests").glob("*.json")):
        try:
            process(json.loads(p.read_text(encoding="utf8")))
            p.unlink()
        except Exception as e:
            p.replace(NEEDS/"rejected"/p.name)
            print("need request rejected: "+type(e).__name__,file=sys.stderr)
    if time.time()-last_issue_check>=60:
        last_issue_check=time.time()
        try:
            accepted,rejected=drop.consume_issues()
            for nid in rejected:
                create({"code":"build","kind":"phone","title":"Encrypted drop could not be used",
                        "what":"The encrypted issue for need "+nid[-4:]+" did not pass the lab checks.",
                        "why":"No token was installed. GitHub deletion is retried until it succeeds.",
                        "steps_phone":["Open the latest drop link from your phone need and submit a fresh encrypted issue."],
                        "steps_pc":[],"blocking":[],"check":None,"reply":"none",
                        "blocks_build":False,"created_by":"bridge","expires_at":None,
                        "deadline":None,"consequential":False,"skippable":False})
        except Exception:
            print("drop issue check failed",file=sys.stderr)
    # The same durable stage is populated by a phone drop or the local PC
    # fallback. Finish it after a bridge restart as well.
    if drop.STAGED.exists():
        try:
            staged=json.loads(drop.STAGED.read_text())
            nid=staged["need_id"]
            p=NEEDS/(nid+".json")
            n=json.loads(p.read_text(encoding="utf8"))
            if n["status"]=="open":
                n["status"]="resolved"
                n["resolution"]={"how":"check","at":now(),"detail":"encrypted token staged and bot identity checked"}
                n["version"]+=1; save(n,"drop:staged")
            exists=any(x.get("title")=="Start SMAT Sprint bot, part 2" for x in (
                json.loads(q.read_text()) for q in NEEDS.glob("n-*.json")))
            queued=any(x.get("spec",{}).get("title")=="Start SMAT Sprint bot, part 2" for x in (
                json.loads(q.read_text()) for q in (NEEDS/"requests").glob("*.json")))
            if not exists and not queued:
                create({"code":"build","kind":"phone","title":"Start SMAT Sprint bot, part 2",
                        "what":"Start the new bot so I can verify that it reaches your private Telegram chat.",
                        "why":"The token alone does not prove ownership of the chat.",
                        "steps_phone":["Open https://t.me/"+staged["username"],
                                       "Tap Start, or send /start. Do not paste the token into chat."],
                        "steps_pc":[],"blocking":["full phone bot connection"],
                        "check":{"id":"bot_owner_verified","args":{}},"reply":"done",
                        "blocks_build":False,"created_by":"bridge","expires_at":None,
                        "deadline":None,"consequential":False,"skippable":False})
        except Exception:
            print("staged bot processing failed",file=sys.stderr)
    for p in sorted(NEEDS.glob("n-*.json")):
        n=json.loads(p.read_text(encoding="utf8"))
        if n["status"]!="open": continue
        c=n.get("check")
        if c and c["id"] in ("gh_auth","bot_owner_verified"):
            last=n.get("last_check_at")
            due=last is None or time.time()-datetime.fromisoformat(last).timestamp()>=60 or n.pop("next_check_at",None)
            if due:
                if c["id"]=="gh_auth": ok=gh_auth(); detail="logged in as mushfique-dgist"
                else:
                    try: ok,username=drop.check_owner()
                    except Exception: ok=False; username=None
                    ok = ok and (ROOT/"state/bridge/full_test_passed.json").exists()
                    detail="owner verified for "+username if username else "bot owner not verified"
                    if ok:
                        atomic_json(full.MODE,{"mode":"full","at":now()})
                n["last_check_at"]=now()
                if ok:
                    n["status"]="resolved"
                    n["resolution"]={"how":"check","at":now(),"detail":detail}
                n["version"]+=1; save(n,"check:passed" if ok else "check:pending")
        if n["status"]=="open" and n.get("snoozed_until"):
            if datetime.fromisoformat(n["snoozed_until"])<=datetime.now(timezone.utc):
                n["snoozed_until"]=None
                n["telegram"]["last_sent_at"]=None
                n["version"]+=1; save(n,"snooze-ended")
        if n["status"]=="open" and not n["telegram"]["last_sent_at"]:
            try: send(n)
            except Exception: print("need send failed: "+n["need_id"],file=sys.stderr)
    mode=json.loads(full.MODE.read_text()).get("mode","send_only") if full.MODE.exists() else "send_only"
    atomic_json(ROOT/"state/bridge/heartbeat.json",{"at":now(),"mode":mode})
def main():
    NEEDS.mkdir(parents=True,exist_ok=True)
    for d in ("requests","rejected"): (NEEDS/d).mkdir(exist_ok=True)
    with (NEEDS/"bridge.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not full.MODE.exists():
            atomic_json(full.MODE,{"mode":"send_only"})
        first_full=True
        while True:
            tick()
            mode=json.loads(full.MODE.read_text()).get("mode","send_only")
            if mode=="full":
                try:
                    full.poll_once(save,first=first_full)
                    first_full=False
                except Exception:
                    print("programme bot poll failed",file=sys.stderr)
                    time.sleep(5)
            else: time.sleep(5)
if __name__=="__main__": main()
