# SMAT-Sprint build plan — 2026-09-26 KST

## Defaults assumed in the first report
Separate sibling project `smat-sprint`, private repository `mushfique-dgist/smat-sprint-lab`, and separate Telegram bot. Builder mode 1, in a build jail. Phone is not assumed on the tailnet. Experiment ceiling: 48 threads and 12 GB RAM; sandbox: 16 threads, 6 GB RAM and 4 GB VRAM; build: 8 threads and 6 GB RAM. Sandbox idle stop: 2 hours. Up to 3 read-only run summaries per day. Park the GPU after the paper gate. Venue: RA-L, then IROS 2027 transfer if available. Phase 2 waits for the user's go. Author materials and a SCONE licence are unconfirmed. Drive quota is unknown; lean archives. No extra server rules supplied. KB weekly-note vocabulary and the venue's official manuscript class. Project disk cap: 30 GB; job admission preserves 63 GB shared free space, hard pause under 55 GB and automatic disk resume after 60 GB holds for 30 minutes. Seeds: at least 3 full pipelines through L3, 5 for superiority, 10 for equivalence. Vast caps: USD 60 per rental and USD 150 per month for this programme, pending the user's budget-scope answer.

## Live environment and Phase 0 evidence
- Handoff source: `/home/aurnab/projects/smat-sprint-autoresearch-handoff/`, kept read-only. This document and the spec snapshot are in this new repository.
- `gh` 2.101.0 copied to `/home/aurnab/.local/share/smatsprint/bin/gh`; `sha256sum -c` passed. Its separate `GH_CONFIG_DIR` has mode 0700 and `hosts.yml` mode 0600. Device login finished as `mushfique-dgist`. The forge's `~/.config/gh` was not used.
- The configured DGIST bot `sendMessage` failed with HTTP 400, "chat not found", for the exact positive `TELEGRAM_OWNER_CHAT_ID` in the course service env. No group id was read. `getMe` showed `dgist_bot`; `getChat` on the owner id also failed. The first GitHub need reached the configured Gmail fallback, `aurnab0001@gmail.com`, and the login succeeded. This address is a single recipient. The Telegram route remains open.
- 105 GB free on the shared 915 GB filesystem; 24 GiB MemAvailable in 30 GiB RAM; one RTX 5090, driver 595.84, about 521 MiB in use at the check. Ports 8800–8809 appeared free. Linger=yes and user cgroup delegation is cpu, memory, pids. No shared server reboot or other-project change.
- The forge controller and director are active; its worker is failed. Its state is read-only here. DGIST course Telegram service is active.
- Server Codex CLI is 0.155.0-alpha.16.4 (handoff probed 0.153.4); `codex exec --help` still lists builder-mode bypass, auto-review, profile, JSON and output flags. Exact behavior still requires canaries.
- Old sprint venv torch 2.14.0+cu130 saw the RTX 5090 from this shell and a transient user unit. A 64x64 MuJoCo EGL frame rendered. Bubblewrap with a broad /dev test bind ran that same canary. The final build jail's narrower mounts and secrecy checks remain to be tested.
- A transient scope accepted `BindsTo=` and `After=` under user systemd 255. systemd-oomd is active; full unit-specific OOM score checks remain.
- Remaining prerequisite probe: headless Chromium from this project's cache and final build-jail CUDA matmul; run detached if over ten minutes.

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
