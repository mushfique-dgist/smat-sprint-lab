"""Single-writer bootstrap bridge. No getUpdates in send-only mode."""
import fcntl, json, os, subprocess, sys, time
from datetime import datetime, timezone
from smatsprint.needs import NEEDS, ROOT, atomic_json, validate
from ops.fallback import dgist_send

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
    lines += [str(i)+". "+s for i,s in enumerate(n["steps_phone"],1)]
    if n.get("blocking"): lines.append("Everything else is continuing; only "+", ".join(n["blocking"])+" waits.")
    lines += ["Need "+n["need_id"][-4:],"Do not reply to the DGIST bot; that chat belongs to the course service."]
    text="\n".join(lines)
    if len(text)>1500: raise ValueError("message length")
    return text
def send(n):
    text=message(n)
    try:
        dgist_send.send_telegram(text); channel="dgist"
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
    elif req["op"]=="check_now":
        if not n.get("check"): raise ValueError("no check")
        n["next_check_at"]=now()
    else: raise ValueError("unknown operation")
    n["version"]+=1; save(n,req["op"])
def tick():
    for p in sorted((NEEDS/"requests").glob("*.json")):
        try:
            process(json.loads(p.read_text(encoding="utf8")))
            p.unlink()
        except Exception as e:
            p.replace(NEEDS/"rejected"/p.name)
            print("need request rejected: "+type(e).__name__,file=sys.stderr)
    for p in sorted(NEEDS.glob("n-*.json")):
        n=json.loads(p.read_text(encoding="utf8"))
        if n["status"]!="open": continue
        c=n.get("check")
        if c and c["id"]=="gh_auth":
            last=n.get("last_check_at")
            due=last is None or time.time()-datetime.fromisoformat(last).timestamp()>=60 or n.pop("next_check_at",None)
            if due:
                ok=gh_auth(); n["last_check_at"]=now()
                if ok:
                    n["status"]="resolved"
                    n["resolution"]={"how":"check","at":now(),"detail":"logged in as mushfique-dgist"}
                n["version"]+=1; save(n,"check:passed" if ok else "check:pending")
        if n["status"]=="open" and not n["telegram"]["last_sent_at"]:
            try: send(n)
            except Exception: print("need send failed: "+n["need_id"],file=sys.stderr)
    atomic_json(ROOT/"state/bridge/heartbeat.json",{"at":now(),"mode":"send_only"})
def main():
    NEEDS.mkdir(parents=True,exist_ok=True)
    for d in ("requests","rejected"): (NEEDS/d).mkdir(exist_ok=True)
    with (NEEDS/"bridge.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        atomic_json(ROOT/"state/bridge/mode.json",{"mode":"send_only"})
        while True:
            tick(); time.sleep(5)
if __name__=="__main__": main()
