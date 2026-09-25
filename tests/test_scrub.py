"""Secret screening and redaction examples, without sending messages."""
import base64, sys, urllib.parse
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ops.fallback import dgist_send

token="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
variants=[token,token[:12]+"\n"+token[12:],urllib.parse.quote(token,safe=""),
          base64.urlsafe_b64encode(token.encode()).decode().rstrip("="),
          "See [the link](https://example.com/?token="+token+")",
          "github_pat_sample", "GOCSPX-"+"A"*24, "ya29."+"A"*30]
with patch.object(dgist_send,"owner_credentials",lambda:("654321:"+"Z"*35,8746723177)), \
     patch.object(dgist_send,"email_settings",lambda:({"GMAIL_APP_PASSWORD":"abcdefghijklmnop"},465)):
    for candidate in variants:
        try: dgist_send.scrub_outbound(candidate)
        except ValueError: pass
        else: raise AssertionError("unsafe body accepted")
    try: dgist_send.scrub_outbound("password abcdefghijklmnop")
    except ValueError: pass
    else: raise AssertionError("known secret accepted")
safe="Read https://github.com/mushfique-dgist/smat-sprint-lab and https://doi.org/10.1234/example"
assert dgist_send.scrub_outbound(safe)==safe
redacted=dgist_send.scrub_outbound("See https://bad.example/x and /home/aurnab/.config/test/key")
assert "[link removed: bad.example]" in redacted
assert "[path in secrets directory]" in redacted
print("PASS outbound split, encoded, known and prefix secrets withheld; safe links and redactions")
