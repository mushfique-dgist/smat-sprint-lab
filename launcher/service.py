"""Fixed-operation launcher outside the build jail; never accepts command text."""
import fcntl
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from smatsprint.needs import ROOT, atomic_json

PROJECT=Path("/home/aurnab/projects/smat-sprint")
CONFIG=Path("/home/aurnab/.config/smatsprint")
REQUESTS=ROOT/"state/launcher/requests"
RESULTS=ROOT/"state/launcher/results"
EVENTS=ROOT/"state/launcher/events.jsonl"
OPS={"push_main","push_pages","create_deploy_key","repo_access","pages_live","restart_bridge"}
ID=re.compile(r"[0-9a-f]{16}\Z")
GH="/home/aurnab/.local/share/smatsprint/bin/gh"
REPO="mushfique-dgist/smat-sprint-lab"
REMOTE="git@github.com:mushfique-dgist/smat-sprint-lab.git"

def now(): return datetime.now(timezone.utc).isoformat()
def run(cmd,cwd=None,env=None,timeout=60):
    result=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
    if result.returncode: raise RuntimeError("registered operation failed")
    return result.stdout.strip()
def gh_env():
    return {"PATH":"/usr/local/bin:/usr/bin:/bin","HOME":"/home/aurnab",
            "GH_CONFIG_DIR":str(CONFIG/"gh"),"GH_PROMPT_DISABLED":"1"}
def execute(op):
    if op not in OPS: raise ValueError("unregistered operation")
    if op in ("push_main","push_pages"):
        tree=PROJECT if op=="push_main" else PROJECT/"cache/pages-worktree"
        branch="main" if op=="push_main" else "gh-pages"
        if run(["git","remote","get-url","origin"],tree)!=REMOTE:
            raise RuntimeError("wrong remote")
        if run(["git","branch","--show-current"],tree)!=branch:
            raise RuntimeError("wrong branch")
        run(["git","push","origin",branch],tree,timeout=90)
        return {"branch":branch,"head":run(["git","rev-parse","--short=12","HEAD"],tree)}
    if op=="create_deploy_key":
        key=CONFIG/"deploy_key"
        pub=CONFIG/"deploy_key.pub"
        if not key.exists():
            run(["ssh-keygen","-q","-t","ed25519","-N","","-C","smat-sprint-deploy","-f",str(key)],timeout=30)
            key.chmod(0o600)
        if not pub.exists() or key.stat().st_mode & 0o777 != 0o600: raise RuntimeError("deploy key invalid")
        return {"fingerprint":run(["ssh-keygen","-lf",str(pub)]).split()[1]}
    if op=="repo_access":
        data=json.loads(run([GH,"api",f"repos/{REPO}"],env=gh_env(),timeout=30))
        if data.get("full_name")!=REPO or data.get("private") is not True: raise RuntimeError("repository access failed")
        return {"repository":REPO,"private":True}
    if op=="pages_live":
        url="https://mushfique-dgist.github.io/smat-sprint-lab/"
        with urllib.request.urlopen(url,timeout=25) as response:
            body=response.read(100000)
            if response.status!=200 or b"SMAT-Sprint dashboard" not in body: raise RuntimeError("Pages not live")
        return {"url":url}
    if op=="restart_bridge":
        run(["systemctl","--user","restart","smatsprint-bridge.service"],timeout=30)
        return {"unit":"smatsprint-bridge.service"}
    raise AssertionError(op)

def process(path):
    request=json.loads(path.read_text(encoding="utf8"))
    rid=request.get("id")
    if not isinstance(rid,str) or not ID.fullmatch(rid): raise ValueError("invalid request id")
    result_path=RESULTS/(rid+".json")
    if result_path.exists():
        path.unlink()
        return
    op=request.get("op")
    if op not in OPS or set(request)!={"schema_version","id","op","created_at"} or request["schema_version"]!=1:
        outcome={"id":rid,"op":op if isinstance(op,str) and len(op)<60 else "invalid","ok":False,"error":"unregistered request","at":now()}
    else:
        try:
            data=execute(op)
            outcome={"id":rid,"op":op,"ok":True,"result":data,"at":now()}
        except Exception as exc:
            outcome={"id":rid,"op":op,"ok":False,"error":type(exc).__name__,"at":now()}
    atomic_json(result_path,outcome)
    with EVENTS.open("a",encoding="utf8") as out:
        out.write(json.dumps({k:outcome[k] for k in ("id","op","ok","at")})+"\n")
        out.flush(); os.fsync(out.fileno())
    path.unlink()

def main():
    REQUESTS.mkdir(parents=True,exist_ok=True)
    RESULTS.mkdir(parents=True,exist_ok=True)
    (ROOT/"state/launcher/rejected").mkdir(parents=True,exist_ok=True)
    with (ROOT/"state/launcher/lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            for path in sorted(REQUESTS.glob("*.json")):
                try: process(path)
                except Exception as exc:
                    print("invalid launcher request: "+type(exc).__name__,file=sys.stderr)
                    path.replace(ROOT/"state/launcher/rejected"/path.name)
            atomic_json(ROOT/"state/launcher/heartbeat.json",{"at":now()})
            time.sleep(2)
if __name__=="__main__": main()
