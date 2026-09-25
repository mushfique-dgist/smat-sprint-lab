# SMAT-Sprint build plan — 2026-09-26 KST

## Defaults assumed in the first report
Separate sibling project `smat-sprint`, private repository `mushfique-dgist/smat-sprint-lab`, and separate Telegram bot. Builder mode 1, in a build jail. Phone is not assumed on the tailnet. Experiment ceiling: 48 threads and 12 GB RAM; sandbox: 16 threads, 6 GB RAM and 4 GB VRAM; build: 8 threads and 6 GB RAM. Sandbox idle stop: 2 hours. Up to 3 read-only run summaries per day. Park the GPU after the paper gate. Venue: RA-L, then IROS 2027 transfer if available. Phase 2 waits for the user's go. Author materials and a SCONE licence are unconfirmed. Drive quota is unknown; lean archives. No extra server rules supplied. KB weekly-note vocabulary and the venue's official manuscript class. Project disk cap: 30 GB; job admission preserves 63 GB shared free space, hard pause under 55 GB and automatic disk resume after 60 GB holds for 30 minutes. Seeds: at least 3 full pipelines through L3, 5 for superiority, 10 for equivalence. Vast caps: USD 60 per rental and USD 150 per month for this programme, pending the user's budget-scope answer.

## Live environment and Phase 0 evidence
- Handoff source: `/home/aurnab/projects/smat-sprint-autoresearch-handoff/`, kept read-only. This document and the spec snapshot are in this new repository.
- `gh` 2.101.0 copied to `/home/aurnab/.local/share/smatsprint/bin/gh`; `sha256sum -c` passed. Its separate `GH_CONFIG_DIR` has mode 0700 and `hosts.yml` mode 0600. Device login finished as `mushfique-dgist`. The forge's `~/.config/gh` was not used.
- The configured DGIST bot `sendMessage` failed with HTTP 400, "chat not found", for the exact positive `TELEGRAM_OWNER_CHAT_ID` in the course service env. No group id was read. `getMe` showed `dgist_bot`; `getChat` on the owner id also failed. The first GitHub need reached the configured Gmail fallback, `aurnab0001@gmail.com`, and the login succeeded. This address is a single recipient. The Telegram route remains open.
- 105 GB free on the shared 915 GB filesystem; 24 GiB MemAvailable in 30 GiB RAM; one RTX 5090, driver 595.84, about 521 MiB in use at the check. Ports 8800–8809 appeared free. Linger=yes and user cgroup delegation is cpu, memory, pids. No shared server reboot or other-project change.
- The forge controller and director are active; its worker is failed. Its state is read-only here. DGIST course Telegram service is active.
- Project AGENTS.md appears in a fresh rendered prompt; context audit passed with the live default gpt-5.6-sol, while the handoff assumed gpt-6-astra. Wrapper will select its model explicitly without editing the shared config.
- Server Codex CLI is 0.155.0-alpha.16.4. A real builder-mode-1 Codex canary returned CHECKED from the CPU-only jail with a private Codex home. The shared config was not changed; GPU behavior remains untested.
- Old sprint venv torch 2.14.0+cu130 saw the RTX 5090 from this shell and a transient user unit before foreign GPU use was reported. A 64x64 MuJoCo EGL frame rendered. The final CPU-only build jail passed secrecy and namespace canaries; its CUDA path remains untested.
- A transient scope accepted user-systemd dependency settings. systemd-oomd is active. The M0 services are enabled with the wrapper unarmed; full science unit OOM checks remain.
- Headless Chromium loaded the local drop page and cross-checked a sealed box against PyNaCl; a bad fingerprint was refused. Pages returned HTTP 200 for the shell and drop assets. GPU work is deferred because another autoresearch is using the GPU; the final build-jail CUDA matmul remains open.

## M0 implementation status
- Private repository created and main pushed with a programme-only Ed25519 deploy key. GitHub's published Ed25519 host fingerprint matched the pinned known-host entry. gh-pages is an orphan branch with only the public shell; Pages reports gh-pages as its source and serves the files.
- A send-only needs bridge and CLI are running as a user service. Need 1 closed by gh_auth; need 2 (BotFather) was delivered through the configured Gmail fallback. Telegram delivery remains unverified.
- The encrypted drop shell passed a real-browser/PyNaCl round trip and deterministic cross-implementation vector. Private issue intake, owner association, duplicate skip, bot getMe and /start validation passed against fakes. Real token delivery remains pending.
- The launcher accepts a fixed operation registry. Jailed repo_access, push_main, restart_bridge, create_deploy_key and pages_live requests passed; an unregistered shell request was refused. Services run from the pinned svc-2 worktree. Later service releases remain gated by tests.
- A CPU-only bubblewrap jail passed foreign-directory, secret canary, process, user-bus, no-GPU, read-only state and writable-spool canaries. A real Codex canary in builder mode 1 and a jailed launcher push canary passed. The wrapper is installed; its live state is in state/codexwrap/state.json.
- The full bot receive path exists but remains gated in send-only mode until remaining fake-backend and real-phone tests pass. The wrapper is installed and an M0 continuation can do independent CPU work. The open bot need blocks only the bot connection. The launcher and wrapper still need their full Part N.11 matrices.

## Order and acceptance
1. M0: need store, typed templates, send-only bridge and fallback, secret drop, own bot, strict owner validation, jail, named-operation launcher and wrapper. Use the fake Bot API and crash tests in Part N.11 before trusting full mode. The bridge failure above must be visible and have a working phone fallback.
2. M1a: pause path and resource admissions first; compose and hash the model; trainer and frozen walk gate; real L0 pipeline; registered Q0–Q2 campaign; one pause/resume and SIGKILL-resume drill. No scientific claim before these pass.
3. M1b: matched controls, method gate and full crash matrix while Q2 runs.
4. M2: state machine, steering, dashboard and Pages, owner-approved devices, weekly note.
5. M3: isolated sandbox, viewer, Promote and tested guide.
6. M4: Warp parity and measured end-to-end throughput. CPU remains the reference evaluator.
7. M5–M6: Vast and Drive behind fake fault matrices and a real rehearsal under USD 5.
8. M7: paper package and weekly chaos drill. M8 begins only after the user's phone go.

No experiment result, running campaign, finished M0, bot bridge or unattended wrapper is claimed in this plan.
