"""Nonblocking need requests; the bridge is the sole state writer."""
import json, os, re, secrets, time
from datetime import datetime
from pathlib import Path

ROOT = Path(os.getenv("SMATSPRINT_HOME", "/home/aurnab/smatsprint-home"))
NEEDS = ROOT / "state/needs"
ALLOWED_REPLIES = {"none", "done", "yes_no", "pick_one", "code", "text"}
ID = re.compile(r"n-[0-9]{8}-[a-z0-9-]{1,30}-[0-9a-f]{4}$")

def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + secrets.token_hex(6) + ".tmp")
    with tmp.open("x", encoding="utf8") as out:
        json.dump(obj, out, sort_keys=True, ensure_ascii=False)
        out.write("\n")
        out.flush(); os.fsync(out.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def validate(s):
    for key, limit in (("title",80),("what",300),("why",300)):
        if not isinstance(s.get(key),str) or not 1 <= len(s[key]) <= limit: raise ValueError(key)
    if s.get("kind") not in ("phone","pc") or s.get("reply") not in ALLOWED_REPLIES: raise ValueError("kind/reply")
    if not isinstance(s.get("steps_phone"),list) or len(s["steps_phone"])>8 or any(not isinstance(x,str) or len(x)>300 for x in s["steps_phone"]): raise ValueError("steps")
    if not isinstance(s.get("blocking"),list): raise ValueError("blocking")
    check=s.get("check")
    if check is not None and (not isinstance(check,dict) or check.get("id") not in ("none","gh_auth") or check.get("args",{})!={}): raise ValueError("check")
    if s.get("reissue") is not None: raise ValueError("reissue not installed")
    if s.get("code") not in ("build",): raise ValueError("code")

def create(spec):
    validate(spec)
    for _ in range(20):
        nid="n-"+datetime.now().strftime("%Y%m%d")+"-"+spec["code"]+"-"+secrets.token_hex(2)
        if not (NEEDS/(nid+".json")).exists(): break
    else: raise RuntimeError("id collision")
    atomic_json(NEEDS/"requests"/(str(time.time_ns())+"-"+secrets.token_hex(4)+".json"),
                {"op":"create","need_id":nid,"expected_version":None,"spec":spec})
    return nid

def status(nid):
    if not ID.fullmatch(nid): raise ValueError("id")
    p=NEEDS/(nid+".json")
    return json.loads(p.read_text(encoding="utf8")) if p.exists() else None

def list_open():
    result=[]
    for p in NEEDS.glob("n-*.json"):
        n=json.loads(p.read_text(encoding="utf8"))
        if n["status"]=="open": result.append(n)
    return sorted(result,key=lambda n:n["created_at"])

def request_transition(nid,op,reason=""):
    if op not in ("cancel","check_now"): raise ValueError("op")
    n=status(nid)
    if n is None: raise ValueError("unknown")
    atomic_json(NEEDS/"requests"/(str(time.time_ns())+"-"+secrets.token_hex(4)+".json"),
                {"op":op,"need_id":nid,"expected_version":n["version"],"reason":reason[:200]})
    return nid
