#!/usr/bin/env python3
"""External build jail for Codex. Never run foreign projects or shared units here."""
import os
import sys
from pathlib import Path

HOME = Path("/home/aurnab")
PROJECT = HOME / "projects/smat-sprint"
RECORD = HOME / "smatsprint-home"
CONFIG = HOME / ".config/smatsprint"
CODEX = HOME / ".codex"
BWRAP = "/usr/bin/bwrap"

def command(argv):
    if not argv or argv[0] != "--" or len(argv) < 2:
        raise SystemExit("usage: jail.py -- COMMAND [ARGS]")
    if not PROJECT.is_dir() or not RECORD.is_dir() or not CONFIG.is_dir():
        raise SystemExit("SMAT-Sprint paths missing")
    codex_home = RECORD / "state/codexwrap/codex-home"
    detached = RECORD / "state/detached"
    launch_requests = RECORD / "state/launcher/requests"
    build_requests = RECORD / "state/codexwrap/requests"
    project_cache = PROJECT / "cache"
    for p in (codex_home, detached, launch_requests, build_requests):
        p.mkdir(parents=True, exist_ok=True)
    args = [
        BWRAP, "--ro-bind", "/", "/",
        "--tmpfs", str(HOME / "projects"),
        "--bind", str(PROJECT), str(PROJECT),
    ]
    for name in ("smat-sprint-autoresearch-handoff",
                 "ugrp-autoresearch-handoff", "sail-sprint-20260905"):
        p = HOME / "projects" / name
        if p.exists(): args += ["--ro-bind", str(p), str(p)]
    args += [
        "--tmpfs", str(HOME / ".config"),
        "--dir", str(HOME / ".config/ugrp-forge"),
        "--dir", str(HOME / ".config/gh"),
        "--dir", str(HOME / ".config/dgist-agents"),
        "--dir", str(HOME / ".config/vastai"),
        "--dir", str(CONFIG),
        "--bind", str(CONFIG / "gh"), str(CONFIG / "gh"),
        "--tmpfs", str(HOME / ".ssh"),
        "--tmpfs", str(HOME / ".cache"),
        "--tmpfs", "/run",
        "--dir", "/run/systemd",
        "--ro-bind", "/run/systemd/resolve", "/run/systemd/resolve",
        "--tmpfs", "/tmp",
        "--dev", "/dev",
        "--proc", "/proc",
        "--ro-bind", str(RECORD), str(RECORD),
        "--bind", str(RECORD / "state/needs/requests"), str(RECORD / "state/needs/requests"),
        "--bind", str(launch_requests), str(launch_requests),
        "--bind", str(build_requests), str(build_requests),
        "--bind", str(detached), str(detached),
        "--bind", str(codex_home), str(codex_home),
        "--tmpfs", str(CODEX),
        "--ro-bind", str(CODEX / "config.toml"), str(CODEX / "config.toml"),
        "--ro-bind", str(CODEX / "AGENTS.md"), str(CODEX / "AGENTS.md"),
        "--ro-bind", str(CODEX / "rules"), str(CODEX / "rules"),
        "--unshare-pid", "--die-with-parent", "--new-session", "--cap-drop", "ALL",
        "--chdir", str(PROJECT),
        "--setenv", "HOME", str(HOME),
        "--setenv", "SMATSPRINT_HOME", str(RECORD),
        "--setenv", "CODEX_HOME", str(codex_home),
        "--setenv", "XDG_CACHE_HOME", str(project_cache / "home"),
        "--setenv", "UV_CACHE_DIR", str(project_cache / "uv"),
        "--setenv", "GH_CONFIG_DIR", str(CONFIG / "gh"),
        "--unsetenv", "GH_TOKEN", "--unsetenv", "GITHUB_TOKEN",
        "--", *argv[1:],
    ]
    session=os.environ.get("SMATSPRINT_SESSION_DIR")
    if session:
        p=Path(session).resolve()
        base=(RECORD / "state/codexwrap/sessions").resolve()
        if p.parent!=base or not p.name.isdigit() or not p.is_dir():
            raise SystemExit("invalid session directory")
        at=args.index("--unshare-pid")
        args[at:at]=["--bind",str(p),str(p)]
    return args

if __name__ == "__main__":
    os.execv(BWRAP, command(sys.argv[1:]))
