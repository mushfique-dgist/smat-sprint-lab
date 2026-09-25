"""Failure, recovery, fallback and detached-job wrapper cases."""
import json, sys, tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codexwrap import wrapper as w

def endfile(directory,seconds=60):
    directory.mkdir(parents=True,exist_ok=True)
    start=w.now()-timedelta(seconds=seconds)
    (directory/"started_at").write_text(start.isoformat())
    (directory/"ended_at").write_text(w.stamp())
    (directory/"exit_code").write_text("0")
    (directory/"end.json").write_text(json.dumps({"reason":"c","milestone_complete":True,
                                                  "waiting_for_needs":[],"waiting_for_jobs":[]}))
    (directory/"inputs.json").write_text(json.dumps({"progress_before":{"head":"same","progress_sections_sha256":"same"}}))
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp); base=root/"codexwrap"
    for d in ("sessions","requests","results","rejected"): (base/d).mkdir(parents=True)
    aliases={"BASE":base,"SESSIONS":base/"sessions","STATE":base/"state.json",
             "REQUESTS":base/"requests","RESULTS":base/"results","EVENTS":base/"transitions.jsonl",
             "ROOT":root}
    with patch.multiple(w,**aliases), patch.object(w,"progress_signature",lambda:{"head":"same","progress_sections_sha256":"same"}):
        s=w.get_state(); s["state"]="RUNNING"; s["current_session"]=1
        endfile(w.SESSIONS/"1",seconds=60)
        with patch.object(w,"active_unit",lambda number:(False,{})):
            s=w.finish(s)
        assert s["state"]=="BACKOFF" and s["failures"]==1
        endfile(w.SESSIONS/"2",seconds=60)
        s["state"]="RUNNING"; s["current_session"]=2
        raised=[]
        with patch.object(w,"active_unit",lambda number:(False,{})), patch.object(w,"create",lambda spec:raised.append(spec)):
            s=w.finish(s)
        assert s["failures"]==2 and len(raised)==1
        assert (w.parse(s["backoff_until"])-w.now()).total_seconds()<=1201
        s["state"]="LAUNCHING"; s["current_session"]=3
        (w.SESSIONS/"3").mkdir()
        w.save(s,"test-crash")
        checks=[(False,{"LoadState":"not-found"}),(True,{"LoadState":"loaded"})]
        starts=[]
        with patch.object(w,"active_unit",lambda number:checks.pop(0) if checks else (True,{"LoadState":"loaded"})), \
             patch.object(w,"start_unit",lambda number:starts.append(number) or type("R",(),{"returncode":0})()), \
             patch.object(w,"finish",lambda state:state):
            s=w.tick()
            for _ in range(20): s=w.tick()
        assert starts==[3] and s["state"]=="RUNNING"
        s["state"]="HOLD"; s["hold_reason"]="waiting for detached jobs"
        s["waiting_for_jobs"]=[{"name":"fake-job","eta":(w.now()+timedelta(hours=1)).isoformat()}]
        s["jobs_wait_started_at"]=w.stamp(); w.save(s,"test-job")
        with patch.object(w,"blockers",lambda state:["hold"]):
            assert w.tick()["state"]=="HOLD"
            job=root/"state/detached/fake-job"
            job.mkdir(parents=True); (job/"exit_code").write_text("0")
            assert w.tick()["state"]=="ARMED"
        s=w.get_state(); s["next"]="M0"
        s["armed_at"]=(w.now()-timedelta(minutes=10)).isoformat()
        s["bootstrap_sent_at"]=(w.now()-timedelta(hours=25)).isoformat()
        s["last_launch_at"]=None; s["launches"]=[]; s["backoff_until"]=None
        s["state"]="ARMED"
        with patch.object(w,"list_open",lambda:[
             {"need_id":"n-20260926-build-a001","title":"GitHub login for SMAT-Sprint","blocks_build":True},
             {"need_id":"n-20260926-build-a002","title":"Create SMAT Sprint bot, part 1","blocks_build":True}]), \
             patch.object(w,"memory_available",lambda:20*1024**3), \
             patch.object(w,"free_disk",lambda:100*1024**3), \
             patch.object(w,"another_codex_active",lambda:False), \
             patch.object(w,"active_unit",lambda number:(False,{})):
            assert w.blockers(s)==[] and s["next"]=="M1a"
        s["next"]="M8"
        with patch.object(w,"list_open",lambda:[]), \
             patch.object(w,"memory_available",lambda:20*1024**3), \
             patch.object(w,"free_disk",lambda:100*1024**3), \
             patch.object(w,"another_codex_active",lambda:False), \
             patch.object(w,"active_unit",lambda number:(False,{})):
            assert "Phase 2 go" in w.blockers(s)
print("PASS short-session backoff, one recovered launch, job hold, 24h fallback and Phase 2 gate")
