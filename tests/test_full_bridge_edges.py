"""More fake Bot API cases for owner, buttons and reply binding."""
import json, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import full

OWNER=8746723177
NOW=int(time.time())
def need(short="abcd"):
    return {"need_id":"n-20260926-build-"+short,"kind":"phone","title":"Question",
            "what":"Question","why":"Reason","steps_phone":[],"blocking":[],
            "reply":"done","check":{"id":"gh_auth","args":{}},"status":"open","version":1,
            "telegram":{"message_ids":[42],"nonce":"1234abcd","last_sent_at":datetime.now(timezone.utc).isoformat(),"sent_count":1},
            "skippable":False}
def callback(action="done",date=NOW,owner=OWNER,nonce="1234abcd",extra=None):
    data={"update_id":1,"callback_query":{"id":"cb1","from":{"id":owner,"is_bot":False},
          "message":{"date":date,"chat":{"id":OWNER,"type":"private"},"message_id":42},
          "data":f"v1|{action}|abcd|{nonce}"}}
    if extra: data["callback_query"].update(extra)
    return data
def message(text,owner=OWNER,extra=None):
    m={"update_id":2,"message":{"message_id":70,"date":NOW,"text":text,
       "from":{"id":owner,"is_bot":False},"chat":{"id":OWNER,"type":"private"}}}
    if extra: m["message"].update(extra)
    return m
sent=[]; saved=[]
def api(token,method,body=None):
    assert token=="fake"
    sent.append((method,body))
    return {"message_id":100} if method=="sendMessage" else True
def save(n,cause): saved.append((n["status"],cause))
with patch.object(full,"credentials",lambda:("fake",OWNER)), \
     patch.object(full,"bot_api",api):
    n=need()
    checks=iter([False,True])
    with patch.object(full,"_matching",lambda short:n), patch("bridge.service.gh_auth",lambda:next(checks)):
        full.handle_update(callback(date=NOW-3*86400),save)
        assert n["status"]=="open" and "not passed" in sent[-1][1]["text"]
        full.handle_update(callback(),save)
        assert n["status"]=="resolved" and saved[-1][0]=="resolved"
    n=need(); sent.clear()
    with patch.object(full,"_matching",lambda short:n), patch("bridge.service.gh_auth",lambda:True):
        full.handle_update(callback(action="later"),save)
        assert n["status"]=="open" and n["snoozed_until"]
        full.handle_update(callback(),save)
        assert n["status"]=="resolved"
    n=need(); sent.clear()
    with patch.object(full,"_matching",lambda short:n):
        full.handle_update(callback(action="skip"),save)
        assert n["status"]=="open"
        n["skippable"]=True
        full.handle_update(callback(action="skip"),save)
        assert n["status"]=="skipped"
    n=need(); sent.clear()
    with patch.object(full,"_matching",lambda short:n):
        full.handle_update(callback(extra={"inline_message_id":"inline"}),save)
        full.handle_update(callback(date=0),save)
        assert n["status"]=="open" and all(x[0]=="answerCallbackQuery" for x in sent)
    sent.clear()
    full.handle_update(message("yes",extra={"forward_origin":{"type":"user"}}),save)
    assert sent[-1][0]=="sendMessage" and "ignore forwarded" in sent[-1][1]["text"]
    n=need(); n["reply"]="yes_no"; n["check"]=None; n["consequential"]=True
    sent.clear()
    with patch.object(full,"list_open",lambda:[n]):
        full.handle_update(message("yes"),save)
        assert n["status"]=="open"
        full.handle_update(message("abcd yes"),save)
        assert n["status"]=="resolved" and n["resolution"]["detail"]=="Yes"
    with tempfile.TemporaryDirectory() as tmp:
        one=need("aaaa"); one["status"]="resolved"; one["telegram"]["message_ids"]=[60]
        two=need("bbbb"); two["reply"]="yes_no"; two["check"]=None
        two["telegram"]["message_ids"]=[55]
        Path(tmp,"one.json").write_text(json.dumps(one));Path(tmp,"two.json").write_text(json.dumps(two))
        sent.clear()
        with patch.object(full,"NEEDS",Path(tmp)), patch.object(full,"list_open",lambda:[two]):
            full.handle_update(message("yes"),save)
        assert two["status"]=="open" and "Please reply" in sent[-1][1]["text"]
    three=[need("a001"),need("a002"),need("a003")]
    for i,n in enumerate(three): n["telegram"]["message_ids"]=[90+i]
    sent.clear()
    with patch.object(full,"list_open",lambda:three):
        full.handle_update(message("/needs"),save)
    replies=[x[1]["reply_parameters"]["message_id"] for x in sent if x[0]=="sendMessage"]
    assert replies==[90,91,92],replies
print("PASS failing/passing Done, old callback, Later, Skip, inline/inaccessible, forward, consequential and /needs")
