#!/usr/bin/env python3
"""Nonblocking client for the SMAT-Sprint bridge need store."""
import argparse
import json
import os
import secrets
from datetime import datetime, timezone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smatsprint import needs


def main():
    parser = argparse.ArgumentParser(prog="sprintctl")
    sub = parser.add_subparsers(dest="area", required=True)
    need = sub.add_parser("need")
    actions = need.add_subparsers(dest="action", required=True)
    create = actions.add_parser("create")
    create.add_argument("--code", required=True)
    create.add_argument("--kind", choices=("phone", "pc"), required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--what", required=True)
    create.add_argument("--why", required=True)
    create.add_argument("--step", action="append", default=[])
    create.add_argument("--blocking", action="append", default=[])
    create.add_argument("--check", choices=("none", "gh_auth", "bot_owner_verified"))
    create.add_argument("--reply", choices=sorted(needs.ALLOWED_REPLIES), default="none")
    create.add_argument("--no-block-build", action="store_true")
    create.add_argument("--created-by", choices=("codex-build", "runner", "controller", "bridge", "wrapper", "watchdog"), default="codex-build")
    create.add_argument("--expires-at")
    create.add_argument("--deadline")
    create.add_argument("--consequential", action="store_true")
    create.add_argument("--skippable", action="store_true")
    status = actions.add_parser("status")
    status.add_argument("need_id")
    status.add_argument("--json", action="store_true")
    listing = actions.add_parser("list")
    listing.add_argument("--open", action="store_true")
    cancel = actions.add_parser("cancel")
    cancel.add_argument("need_id")
    cancel.add_argument("--reason", required=True)
    launch = sub.add_parser("launch")
    lsub = launch.add_subparsers(dest="launch_action", required=True)
    lr = lsub.add_parser("request")
    lr.add_argument("op", choices=("push_main","push_pages","create_deploy_key","repo_access","pages_live","restart_bridge"))
    ls = lsub.add_parser("status")
    ls.add_argument("request_id")
    build = sub.add_parser("build")
    bsub = build.add_subparsers(dest="build_action", required=True)
    ba = bsub.add_parser("arm")
    ba.add_argument("--next", choices=("M0","M1a"), required=True)
    bh = bsub.add_parser("hold")
    bh.add_argument("--reason", required=True)
    bsub.add_parser("resume")
    bsub.add_parser("release")
    bsub.add_parser("status")
    bsub.add_parser("shell")
    args = parser.parse_args()
    if args.area == "build":
        if args.build_action == "shell":
            os.execv("/usr/bin/python3",["/usr/bin/python3",
                "/home/aurnab/smatsprint-home/state/trees/service/codexwrap/jail.py","--",
                "/usr/local/bin/codex","-m","gpt-6-astra","-p","smatsprint-builder",
                "-C","/home/aurnab/projects/smat-sprint",
                "-c","plugins={}","-c","marketplaces={}"])
        if args.build_action == "status":
            p=needs.ROOT/"state/codexwrap/state.json"
            print(p.read_text() if p.exists() else '{"state":"BOOTSTRAP"}')
        else:
            rid=secrets.token_hex(8)
            req={"schema_version":1,"id":rid,"op":args.build_action,
                 "created_at":datetime.now(timezone.utc).isoformat(),
                 "requester_pid":os.getpid()}
            if args.build_action == "arm": req["next"]=args.next
            if args.build_action == "hold": req["reason"]=args.reason
            needs.atomic_json(needs.ROOT/"state/codexwrap/requests"/(rid+".json"),req)
            print(rid)
        return
    if args.area == "launch":
        if args.launch_action == "request":
            rid = secrets.token_hex(8)
            needs.atomic_json(needs.ROOT/"state/launcher/requests"/(rid+".json"),
                {"schema_version":1,"id":rid,"op":args.op,
                 "created_at":datetime.now(timezone.utc).isoformat()})
            print(rid)
        else:
            if not __import__("re").fullmatch(r"[0-9a-f]{16}",args.request_id):
                raise ValueError("request id")
            p = needs.ROOT/"state/launcher/results"/(args.request_id+".json")
            print(p.read_text() if p.exists() else "pending")
        return
    if args.action == "create":
        spec = {"code": args.code, "kind": args.kind, "title": args.title,
                "what": args.what, "why": args.why, "steps_phone": args.step,
                "steps_pc": [], "blocking": args.blocking, "check": {"id": args.check, "args": {}} if args.check else None,
                "reply": args.reply, "blocks_build": not args.no_block_build,
                "created_by": args.created_by, "expires_at": args.expires_at,
                "deadline": args.deadline, "consequential": args.consequential, "skippable": args.skippable}
        print(needs.create(spec))
    elif args.action == "status":
        value = needs.status(args.need_id)
        print(json.dumps(value, indent=2) if args.json else (value["status"] if value else "not found"))
    elif args.action == "list":
        print(json.dumps(needs.list_open(), indent=2))
    elif args.action == "cancel":
        print(needs.request_transition(args.need_id, "cancel", reason=args.reason))


if __name__ == "__main__":
    main()
