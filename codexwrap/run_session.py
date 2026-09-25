"""One bounded Codex build session, run by a transient user unit."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from smatsprint.needs import ROOT

PROJECT = Path("/home/aurnab/projects/smat-sprint")
BASE = ROOT / "state/codexwrap/sessions"
CODEX = "/usr/local/bin/codex"
JAIL = Path(__file__).resolve().parent / "jail.py"

def now(): return datetime.now(timezone.utc).isoformat()

def run(number):
    if not number.isdigit() or str(int(number)) != number:
        raise ValueError("invalid session number")
    directory = BASE / number
    if not directory.is_dir() or not (directory / "prompt.md").is_file():
        raise ValueError("session is not prepared")
    os.umask(0o077)
    env = {
        "PATH": "/home/aurnab/.local/share/smatsprint/bin:/home/aurnab/.local/bin:/usr/local/bin:/usr/bin:/bin",
        "HOME": "/home/aurnab",
        "SMATSPRINT_HOME": str(ROOT),
        "CODEX_HOME": str(ROOT / "state/codexwrap/codex-home"),
        "SMATSPRINT_SESSION_DIR": str(directory),
        "GH_CONFIG_DIR": "/home/aurnab/.config/smatsprint/gh",
        "GH_PROMPT_DISABLED": "1",
        "TERM": "dumb",
    }
    command = [
        "/usr/bin/python3", str(JAIL), "--", CODEX, "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "-c", "shell_environment_policy.ignore_default_excludes=false",
        "-c", "plugins={}", "-c", "marketplaces={}",
        "-m", "gpt-6-astra", "-p", "smatsprint-builder",
        "-C", str(PROJECT), "--json",
        "-o", str(directory / "last_message.md"), "-",
    ]
    (directory / "started_at").write_text(now() + "\n")
    with (directory / "prompt.md").open("rb") as prompt, \
         (directory / "events.jsonl").open("ab", buffering=0) as events, \
         (directory / "stderr.log").open("ab", buffering=0) as errors:
        process = subprocess.Popen(command, stdin=prompt, stdout=events, stderr=errors, env=env)
        exit_code = process.wait()
    (directory / "exit_code").write_text(str(exit_code) + "\n")
    (directory / "service_result").write_text("success\n" if exit_code == 0 else "exit-code\n")
    (directory / "ended_at").write_text(now() + "\n")
    for line in (directory / "events.jsonl").read_text(errors="ignore").splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            (directory / "thread_id").write_text(event["thread_id"] + "\n")
            break
    return exit_code

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("one session number required")
    raise SystemExit(run(sys.argv[1]))
