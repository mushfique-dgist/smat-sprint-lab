"""CPU-only fallback and deletion retry checks."""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import drop, service
from ops import sprintctl

class Tty(io.StringIO):
    def isatty(self): return True

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/"gh").mkdir()
    (root/"gh/hosts.yml").write_text("test")
    issue={"number":111,"title":"secret-drop n-20260926-build-abcd",
           "user":{"login":"stranger"},"author_association":"NONE"}
    calls=[]
    def fake_gh(args):
        calls.append(args)
        if args[0]=="api": return json.dumps([issue])
        if args[:2]==["issue","delete"] and len([x for x in calls if x[:2]==["issue","delete"]])==1:
            raise RuntimeError("temporary GitHub outage")
        return ""
    with patch.object(drop,"CONFIG",root), patch.object(drop,"SEEN",root/"seen.json"), patch.object(drop,"gh",fake_gh):
        assert drop.consume_issues()==([],[])
        assert json.loads((root/"seen.json").read_text())==[111]
        assert drop.consume_issues()==([],[])
    assert len([x for x in calls if x[:2]==["issue","delete"]])==2

nid="n-20260926-build-5d0b"
n={"need_id":nid,"kind":"phone","title":"Bot setup","what":"Create the bot.",
   "why":"For phone needs.","steps_phone":["Open BotFather."],
   "steps_pc":["ssh sail-gpu","sprintctl secret set telegram-bot-token"],
   "blocking":[]}
assert "PC fallback: ssh sail-gpu; sprintctl secret set telegram-bot-token" in service.message(n)
captured=[]
with patch.object(sys,"argv",["sprintctl","secret","set","telegram-bot-token"]), \
     patch.object(sys,"stdin",Tty("SMAT_sprint_lab_bot\n")), \
     patch("getpass.getpass",lambda prompt:"123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"), \
     patch.object(sprintctl.needs,"list_open",lambda:[dict(n,drop_kind="telegram-bot-token")]), \
     patch.object(drop,"stage_bot",lambda value,digest:captured.append((dict(value),digest))), \
     contextlib.redirect_stdout(io.StringIO()) as output:
    sprintctl.main()
assert captured[0][0]["need_id"]==nid
assert captured[0][0]["username"]=="SMAT_sprint_lab_bot"
assert captured[0][0]["value"].startswith("123456:")
assert "123456:" not in output.getvalue()
print("PASS delete retry, same-message PC fallback and hidden local token input")
