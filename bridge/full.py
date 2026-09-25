"""Owner-checked Telegram receive path for the programme bot only."""
import html
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from smatsprint.needs import NEEDS, ROOT, atomic_json, list_open
from ops.fallback.dgist_send import scrub_outbound
from bridge.drop import bot_api

MODE = ROOT/"state/bridge/mode.json"
OFFSET = ROOT/"state/bridge/offset.json"
SEEN = ROOT/"state/bridge/seen.jsonl"
POLL_LOCK = ROOT/"state/bridge/poll.lock"
TOKEN_ENV = Path("/home/aurnab/.config/smatsprint/telegram.env")
BUTTON = re.compile(r"v1\|([a-z0-9:]+)\|([0-9a-f]{4})\|([0-9a-f]{8})\Z")

def credentials():
    values={}
    for line in TOKEN_ENV.read_text(encoding="utf8").splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="): values["token"]=line.split("=",1)[1]
        if line.startswith("TELEGRAM_OWNER_CHAT_ID="): values["owner"]=int(line.split("=",1)[1])
    if set(values)!={"token","owner"} or values["owner"]<=0: raise ValueError("bot credentials invalid")
    return values["token"],values["owner"]

def buttons(need,nonce):
    rows=[]
    short=need["need_id"][-4:]
    def button(label,action): return {"text":label,"callback_data":f"v1|{action}|{short}|{nonce}"}
    if need.get("check") and need["check"]["id"]!="none": rows.append([button("Done","done"),button("Later","later")])
    elif need["reply"]=="pick_one":
        for i,label in enumerate(need.get("options",[]),1): rows.append([button(label,f"opt:{i}")])
        rows.append([button("Later","later")])
    elif need["reply"]=="yes_no": rows.append([button("Yes","opt:1"),button("No","opt:2")])
    elif need["reply"] in ("code","text"): rows.append([button("Later","later")])
    if need.get("skippable"): rows.append([button("Skip","skip")])
    return {"inline_keyboard":rows} if rows else None

def send_need(need,plain):
    token,owner=credentials()
    clean=scrub_outbound(plain)
    nonce=secrets.token_hex(4)
    markup=buttons(need,nonce)
    body={"chat_id":owner,"text":html.escape(clean),"parse_mode":"HTML",
          "link_preview_options":{"is_disabled":True}}
    if markup: body["reply_markup"]=markup
    result=bot_api(token,"sendMessage",body)
    return result["message_id"],nonce

def send_plain(plain):
    token,owner=credentials()
    clean=scrub_outbound(plain)
    return bot_api(token,"sendMessage",{"chat_id":owner,"text":html.escape(clean),
                                        "parse_mode":"HTML","link_preview_options":{"is_disabled":True}})

def _matching(short):
    matches=[]
    for path in NEEDS.glob("n-*.json"):
        n=json.loads(path.read_text(encoding="utf8"))
        if n["need_id"].endswith("-"+short): matches.append(n)
    return matches[0] if len(matches)==1 else None

def _valid_message(message,owner):
    sender=message.get("from",{})
    chat=message.get("chat",{})
    return (chat.get("type")=="private" and chat.get("id")==owner and
            sender.get("id")==owner and sender.get("is_bot") is False and
            "forward_origin" not in message and "via_bot" not in message and
            message.get("date",0)>=time.time()-86400)

def _answer(token,callback_id,text=""):
    bot_api(token,"answerCallbackQuery",{"callback_query_id":callback_id,"text":text[:180]})

def _transition(n,action,save):
    if n["status"]!="open": return "Already closed."
    if action=="later":
        from datetime import timedelta
        n["snoozed_until"]=(datetime.now(timezone.utc)+timedelta(hours=3)).isoformat()
        n["version"]+=1; save(n,"button:later")
        return "I will remind you in three hours."
    if action=="skip" and n.get("skippable"):
        n["status"]="skipped"
        n["resolution"]={"how":"skip","at":datetime.now(timezone.utc).isoformat(),"detail":""}
    elif action.startswith("opt:"):
        try: idx=int(action.split(":")[1])
        except ValueError: return "Invalid choice."
        labels=n.get("options",["Yes","No"] if n["reply"]=="yes_no" else [])
        if not 1<=idx<=len(labels): return "Invalid choice."
        n["status"]="resolved"
        n["resolution"]={"how":"button","at":datetime.now(timezone.utc).isoformat(),"detail":labels[idx-1]}
    elif action=="done" and n.get("check"):
        if n["check"]["id"]=="gh_auth":
            from bridge.service import gh_auth
            ok=gh_auth()
        elif n["check"]["id"]=="bot_owner_verified":
            from bridge.drop import check_owner
            ok,_=check_owner()
        else: ok=False
        if not ok: return "The check has not passed yet."
        n["status"]="resolved"
        n["resolution"]={"how":"check","at":datetime.now(timezone.utc).isoformat(),"detail":"verified"}
    else: return "That action is not available."
    n["version"]+=1; save(n,"button:"+action)
    return "Recorded for need "+n["need_id"][-4:]+"."

def handle_update(update,save):
    token,owner=credentials()
    if "callback_query" in update:
        cb=update["callback_query"]
        cb_id=cb.get("id")
        if not cb_id: return
        sender=cb.get("from",{})
        msg=cb.get("message",{})
        data=cb.get("data","")
        match=BUTTON.fullmatch(data)
        answer=""
        if (sender.get("id")==owner and sender.get("is_bot") is False and
            isinstance(msg,dict) and msg.get("date",0)>0 and
            msg.get("chat",{}).get("id")==owner and match):
            action,short,nonce=match.groups()
            need=_matching(short)
            if need and msg.get("message_id") in need.get("telegram",{}).get("message_ids",[]):
                if nonce!=need["telegram"].get("nonce"): answer="This button is from an older message; use the latest one."
                else: answer=_transition(need,action,save)
        _answer(token,cb_id,answer)
        return
    message=update.get("message")
    if not isinstance(message,dict) or not _valid_message(message,owner): return
    text=message.get("text","")
    if len(text)>1500:
        send_plain("That message is too long for a need reply."); return
    try: scrub_outbound(text)
    except ValueError:
        bot_api(token,"deleteMessage",{"chat_id":owner,"message_id":message["message_id"]})
        send_plain("I deleted a message that looked like a secret. Deleting it does not un-send it, so please rotate it and use the encrypted drop.")
        return
    if text=="/start": send_plain("Connected to SMAT-Sprint. Use /needs to see open requests."); return
    if text=="/help": send_plain("Use /needs for open requests and /status for a short build status. Do not send tokens here."); return
    if text=="/needs":
        for n in list_open(): send_plain("Open need "+n["need_id"][-4:]+": "+n["title"])
        return
    if text=="/status":
        state=ROOT/"state/codexwrap/state.json"
        label=json.loads(state.read_text()).get("state","BOOTSTRAP") if state.exists() else "BOOTSTRAP"
        send_plain("SMAT-Sprint build: "+label+". Open needs: "+str(len(list_open()))+".")
        return
    if text.startswith("/build"):
        send_plain("Build controls are being installed. The build is held while the phone bridge is incomplete.")
        return
    # Text-like replies require an unambiguous binding; no free text becomes a command.
    candidates=[n for n in list_open() if n["reply"] in ("yes_no","pick_one","code","text")]
    prefix=re.match(r"^([0-9a-f]{4})\s+(.+)$",text,re.S)
    if prefix: candidates=[n for n in candidates if n["need_id"].endswith("-"+prefix.group(1))]
    elif message.get("reply_to_message"):
        mid=message["reply_to_message"].get("message_id")
        candidates=[n for n in candidates if mid in n.get("telegram",{}).get("message_ids",[])]
    elif len(candidates)!=1: candidates=[]
    if len(candidates)!=1:
        send_plain("Please reply to the latest need message or start with its four-character id.")
        return
    n=candidates[0]
    if n.get("consequential") and not prefix:
        send_plain("For this decision, start your reply with "+n["need_id"][-4:]+".")
        return
    value=(prefix.group(2) if prefix else text).strip()
    if n["reply"]=="yes_no":
        labels=["Yes","No"]
        chosen="Yes" if value.lower() in ("yes","y") else "No" if value.lower() in ("no","n") else None
    elif n["reply"]=="pick_one":
        labels=n.get("options",[])
        chosen=labels[int(value)-1] if value.isdigit() and 1<=int(value)<=len(labels) else next((x for x in labels if x.casefold()==value.casefold()),None)
    elif n["reply"]=="text" and len(value)<=500: chosen=value
    else: chosen=None
    if chosen is None:
        send_plain("I could not match that answer to need "+n["need_id"][-4:]+".")
        return
    n["status"]="resolved"; n["version"]+=1
    n["resolution"]={"how":"reply","at":datetime.now(timezone.utc).isoformat(),"detail":chosen}
    save(n,"reply")
    send_plain("Recorded "+chosen+" for need "+n["need_id"][-4:]+".")

def poll_once(save,first=False):
    import fcntl
    token,_=credentials()
    POLL_LOCK.parent.mkdir(parents=True,exist_ok=True)
    with POLL_LOCK.open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        offset=json.loads(OFFSET.read_text()).get("offset") if OFFSET.exists() and not first else None
        body={"timeout":0 if first else 45,"allowed_updates":["message","callback_query"]}
        if offset is not None: body["offset"]=offset
        updates=bot_api(token,"getUpdates",body)
        if first and not updates and OFFSET.exists(): OFFSET.unlink()
        seen=set()
        if SEEN.exists():
            for line in SEEN.read_text().splitlines()[-10000:]:
                try:
                    item=json.loads(line)
                    if item.get("phase")=="done": seen.add(item["update_id"])
                except Exception: pass
        for update in updates:
            uid=update["update_id"]
            if uid not in seen:
                with SEEN.open("a",encoding="utf8") as out:
                    out.write(json.dumps({"update_id":uid,"phase":"processing","at":datetime.now(timezone.utc).isoformat()})+"\n")
                    out.flush(); os.fsync(out.fileno())
                handle_update(update,save)
                with SEEN.open("a",encoding="utf8") as out:
                    out.write(json.dumps({"update_id":uid,"phase":"done","at":datetime.now(timezone.utc).isoformat()})+"\n")
                    out.flush(); os.fsync(out.fileno())
                seen.add(uid)
            offset=max(offset or 0,uid+1)
            atomic_json(OFFSET,{"offset":offset})
        return len(updates)
