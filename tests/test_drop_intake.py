"""No-network tests of encrypted issue and owner validation."""
import base64, json, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from nacl.public import PublicKey, SealedBox
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge import drop

PUBLIC = json.loads(Path("dashboard/drop-key.json").read_text())
NEED_ID = "n-20260926-build-5d0b"
TOKEN = "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
USERNAME = "SMAT_sprint_lab_bot"
payload = {"need_id":NEED_ID,"kind":"telegram-bot-token","value":TOKEN,
           "username":USERNAME,"created_at":datetime.now(timezone.utc).isoformat(),
           "key_id":PUBLIC["key_id"]}
cipher = SealedBox(PublicKey(base64.b64decode(PUBLIC["public_key"]))).encrypt(json.dumps(payload).encode())
encoded = base64.urlsafe_b64encode(cipher).decode().rstrip("=")
body = "BEGIN SMATSPRINT DROP v1\n"+encoded+"\nEND"
issue = {"number":101,"title":"secret-drop "+NEED_ID,"body":body,
         "user":{"login":"mushfique-dgist"},"author_association":"OWNER"}
foreign = dict(issue,number=102,user={"login":"someone-else"})
calls = []
def fake_gh(args):
    calls.append(args)
    if args[0]=="api": return json.dumps([issue,foreign])
    if args[:2]==["issue","delete"]: return ""
    raise AssertionError(args)
def fake_bot_api(token, method, body=None):
    assert token == TOKEN
    if method == "getMe": return {"username":USERNAME}
    if method == "getUpdates":
        assert body["timeout"] == 0
        return [{"message":{"text":"/start","from":{"id":8746723177,"is_bot":False},
                            "chat":{"id":8746723177,"type":"private"},"date":int(time.time())}}]
    raise AssertionError(method)

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    (root/"gh").mkdir()
    (root/"gh/hosts.yml").write_text("test")
    (root/"drop_x25519").write_bytes(Path("/home/aurnab/.config/smatsprint/drop_x25519").read_bytes())
    with patch.object(drop,"STAGED",root/"staged_bot.json"), \
         patch.object(drop,"OWNER_VERIFIED",root/"owner_verified.json"), \
         patch.object(drop,"SEEN",root/"seen.json"), \
         patch.object(drop,"CONFIG",root), \
         patch.object(drop,"gh",fake_gh), \
         patch.object(drop,"bot_api",fake_bot_api), \
         patch.object(drop,"owner_credentials",lambda: ("unused",8746723177)):
        accepted = drop.consume_issues()
        assert accepted == [NEED_ID], accepted
        assert (root/"staged_bot.json").stat().st_mode & 0o777 == 0o600
        assert json.loads((root/"seen.json").read_text()) == [101]
        assert len([c for c in calls if c[:2]==["issue","delete"]]) == 1
        assert drop.consume_issues() == []
        ok,name = drop.check_owner()
        assert ok and name == USERNAME
        assert (root/"telegram.env").stat().st_mode & 0o777 == 0o600
        assert TOKEN not in json.dumps(calls)
print("PASS owner-only issue intake, replay skip, delete, owner /start and mode 0600")
