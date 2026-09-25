"""No-Codex wrapper state and single-launch tests."""
import json, sys, tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codexwrap import wrapper as w

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    base=root/"codexwrap"
    for name in ("sessions","requests","results","rejected"):
        (base/name).mkdir(parents=True)
    aliases={"BASE":base,"SESSIONS":base/"sessions","STATE":base/"state.json",
             "REQUESTS":base/"requests","RESULTS":base/"results","EVENTS":base/"transitions.jsonl",
             "ROOT":root}
    with patch.multiple(w,**aliases):
        s=w.get_state()
        assert s["state"]=="BOOTSTRAP" and s["builder_mode"]==1
        assert w.tick()["state"]=="BOOTSTRAP"
        session0=w.SESSIONS/"0"
        session0.mkdir()
        (session0/"end.json").write_text(json.dumps({"reason":"a","milestone_complete":False,
            "waiting_for_needs":["n-20260926-build-5d0b"],"waiting_for_jobs":[]}))
        req={"schema_version":1,"id":"1111111111111111","op":"arm","next":"M0",
             "created_at":w.stamp(),"requester_pid":123}
        (w.REQUESTS/"one.json").write_text(json.dumps(req))
        with patch.object(w,"list_open",lambda:[]):
            s=w.tick()
        assert s["state"]=="ARMED" and s["next"]=="M0"
        assert "first-session exit delay" in w.blockers(s)
        assert json.loads((w.RESULTS/"1111111111111111.json").read_text())["ok"]
        req["id"]="2222222222222222"
        (w.REQUESTS/"two.json").write_text(json.dumps(req))
        with patch.object(w,"list_open",lambda:[]):
            w.tick()
        assert json.loads((w.RESULTS/"2222222222222222.json").read_text())["ok"] is False
        s=w.get_state(); s["armed_at"]=(w.now()-timedelta(minutes=10)).isoformat()
        w.save(s,"test-clock")
        calls=[]
        def fake_launch(state):
            calls.append(state["next"])
            state["state"]="RUNNING"; state["current_session"]=1; w.save(state,"test-launch")
            return state
        with patch.object(w,"blockers",lambda state:[]), \
             patch.object(w,"launch",fake_launch), \
             patch.object(w,"finish",lambda state:state):
            w.tick()
            for _ in range(20): w.tick()
        assert calls==["M0"] and w.get_state()["state"]=="RUNNING"
        s=w.get_state(); s["state"]="HOLD"; s["hold_reason"]="waiting for phone need"
        s["waiting_for_needs"]=["n-20260926-build-5d0b"]
        w.save(s,"test-hold")
        needs=w.NEEDS
        with patch.object(w,"NEEDS",root/"needs"), patch.object(w,"blockers",lambda state:["test hold"]):
            (root/"needs").mkdir()
            (root/"needs/n-20260926-build-5d0b.json").write_text('{"status":"open"}')
            assert w.tick()["state"]=="HOLD"
            (root/"needs/n-20260926-build-5d0b.json").write_text('{"status":"resolved"}')
            assert w.tick()["state"]=="ARMED"
        for bad in ({}, {"reason":"a","milestone_complete":"yes",
                       "waiting_for_needs":[],"waiting_for_jobs":[]}):
            try: w.validate_end(bad)
            except ValueError: pass
            else: raise AssertionError("invalid end accepted")
print("PASS bootstrap, arm gate, duplicate refusal, 20 restart ticks, need hold")

