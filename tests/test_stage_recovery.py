"""Recover a staged bot into exactly one part-two phone need."""
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import service, drop, full

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    needs=root/"state/needs"
    (needs/"requests").mkdir(parents=True)
    nid="n-20260926-build-5d0b"
    n={"need_id":nid,"title":"Create SMAT Sprint bot, part 1","status":"open",
       "version":1,"telegram":{"last_sent_at":"2026-09-25T15:58:41+00:00"}}
    (needs/(nid+".json")).write_text(json.dumps(n))
    staged=root/"staged_bot.json"
    staged.write_text(json.dumps({"need_id":nid,"username":"SMAT_sprint_lab_bot",
                                  "token":"123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"}))
    made=[]
    def fake_create(spec):
        made.append(spec)
        (needs/"n-20260926-build-bbbb.json").write_text(json.dumps({
            "need_id":"n-20260926-build-bbbb","title":spec["title"],
            "status":"resolved","version":1,"telegram":{"last_sent_at":None}}))
        return "n-20260926-build-bbbb"
    service.last_issue_check=time.time()
    with patch.object(service,"ROOT",root),patch.object(service,"NEEDS",needs), \
         patch.object(drop,"STAGED",staged),patch.object(full,"MODE",root/"mode.json"), \
         patch.object(service,"create",fake_create):
        service.tick()
        service.tick()
    assert len(made)==1 and made[0]["title"]=="Start SMAT Sprint bot, part 2"
    assert made[0]["blocks_build"] is False
    saved=json.loads((needs/(nid+".json")).read_text())
    assert saved["status"]=="resolved"
    assert saved["resolution"]["detail"]=="encrypted token staged and bot identity checked"
print("PASS PC or phone bot stage recovered after restart without duplicate part-two need")
