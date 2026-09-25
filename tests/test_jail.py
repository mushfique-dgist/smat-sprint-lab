"""Build-jail secrecy, write boundary, namespace and network canaries."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RECORD = Path("/home/aurnab/smatsprint-home")
CANARY = Path("/home/aurnab/.config/smatsprint-canary/CANARY")
CODEX_CONFIG = Path("/home/aurnab/.codex/config.toml")
before = hashlib.sha256(CODEX_CONFIG.read_bytes()).hexdigest()
CANARY.parent.mkdir(mode=0o700, exist_ok=True)
CANARY.write_text("private canary")
CANARY.chmod(0o600)
probe = r"""
import json,os,socket,subprocess
from pathlib import Path
home=Path('/home/aurnab')
record=Path('/home/aurnab/smatsprint-home')
foreign=('ugrp-forge','gh','dgist-agents','vastai')
def writable(path):
 try:
  fd=os.open(path,os.O_WRONLY)
  os.close(fd)
  return True
 except OSError: return False
spool=record/'state/needs/requests/.canary'
try:
 spool.write_text('canary')
 spool_ok=spool.read_text()=='canary'
 spool.unlink()
except OSError: spool_ok=False
try: dns=bool(socket.getaddrinfo('github.com',443))
except OSError: dns=False
bus=subprocess.run(['/usr/bin/systemctl','--user','is-active','jail-foreign-canary.service'],
                   capture_output=True,timeout=5).returncode
print(json.dumps({
 'foreign_empty':all((home/'.config'/x).is_dir() and not list((home/'.config'/x).iterdir()) for x in foreign),
 'foreign_project_hidden':not (home/'projects/ugrp-cl-autoresearch').exists(),
 'handoff_readable':(home/'projects/smat-sprint-autoresearch-handoff/00_README.md').exists(),
 'canary_hidden':not (home/'.config/smatsprint-canary/CANARY').exists(),
 'gpu_hidden':not Path('/dev/nvidia0').exists(),
 'proc_isolated':len([x for x in os.listdir('/proc') if x.isdigit()])<8,
 'events_read_only':not writable(record/'state/needs/events.jsonl'),
 'codex_config_read_only':not writable(home/'.codex/config.toml'),
 'spool_writable':spool_ok,'user_bus_inaccessible':bus!=0,
 'dns_available':dns,'project_writable':os.access(home/'projects/smat-sprint',os.W_OK)
}))
"""
try:
    result = subprocess.run(["python3",str(PROJECT/"codexwrap/jail.py"),"--",
                             "/usr/bin/python3","-c",probe],cwd=PROJECT,capture_output=True,text=True,timeout=30)
    if result.returncode: raise AssertionError((result.returncode,result.stderr[-500:]))
    findings=json.loads(result.stdout)
    assert all(findings.values()), findings
    assert hashlib.sha256(CODEX_CONFIG.read_bytes()).hexdigest()==before
    print("PASS",json.dumps(findings,sort_keys=True))
finally:
    CANARY.unlink(missing_ok=True)
    CANARY.parent.rmdir()
