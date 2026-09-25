"""Fake Bot API checks before the programme bot is allowed to poll."""
import json, sys, tempfile, time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import full

owner=8746723177
sent=[]
saved=[]
need={"need_id":"n-20260926-build-abcd","kind":"phone","title":"Check",
      "what":"Check", "why":"Check", "steps_phone":[],"blocking":[],
      "reply":"done","check":{"id":"gh_auth","args":{}},"status":"open","version":1,
      "telegram":{"message_ids":[42],"nonce":"1234abcd","last_sent_at":"now","sent_count":1},
      "skippable":False}
def api(token,method,body=None):
    assert token=="fake-token"
    sent.append((method,body))
    if method=="sendMessage": return {"message_id":99}
    if method=="getUpdates": return list(updates)
    return True
def save(n,cause): saved.append((n["status"],cause))
def callback(from_id=owner,nonce="1234abcd"):
    return {"update_id":1,"callback_query":{"id":"cb1","from":{"id":from_id,"is_bot":False},
            "message":{"date":int(time.time()),"chat":{"id":owner,"type":"private"},"message_id":42},
            "data":"v1|done|abcd|"+nonce}}
with patch.object(full,"credentials",lambda:("fake-token",owner)), \
     patch.object(full,"bot_api",api), patch.object(full,"_matching",lambda short:need), \
     patch("bridge.service.gh_auth",lambda:True):
    full.handle_update(callback(from_id=owner+1),save)
    assert sent[-1][0]=="answerCallbackQuery" and sent[-1][1]["text"]==""
    assert need["status"]=="open"
    full.handle_update(callback(nonce="deadbeef"),save)
    assert "older" in sent[-1][1]["text"] and need["status"]=="open"
    full.handle_update(callback(),save)
    assert need["status"]=="resolved" and saved[-1]==("resolved","button:done")
    sent.clear()
    full.handle_update({"update_id":2,"message":{"text":"/status","message_id":6,
        "date":int(time.time()),"from":{"id":owner+1,"is_bot":False},
        "chat":{"id":owner,"type":"private"}}},save)
    assert not sent
    sent.clear()
    full.handle_update({"update_id":3,"message":{"text":"123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
        "message_id":7,"date":int(time.time()),"from":{"id":owner,"is_bot":False},
        "chat":{"id":owner,"type":"private"}}},save)
    assert sent and sent[0][0]=="deleteMessage"
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        updates=[{"update_id":10,"message":{"text":"/start","message_id":8,
                 "date":int(time.time()),"from":{"id":owner,"is_bot":False},
                 "chat":{"id":owner,"type":"private"}}}]
        sent.clear()
        with patch.object(full,"POLL_LOCK",root/"poll.lock"), \
             patch.object(full,"OFFSET",root/"offset.json"), \
             patch.object(full,"SEEN",root/"seen.jsonl"):
            full.poll_once(save,first=True)
            count=len([x for x in sent if x[0]=="sendMessage"])
            full.poll_once(save,first=True)
            assert len([x for x in sent if x[0]=="sendMessage"])==count and json.loads((root/"offset.json").read_text())["offset"]==11
print("PASS owner-only callbacks, stale nonce, secret deletion, duplicate update skip")
