# CODEX MASTER PROMPT — SMAT reproduction and sprint-time reduction (user-steered, two lanes)

Version 1.0: written 2026-09-23 by Claude for Mushfique's Codex agent on `sail-gpu`, from the user's request of
2026-09-22 (`00_REQUEST_PROMPT.md`), after a live check of the server, the forge build, both SMAT papers page by page,
the adjacent literature and the tooling. This is the standing instruction set for building a user-steered research
programme that runs unattended for weeks. It reuses the forge handoff's loop engine, failsafes, control plane and
testing (Parts C, R, D, E, adapted) and adds the two lanes and the steering interface (Part H) and the Telegram needs
protocol with the session wrapper (Part N).

## Page one — if you remember nothing else

**What you are building, in priority order. If time, quota or context runs short, the earlier item wins.**

1. **M0.** The needs protocol, the Telegram bridge on the programme's own bot, the secret drop and the session wrapper
   (Part N). Nothing that could need the user starts before these work.
2. **M1.** The experiment lane on the lab: the reconstructed SMAT environment and staged trainer, frozen `eval/` and
   `gate/`, the queue, the runner, the worker, the hash-chained ledger, Pause/Resume that frees the GPU and the CPU
   cores. Then **the pre-loaded campaign starts and keeps running** (Part B.7).
3. **M2.** The dashboard (Watch, Steer, Ledger, Needs, Locations and settings) and the steering API.
4. **M3.** The sandbox lane, the interactive viewer, Promote, and the tested hop-in/hop-out guide (Part H).
5. **M4.** GPU-batched physics (MuJoCo Warp) behind parity gates (Part B.5).
6. **M5, M6.** Move to Vast and back; Drive archive, evacuate and restore.
7. **M7.** The paper package, the weekly note, the optional summaries, the monthly novelty re-query.

**Rules that override everything else.**

- You are the builder, not the programme: no goal mode, no thread goal, no watching. Build, test, start, report, stop.
- Nothing invents or launches experiments on its own. The runner executes the queue the user steers and the campaign
  pre-loaded from Part B; when the queue empties it runs the pre-planned evergreen tasks and asks the user.
- The success criteria (Part G) govern. `gate/` and `eval/` are frozen against everyone who queues, steers or runs
  experiments, **the user included**; no band is ever relaxed after a result exists.
- Steering changes what runs next, never what already ran or how it is judged. The sandbox cannot change the
  experiment; Promote (one config, never a checkpoint or result) is the only bridge.
- Never wait for the user at the PC: create a need (Part N) and carry on with everything else.
- Fail the job, never the runner. Nothing is deleted or destroyed before its replacement copy is verified.
- No user credential ever reaches a rented host; no secret ever enters the repository, the status branch or the
  Pages site; no password is ever asked for or sent over Telegram.
- Nothing the user can press ships before its tests pass.
- **Never touch the forge** (the UGRP project building beside you): its units, slices, files, bot, `gh` session,
  Vast instances or disk margin. Never reboot the shared server; never touch other users' processes.
- No ceremony: git, the ledger and the tests are the audit trail. Runs, not audits.

**How to read.**

- Read `00_README.md` first: the defaults chosen for the user and the user's answers. Where they differ from this
  prompt, the README wins; where the user is silent, use the defaults and list them at the top of your first report.
- Read this prompt once, in full, then `02_RESEARCH_DIRECTIONS.md`. Re-read the governing Part at the start of any
  session that builds the component it governs (table below).
- Do **not** read `01_PAPERS.md` or `03_PAPER_DIGESTS.md` end to end. Open them by cluster or paper when you need one.
  `research-data/infra/smat_spec.json` is the machine-readable SMAT specification; use it when building the
  environment, the rewards and `eval/`.
- Then follow Part E.8. A later session reads `AGENTS.md`, then `docs/PROGRESS.md`, then the Part named there.

---

## PART A — Mission, what went wrong before, and hard constraints

### A.1 Mission in one paragraph

Build and hand over a **user-steered simulation research programme** that (Phase 1) independently reconstructs SMAT
(Staged Multi-Agent Training for co-adaptive hip-exoskeleton control; Yuan, Zhou, Androwis; NJIT and Kessler
Foundation; arXiv 2603.07618, IROS 2026, and the extended arXiv 2608.00715) in MyoAssist on MuJoCo, converges to its
published **simulated** numbers or better under bands fixed in advance, and tests whether its gain survives the
controls the papers did not run (the reward-matched zero-torque human, a matched rate-limited velocity-proportional
controller, a matched phase profile); and then (Phase 2) attacks the lab's actual goal: reducing **simulated 200 m
sprint time** with a wearable hip exosuit under realistic actuator limits. The authors' code is not public (the official
`Fitz-Yuan/SMAT-Exo` repository was still a 131-byte README on 2026-09-22), so the reconstruction is the only route, and
with about forty unspecified implementation choices it can only be done by running hundreds of training attempts
unattended, with the published numbers as the target and honest tolerances fixed first. Codex (you) sets everything
up, tests it adversarially, pre-loads the queue, starts it, writes the user's guide, reports on Telegram and stops.
The runner then runs for days; the user steers from a dashboard and a CLI, hops in and out whenever they like, and
tests ideas in a sandbox that cannot change the experiment. Nothing may be faked, inflated or quietly narrowed, and the
programme must be able to come back with "it does not reproduce" or "a simpler controller does the same", with
evidence.

### A.2 What went wrong before (so you do not repeat it)

- **Since 27 August the SAIL sprint work produced no SMAT training run.** It produced audits, coverage ledgers, a
  34-slide deck, a browser viewer, a Kinesis preparation, a code-availability audit and specification revisions. The
  Codex thread of 13 September (`01a09685…`) ended with an excellent audit and the sentence "No physics or training
  was started." Everything was "researcher-operated" in the worst sense: the RTX 5090 sat idle waiting for the user to
  press Load. Nothing ran while the user was away.
- **Earlier research loops spiralled.** A previous task (recorded in the KB's `03-research-loop-failures.md`) spent
  weeks on execution-security attestation and specification versions V11 to V46 without a scientific run; another
  killed every direction with a novelty filter before testing it. Test counts and hash counts are not progress.
- **The forge build (2026-09-22) taught three operational lessons, all encoded here:** goal mode turns Codex into the
  loop and burns tokens narrating transfers; a device code printed in a terminal expires unread while the user is away
  (Part N exists for this); and a dedicated bot for replies is needed because the shared DGIST bot is already
  long-polled by another service.

**Consequence:** the deliverables are the running programme, the numbers, and the paper package. Build the
infrastructure that makes runs trustworthy and steerable, then let it run. Do not build another deck, coverage
ledger, Notion revision or attestation framework.

### A.3 The philosophy

- **Reproduction by search, judged by a frozen gate.** The papers specify the architecture, the rewards, the PPO
  settings and the stage budgets, and leave about forty choices open (observations, normalisation, action mapping,
  reference motion, resets, critic inputs, update form, step counting, device mass; Part B.3). They are not guessed by
  thinking; they are swept, with budgets and selection rules declared first, against the bands of Part G.
- **Mechanism over headline.** The Stage-4 exo reward is maximised by velocity-proportional torque, and the reported
  activation reduction changes reward and torque at the same time (Part G.1). The decisive experiments are therefore
  the controls: B0 (the Stage-4 human reward at zero torque) and the matched velocity and phase controllers. If they
  match SMAT, that is a mechanism finding and a paper, not a failure.
- **Throughput is the lever (the DeepSeek lesson).** Physics is the bottleneck, not the networks. SMAT's 547 M
  transitions take about 150 h at the authors' CPU rate, and a reproduction search needs hundreds of pipelines. The
  SMAT authors themselves moved to MuJoCo Warp through mjlab for UniExo. Make GPU-batched physics a first-class track
  with parity gates (Part B.5); until it is certified, use the 64 CPU cores well.
- **The user steers; the runner runs; the sandbox is for play.** The programme never decides the research. It
  executes what is queued, shows what happened in plain words, and asks on Telegram when it needs a decision.
- **Honest in both directions.** Equal budgets, disjoint seeds, all failures kept, checkpoints never chosen by the
  reported metric, bands never moved. A clean negative with an open implementation is a publishable result.
- **Ambition in Phase 2.** New curricula, factorisations, action representations, energy-recycling or clutch actions,
  personalisation latents, device co-design: whatever the evidence supports, provided every gain survives matched
  budgets, matched physiology and the realistic actuator.

### A.4 Environment facts (verified 2026-09-23 over SSH and the GitHub API; re-verify anything you rely on)

**Lab server `sail-gpu`** (host `sail-gpu01`; Tailscale name `sail-gpu01.taile67bdb.ts.net`; user `aurnab`; SSH from the
user's Windows PC with the alias `sail-gpu` and Windows OpenSSH only; Git Bash's ssh fails on that PC):

- Ubuntu 24.04.4 LTS, kernel 7.0.0-30, systemd 255; AMD EPYC 9535, 64 cores, 128 threads; **30 GB RAM** (24 GB
  available at the check); swap 7 GB. **Disk: 82 GB free of 915 GB (91 % used)**, shared with other members; it moves
  by tens of GB a day. Largest projects of this account: `ugrp-neurips-2027` 47 GB (the user's old project), the forge
  `ugrp-cl-autoresearch` 23 GB, `sail-local-ai` 20 GB, `fly-claw` 11 GB, `sail-sprint-20260905` 11 GB.
- One **RTX 5090, 32 GB**, driver 595.84, compute capability 12.0 (sm_120); idle at the check (15 MiB used, 0 %).
- User systemd with **lingering on**; the user manager delegates **`cpu memory pids`** only (no `cpuset`, no `io`), so
  `CPUQuota` and `MemoryMax` work in user slices and CPU pinning is not a cgroup guarantee. Existing user units belong
  to other projects: the forge (`clforge-controller`, `clforge-director`, `clforge-worker` active; `clforge-watchdog`
  and `clforge-daily-summary` timers), the DGIST agents (`dgist-course-telegram` and `dgist-otp-bridge` active, others
  on timers), `llama-swap`, `open-webui`, and an old `ugrp-dashboard-forward-…` unit of the previous UGRP project in
  an auto-restart loop (not ours; leave it). Listening ports include 22, 443, 631, 7070, 8080, 8081, 8443 (Tailscale
  Funnel; never touch), 8766 and 11434. **Reserve this programme's ports in 8800–8809** after `ss -ltn` (the forge
  reserved 8790–8799).
- Tools: `uv` 0.12.7 at `~/.local/bin/uv` (not on the PATH of non-interactive shells or units: use absolute paths);
  system Python 3.12.3; `codex` 0.153.4 at `/usr/local/bin/codex` (default model `gpt-6-astra`, reasoning `xhigh`;
  models on the account: `gpt-6-astra`, `gpt-reserve`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.5`, and
  `codex-auto-review`, which is the approval reviewer, not a working model); `claude` 2.1.263; bubblewrap 0.9.0 with the
  Ubuntu AppArmor profile installed (by the forge; its jailed CUDA probe passed); and, installed by the forge into
  `~/.local/bin`, `gh` 2.101.0, `rclone` 1.75.1, `vastai` 1.8.0 and ShellCheck. Reuse the binaries; never reuse their
  configurations (Part N.7, D.6, D.7).
- **The Codex Linux sandbox hides the GPU** and, in `workspace-write`, mounts `.git` read-only and blocks local sockets
  when network is off; start GPU or network work as `systemd-run --user` units (Part E.4) and see Part N.8 for how
  unattended build sessions run.
- **The previous sprint project** `/home/aurnab/projects/sail-sprint-20260905` (read-only for you; copy, never modify):
  `.venv` (Python 3.12.3, MuJoCo 3.4.0, MyoSuite 2.8.4, Stable-Baselines3 2.9.0, torch 2.14.0+cu130, with
  `assist_sim` and `myo_sim` installed), `.venv-deprl` (Python 3.10.21, MuJoCo 3.1.2, DEP-RL 0.4), the MyoAssist
  checkout `myoassist/` at commit `b1baf69` (2026-08-25; the current main on 2026-09-22), the old four-stage 22-muscle
  ankle integration `smat_integration.py`, the viewer `reproduction/2026-09-13/viewer/user_controlled_viewer.py`, and
  the `reproduction/2026-09-13/` audit. Keep both environments as they are and build this programme in a new project
  directory with its own pinned environment.
- **MyoAssist facts that shape Part B** (checked in that checkout): `myo_sim`'s `myolegs26` has 13 muscles per side
  (`abd, add, hamstrings, bifemsh, edl, fdl, glutmax, iliopsoas, rectfem, vasti, gastroc, soleus, tibant`); `assist_sim`
  ships the hip device **`Hippo_L1`**, declared compatible with `myolegs26`: a pelvis backplate, hip shell, waist bands,
  an AK10-9 actuator block and two thigh links with cuffs, **4.90 kg** in total from the XML inertials, attached to
  `pelvis`, `femur_r` and `femur_l`, with ideal bidirectional hip-flexion actuators `Exo_R` and `Exo_L` of gain 100 and
  control range [−1, 1] (±100 Nm at full command), to be rescaled to SMAT's 6 Nm and 25 Nm stage scales; SMAT's
  hardware device weighs 5.94 kg and its simulated mass is not reported. MyoAssist's RL code composes human, device and
  terrain, trains separate human and exo networks with a shared "common critic" through Stable-Baselines3 with
  per-network observation indexing (`net_indexing_info`), defaults to 30 Hz control and 1,200 Hz physics, ships
  `short_reference_gait.npz` and `segmented.npz`, and has **no staged freezing, no 26-muscle training config and no
  GPU-batched physics**; all three must be built (Part B.2).
- **The forge** (`/home/aurnab/projects/ugrp-cl-autoresearch`, GitHub `mushfique-dgist/ugrp-cl-autoresearch`) is being
  built right now by another Codex task and is in its milestone M1: its units run, its `clforge.slice` caps memory at
  20 GB and its worker at 16 CPU threads, it keeps a shared-filesystem free-space floor of 60 GB, its `gh` session
  lives in `~/.config/gh`, its secrets in `~/.config/ugrp-forge/` (including its own bot `@UGRPforge_bot`), and its Vast
  label prefix is `ugrp-forge-`. **It is off limits** (Part A.5 rule 11).
- **Telegram:** the DGIST bot's token and the owner chat id are in `~/.config/dgist-agents/course/service.env`
  (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID`; a `TELEGRAM_GROUP_CHAT_ID` also exists and must **never** be used).
  That bot is long-polled by `dgist-course-telegram.service`, so this programme only ever calls `sendMessage` on it,
  during the M0 bootstrap, and gets its own bot for everything else (Part N). Gmail SMTP credentials for fallback
  alerts are in `~/.config/dgist-agents/{menu,notice}/service.env` (`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`,
  `GMAIL_SMTP_HOST`, `GMAIL_SMTP_PORT`, `GMAIL_TO`). Read these at runtime; never copy them anywhere.
- **Tailnet:** the peers are `sail-gpu01`, the user's PC `desktop-ri4gdgu`, a `macbook-air` and `magzhan-windows`. **The
  user's phone is not on the tailnet**, so nothing phone-facing may depend on it (Part N.6).
- **Vast.ai:** the shared team account "UGRP Exp" (id 577762), key at `~/.config/vastai/vast_api_key`, shared with other
  people and with the forge. Only ever act on instances labelled `smatsprint-`. A read-only market snapshot of
  2026-09-23 found CPU-heavy offers such as a 128-effective-core host at $0.327/h, and on-demand single RTX 5090 offers
  at $0.47–0.60/h with 8–48 effective cores; bandwidth prices differ by up to 500× between hosts, so the cost model must
  include them (Part D.6).

**User's Windows PC** (`desktop-ri4gdgu`): `gh` logged in as **`mushfique-dgist`** (plan **Pro**); the repository name
`mushfique-dgist/smat-sprint-lab` was free on 2026-09-23; the account already publishes a Pages site from
`course_monitor`, so Pages sites share the `mushfique-dgist.github.io` origin (Part D.3). No `vastai` or `rclone` on the
PC. The user's shell is **Windows PowerShell 5.1**: every command written for the PC uses no `&&`, no `||`, no
`2>/dev/null`.

**GitHub Pages from a private repository is public** on a Pro account; the dashboard is an empty static shell that
fetches everything at view time through the API with a token that lives only in the user's browser (Part D.3).

### A.5 Non-negotiable rules

1. **No fake results, no narrowed goals, no silent scope changes.** If a band cannot be met, the dashboard says so and
   the queue continues; the band never moves (Part G.8).
2. **No metric hacking.** `eval/` and `gate/` are frozen and hash-checked; reported checkpoints are chosen by a
   registered rule, never by the reported metric; evaluation seeds, held-out partners and held-out data are never used
   for selection or tuning (Part C.10, G.5).
3. **Compute and budget honesty.** Every run records transitions, per-actor updates, wall-clock, backend, hardware and
   peak memory; comparisons are at matched transitions, torque budget, code identity, backend class and hardware class,
   or are labelled "not comparable" (Part C.10).
4. **Preserve everything that ran.** Failed, killed and suspect runs stay in the ledger with their reasons; nothing is
   deleted to make a number look better.
5. **Be a good neighbour on the shared machine.** Honour Pause immediately: ≤ 60 s from the controller seeing the
   command, ≤ 90 s from the button, to a GPU and CPU free of this programme's processes (Part D.1). **Polite mode**
   (default on): pause when another Linux account's GPU process holds more than 1 GiB for more than 60 s, resume after
   10 quiet minutes; same-account processes (the forge, `llama-swap`, `open-webui`) coexist and are counted as used
   memory, never killed or reconfigured. **Disk:** this programme's own cap is 30 GB (experiment and sandbox together);
   it starts no new job, download or archive when the shared filesystem's free space is below `min_free_gb` = 65 GB, so
   that it is never the reason the forge reaches its 60 GB floor; below `hard_floor_gb` = 55 GB it checkpoints and stops
   (SAFE_PAUSE). Everything the programme writes lives under its own directories (`TMPDIR`, `UV_CACHE_DIR`,
   `XDG_CACHE_HOME`, `WARP_CACHE_PATH`, Triton and Inductor caches point into `<project>/cache/`), nothing under `/tmp`.
   Never kill other users' processes; never reboot `sail-gpu`.
6. **Money.** Vast spend has per-instance and monthly caps (defaults USD 60 per rental and USD 150 per calendar month)
   below hard ceilings in `~/.config/smatsprint/limits.toml`, changed only over SSH. Never rent without a lease record;
   never touch an instance without the `smatsprint-` label.
7. **LLM use inside the programme** is bounded and never inventive: at most 3 plain-language summaries of finished runs
   per day, read-only, zero allowed (Part C.13). You, Codex, never stay alive to watch anything.
8. **Secrets** live only in `~/.config/smatsprint/` (mode 0700; files 0600), never in argv, logs, the repository, the
   status branch, the Pages site, a Telegram message or a Vast host. Tracebacks are scrubbed against secret patterns
   before they reach the status branch or a message.
9. **One writer per record.** The runner is the only writer of the ledger, registered configs and the outbox; the
   controller of `state/` and `record/`; the worker of the live `work/`; the bridge of need transitions. The lab's
   clone is the source of truth for code; the lab never pulls code from GitHub.
10. **Ask only when it matters, and only through a need.** Infer routine details. Anything only the user can do or
    decide is a need on their phone (Part N), mirrored in `docs/USER_ACTIONS.md`; carry on with everything else.
11. **The forge is off limits.** Do not read its secrets, stop or edit its units, use or log out its `gh` session, poll
    its bot, touch its Vast instances (`ugrp-forge-*`), write into its directories, or push the shared disk below its
    floor. Read its public design (its `docs/PLAN.md` and parts of its handoff) only to reuse proven recipes, and copy
    code with attribution rather than importing from its tree.
12. **Lanes.** Nothing crosses from the sandbox to the experiment except a config through Promote (Part H.8); the
    experiment lane is modified only through the steering API (Part H.5).
13. **No human experiments, no hardware commands, no e-mails to authors, no licence activation, no Notion or lab-wiki
    edits by the programme.** Bench and human work are the user's and gated by the lab. SCONE/Hyfydy is not used
    (the lab's trial licence is Ryu's and expires 2026-09-25); a SCONE cross-simulator study is planned only if the user
    later confirms a lab licence.
