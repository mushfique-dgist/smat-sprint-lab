"""Read private GitHub encrypted-drop issues and verify the new bot."""
import base64
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from nacl.public import PrivateKey, SealedBox
from smatsprint.needs import ROOT, status, atomic_json
from ops.fallback.dgist_send import owner_credentials

GH = "/home/aurnab/.local/share/smatsprint/bin/gh"
REPO = "mushfique-dgist/smat-sprint-lab"
CONFIG = Path("/home/aurnab/.config/smatsprint")
STAGED = ROOT / "state/drop/staged_bot.json"
OWNER_VERIFIED = ROOT / "state/drop/owner_verified.json"
SEEN = ROOT / "state/drop/seen.json"
BOT_RE = re.compile(r"\d{6,12}:[A-Za-z0-9_-]{30,50}\Z")
NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{4,31}_bot\Z", re.I)
MARKERS = re.compile(r"BEGIN SMATSPRINT DROP v1\s+([A-Za-z0-9_-]{20,10000})\s+END")

def gh(args):
    env={"PATH":"/usr/local/bin:/usr/bin:/bin","HOME":"/home/aurnab",
         "GH_CONFIG_DIR":str(CONFIG/"gh"),"GH_PROMPT_DISABLED":"1"}
    r=subprocess.run([GH,*args],env=env,capture_output=True,text=True,timeout=25)
    if r.returncode: raise RuntimeError("GitHub issue operation failed")
    return r.stdout

def bot_api(token, method, body=None):
    request=urllib.request.Request("https://api.telegram.org/bot"+token+"/"+method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type":"application/json"},method="POST" if body is not None else "GET")
    with urllib.request.urlopen(request,timeout=20) as response:
        answer=json.load(response)
    if answer.get("ok") is not True: raise ValueError("bot API rejected request")
    return answer["result"]

def open_envelope(body):
    match=MARKERS.search(body or "")
    if not match: raise ValueError("missing envelope")
    raw=match.group(1)
    box=base64.urlsafe_b64decode(raw+"="*((-len(raw))%4))
    if len(box)<48 or len(box)>5000: raise ValueError("size")
    pub=json.loads((Path(__file__).resolve().parents[1] / "dashboard/drop-key.json").read_text())
    value=json.loads(SealedBox(PrivateKey((CONFIG/"drop_x25519").read_bytes())).decrypt(box))
    if value.get("key_id")!=pub["key_id"]: raise ValueError("key id")
    created=datetime.fromisoformat(value["created_at"])
    if created.tzinfo is None or not -300 <= (datetime.now(timezone.utc)-created).total_seconds() <= 86400:
        raise ValueError("age")
    return value,hashlib.sha256(box).hexdigest()

def stage_bot(value, digest):
    nid=value.get("need_id")
    need=status(nid)
    if not need or need["status"]!="open" or need.get("drop_kind")!="telegram-bot-token" or value.get("kind")!="telegram-bot-token":
        raise ValueError("no matching need")
    token=value.get("value","")
    username=value.get("username","").removeprefix("@")
    if not BOT_RE.fullmatch(token) or not NAME_RE.fullmatch(username): raise ValueError("format")
    if username.lower() in ("dgist_bot","ugrpforge_bot"): raise ValueError("foreign bot")
    actual=bot_api(token,"getMe")
    if actual.get("username","").lower()!=username.lower(): raise ValueError("bot username mismatch")
    if STAGED.exists(): raise ValueError("bot already staged")
    atomic_json(STAGED,{"token":token,"username":actual["username"],"need_id":nid,"digest":digest,"at":datetime.now(timezone.utc).isoformat()})
    STAGED.chmod(0o600)
    return nid

def consume_issues():
    if not (CONFIG/"gh/hosts.yml").exists(): return [],[]
    issues=json.loads(gh(["api",f"repos/{REPO}/issues?state=open&per_page=100"]))
    seen=set(json.loads(SEEN.read_text()) if SEEN.exists() else [])
    accepted=[]; rejected=[]
    for issue in issues:
        if "pull_request" in issue: continue
        title=issue.get("title","")
        if not re.fullmatch(r"secret-drop n-[0-9]{8}-[a-z0-9-]{1,30}-[0-9a-f]{4}",title): continue
        number=issue["number"]
        if number in seen:
            # Seen means processed, not necessarily deleted. Retry deletion after
            # an outage so an encrypted issue cannot stay open indefinitely.
            try: gh(["issue","delete",str(number),"--yes","--repo",REPO])
            except Exception: pass
            continue
        owner=(issue.get("user",{}).get("login")=="mushfique-dgist" and
               issue.get("author_association")=="OWNER")
        if not owner:
            seen.add(number); atomic_json(SEEN,sorted(seen))
            try: gh(["issue","delete",str(number),"--yes","--repo",REPO])
            except Exception: pass
            continue
        try:
            value,digest=open_envelope(issue.get("body",""))
            if title != "secret-drop "+value.get("need_id",""): raise ValueError("title mismatch")
            accepted.append(stage_bot(value,digest))
        except Exception:
            # Never print exception text: provider output could include a token.
            rejected.append(title.rsplit(" ",1)[-1])
        seen.add(number)
        atomic_json(SEEN,sorted(seen))
        try: gh(["issue","delete",str(number),"--yes","--repo",REPO])
        except Exception: pass
    return accepted,rejected

def check_owner():
    if OWNER_VERIFIED.exists() and (CONFIG/"telegram.env").exists():
        return True,json.loads(OWNER_VERIFIED.read_text())["username"]
    if not STAGED.exists(): return False,None
    bot=json.loads(STAGED.read_text())
    _,owner=owner_credentials()
    updates=bot_api(bot["token"],"getUpdates",{"timeout":0,"allowed_updates":["message"]})
    for update in updates:
        message=update.get("message",{})
        sender=message.get("from",{})
        chat=message.get("chat",{})
        if (message.get("text","").startswith("/start") and sender.get("id")==owner and
            not sender.get("is_bot") and chat.get("type")=="private" and chat.get("id")==owner and
            message.get("date",0)>=time.time()-86400):
            config=CONFIG/"telegram.env"
            tmp=config.with_name("telegram.env.tmp")
            tmp.write_text("TELEGRAM_BOT_TOKEN="+bot["token"]+"\nTELEGRAM_OWNER_CHAT_ID="+str(owner)+"\n")
            tmp.chmod(0o600)
            os.replace(tmp,config)
            atomic_json(OWNER_VERIFIED,{"username":bot["username"],"at":datetime.now(timezone.utc).isoformat()})
            STAGED.unlink()
            return True,bot["username"]
    return False,None
