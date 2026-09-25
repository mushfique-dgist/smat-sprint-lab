# SMAT reproduction and sprint-time reduction ("SMAT-Sprint") — handoff to Codex

Written 2026-09-23 by Claude for Mushfique, from your request of 2026-09-22 (`00_REQUEST_PROMPT.md`, kept here
unchanged). This folder is everything Codex needs to build, test and start a **user-steered** research programme on
`sail-gpu`, and then leave it running without spending tokens. It is mirrored on the server at
`/home/aurnab/projects/smat-sprint-autoresearch-handoff/`.

## What is in this folder

| File | What it is |
|---|---|
| **`CODEX_MASTER_PROMPT.md`** | The instruction set, assembled from `parts/`. Nine parts: mission and rules (A), **success criteria (G, the governing part)**, the research programme and pre-loaded campaign (B), **needs, Telegram bridge, secret drop, build jail and session wrapper (N, built first)**, **the two lanes, steering, sandbox and the hop-in/hop-out guide (H)**, the runner (C), failsafes (R), control plane, dashboard and moves (D), testing and milestones M0–M8 (E). About 150 pages; later sessions read only the part they are building. |
| **`01_PAPERS.md`** | The verified reading list: twelve clusters, tiered must-read / should-read / reference, each entry with what to take, what it left untested for this programme, what it costs on our server, and its code status on the check date. Every arXiv id and DOI re-checked by script (`research-data/verification.json`). |
| **`02_RESEARCH_DIRECTIONS.md`** | The reasoning: what the SMAT papers actually show, the search space, the measured throughput, the campaign, the mechanism hypotheses, the sprint thesis, the ranked portfolio with kill rules. About 12 pages; read in full. |
| **`03_PAPER_DIGESTS.md`** | Implementation-grade notes on the cornerstone papers and on MyoAssist's code, written from the PDFs and the code, with the KB's earlier readings checked against the sources. |
| `parts/` | The source of the master prompt. Edit a part, then run `python assemble.py` and `python tools/check_prompt.py`. |
| `research-data/` | The raw data: `infra/smat_spec.json` (the machine-readable SMAT specification, every number with its page), `infra/myoassist_facts.json` (the code facts), `infra/infra_facts_services.json` and `infra_facts_tooling.json` (Telegram, GitHub, Google, Codex, Vast and venue facts with sources), `infra/gpu_physics_facts.json`, `probe/results_2026-09-23/` (the GPU and CPU measurements on `sail-gpu`), `papers/`, `digests/`, `direction-check/` (the novelty check), `verification.json`, and `prompt-review/` (the adversarial review and what was applied). |
| `tools/` | `build_papers.py`, `build_digests.py`, `verify_arxiv_ids.py` (arXiv and DOIs), `check_prompt.py`, `papers_front_matter.md`. |

## The short version of what Codex is told to do

1. **Needs first (M0).** Every time Codex or the programme needs you, you get one Telegram message you can act on
   from your phone (the link, the code, the expiry, buttons for Done, Later, "Send a new code", Skip), and everything
   else keeps going. A small bridge service on the programme's own bot receives your taps; a secret-drop page lets you
   hand over a token from the phone without chat; a session wrapper launches each Codex build session **inside a jail
   that hides your other passwords and tokens** (the forge's, the DGIST agents', the Vast key), reports milestones to
   you on Telegram, waits for the needs, and launches the next. **Codex never waits and never burns tokens waiting.**
2. **The experiment lane (M1a), then the campaign runs.** A reconstructed SMAT environment on MyoAssist's composed
   26-muscle human and hip device, a staged two-actor PPO trainer with freezing proven by weight hashes, frozen
   `eval/` and `gate/`, a hash-chained ledger, and Pause/Resume that frees the GPU and the CPU cores within about a
   minute. As soon as those pass their tests, the **pre-loaded campaign** (Part B.7) starts; the rest of the
   experiment machinery (M1b) is built while the first search runs.
3. **You steer; the runner runs.** Nothing invents experiments. From the dashboard (GitHub Pages, phone and PC),
   Telegram decision buttons or SSH you reorder the queue, pause, kill, requeue, edit a candidate for its next run,
   add seeds, change budgets, launch sweeps with a declared budget and selection rule, and move the work. Every change
   is logged with your reason. You cannot change how results are judged, delete a run, or edit a running job, and
   nobody else can either.
4. **The sandbox is yours (M3).** A separate lane with its own tree, resources, environment and a viewer where you
   load any checkpoint, step, pause, run, change the torque scale live and render. It cannot touch the experiment;
   tests prove it. **Promote** is the only bridge: it sends a config (never a checkpoint or result) to the experiment
   as a new pre-registered candidate that trains from scratch, and only after you confirm it outside the sandbox.
5. **Success criteria govern (Part G).** A frozen ladder L0 (plumbing) → L1 (walking) → L2 (passive device) → L3
   (reproduction) → L4 (better) → L5 (sprint), and a paper gate with three paths: a method result, a rigorous
   reproduction or mechanism result, or an open benchmark. Bands are fixed now, before any result exists.
6. **Throughput (M4).** MuJoCo Warp on the 5090, certified by statistical and learning parity against CPU MuJoCo, with
   every reported number measured on CPU physics.
7. **Moves and Drive (M5, M6)** exactly as you specified: Pause, Resume, Move to Vast, Move to Lab, Backup to Drive,
   Evacuate, Restore, Destroy Vast, Stop, Emergency stop; tested against thousands of random failure sequences with
   fake back ends, then rehearsed once for real for under $5.
8. **Phase 2 on your go (M8).** When you tap "Start Phase 2", the wrapper launches the Codex build of the sprint part
   (the sprinting human first, then the device matrix). Nothing to do at the PC.

## How to start it (the only step at the PC)

1. On your PC, open a **new** Codex thread on `sail-gpu` with working directory `/home/aurnab/projects`. **Do not turn
   on goal mode and do not set a thread goal.** Give it the access the forge build had (network, user-space installs,
   `systemctl --user`, SSH).
2. Paste this as the first message. The last line is your builder-mode choice (see "Builder mode" below); leave it at
   `1` unless you want something else:

   > Read `/home/aurnab/projects/smat-sprint-autoresearch-handoff/00_README.md` first, then follow Part E.8 of
   > `CODEX_MASTER_PROMPT.md` (its step 0 starts my GitHub login before anything else), then read the prompt once in
   > full (start with its Page one) and `02_RESEARCH_DIRECTIONS.md`. Open `01_PAPERS.md` and `03_PAPER_DIGESTS.md` only
   > by cluster or paper when you need them. Do not set a thread goal and do not use goal mode. Everything you need
   > from me becomes a need on my phone (Part N); never wait for me at the PC. List the defaults you assumed at the top
   > of your first report.
   > Builder mode: 1

3. **Keep your phone near you for about 30 minutes.** First a GitHub login code arrives in the **DGIST bot chat**,
   without buttons (do not reply there; that chat belongs to the course monitor). Then a request to create the
   programme's own bot, which takes about 3 minutes in BotFather. If you miss a code, a new one comes at the next of
   08:00, 12:00, 18:00 or 21:00 KST (none at night). If you are away for a whole day, the experiment starts anyway and
   only the dashboard waits for you. From then on the session wrapper launches every build session itself and tells
   you on Telegram when each milestone ends; you never need to type at the PC again for the build.

## What you will be asked, and where

| When | What | Where |
|---|---|---|
| M0, first minutes | GitHub login for this programme: a link and a code, in the DGIST bot chat without buttons (a new code arrives by itself if you miss it) | phone |
| M0 | Create the programme's own Telegram bot in BotFather (also switch off "join groups"), paste its token into the secret-drop page with the bot's username, tap "Submit new issue"; then, in a second message, open the bot and tap Start | phone |
| M0 | Tap one test button, send one reply and press one old button (proves the bridge works; about a minute) | phone |
| M0 onward | The open questions below, one Telegram question each, each naming the default used until you answer | phone |
| M2 | Create one fine-grained GitHub token per device for the dashboard (a pre-filled link; you pick the one repository) and paste it into the dashboard on that device; set a short PIN | phone and PC |
| M2 | Press Pause and Resume from the phone once (proves the loop; nothing waits on it) | phone |
| M2 onward | Confirm each new dashboard device with one tap (a stolen token alone cannot steer) | phone |
| before the first Stage-4 run | Optional: an OSF preregistration or Zenodo record of the frozen gate (the public timestamp itself is automatic) | phone (optional) |
| M2 end | Pick what Codex builds next: the sandbox (recommended) or the GPU physics track | phone |
| M3 | Open the sandbox viewer once through an SSH tunnel (the exact PowerShell line is in the message; skippable) | PC (optional) |
| M4 | How the GPU is shared with the forge (keep coexisting, yield GPU jobs, or pause everything), with the measured contention | phone |
| M5 | Whether USD 150 a month is this programme's own Vast cap or a budget shared with the forge | phone |
| M6 | Google Drive, as three short messages: create a Google Cloud project (not the forge's) with a published consent screen; create a "TVs and Limited Input devices" client and drop its id and secret; enter a code at google.com/device | phone |
| any time | Vast credit if it runs low; decisions at ladder levels (for example "Start Phase 2?") | phone |

**PC-only, as short as possible:** (1) start the first Codex session (above); (2) optionally, open the sandbox viewer
through an SSH tunnel; (3) a sudo script, only if one becomes necessary (none is expected: the forge already installed
bubblewrap; if a prerequisite such as a browser library is missing, all of them come as one script in M0); (4) the
fallback line, if the secret-drop page ever fails; (5) raising a hard ceiling (Vast spend above USD 150 a month, the
dollars-per-hour limit, the resource ceilings) or opening a gate epoch: one `sprintctl` line over SSH, deliberately
impossible from the dashboard so that a stolen token can neither spend money nor move a band; (6) the Drive fallback,
only if Google's phone flow fails. Everything else reaches your phone when it is needed, including starting a Codex
session after the build ("Start a build session" on an error message) and uploading a paywalled PDF (through GitHub
on the phone).

## Defaults I chose for you (all are settings or edits in `parts/`; change any of them)

| Placeholder / decision | Default | Why |
|---|---|---|
| Control plane | **A separate sibling system** (`smat-sprint`, repo `mushfique-dgist/smat-sprint-lab`, units `smatsprint-*`, Vast labels `smatsprint-prod-…` and `smatsprint-reh-…`, Drive folder `SMATSPRINT-archives/`, config `~/.config/smatsprint/`, live state in `~/smatsprint-home/`, ports 8800–8809), not a second project inside the forge | The forge is being built right now by another Codex task (it is in its M1, with no dashboard yet); coupling two moving builds risks breaking both. Proven forge code is copied with attribution, not imported. The host view shows both programmes' CPU, RAM, GPU and disk; each programme adjusts only its own. |
| `<<TELEGRAM>>` | **A separate bot for this programme** | Checked 2026-09-23: the DGIST bot is long-polled by `dgist-course-telegram`, and a second poller on the same token gets `409 Conflict`. The DGIST bot only sends the first messages (and is the fallback if the new bot's token is ever revoked). |
| `<<PHONE-ON-TAILNET>>` | **No** (the design does not depend on it) | You wrote yes, but the lab tailnet's peers on 2026-09-23 are `sail-gpu01`, your PC, a `macbook-air` and `magzhan-windows`: no phone. The secret drop uses GitHub instead. If you add the phone, one setting enables a one-shot Tailscale page as a second route. |
| `<<CPU-RAM-GPU-SPLIT>>` | Yours: experiment ≤ 48 threads and 12 GB; sandbox ≤ 16 threads, 6 GB and 4 GB VRAM; build sessions ≤ 8 threads and 6 GB; GPU shared (an experiment GPU-memory ceiling is available) | Static caps of the two programmes exceed 30 GB together, so admission by available memory (6 GB always left free, a reserve kept for the forge, jobs that die first under memory pressure) is what actually coordinates them. You set this programme's ceilings; the forge's stay in the forge. |
| `<<SANDBOX-IDLE-STOP>>` | 2 hours | Yours. |
| `<<LLM-USE>>` | Plain-language summaries of finished runs, **at most 3 per day**, read-only; 0 is one tap away | Your section 8 wrote this; section 11 said "default none". Tell me if you meant none. |
| `<<AFTER-GATE>>` | Park the GPU and alert you | Yours. |
| `<<VENUE>>` | **IEEE RA-L, then presented at IROS 2027 by transfer**; T-MRB for a longer version; Science Robotics only for a sprint (L5) result | Checked 2026-09-23: there is no RA-L-with-IROS-option track any more; RA-L papers accepted 2026-08-01 to 2027-04-30 can be presented at IROS 2027. IROS 2027 is confirmed for Florence, 26 Sep–1 Oct 2027; the 2027-03-01 deadline so far appears only on the IEEE RAS calendar. |
| `<<PHASE-2-START>>` | **Wait for your go** (a Telegram button at L3, at a mechanism result, or when the seeds reach five) | Nothing launches research on its own. Your go also starts the Codex build of the sprint part (M8) through the wrapper; nothing to do at the PC. |
| `<<AUTHOR-CONTACT>>` | Unknown; the exact-replay mode is built as a dormant, separately labelled mode, so either answer works | If you email the SMAT authors and they send materials, nothing needs redesigning. The programme itself never emails anyone. |
| `<<SCONE-LICENCE>>` | Not confirmed; no SCONE/Hyfydy work | Ryu's trial licence expires 2026-09-25 and is not ours. |
| `<<DRIVE-QUOTA>>` | Unknown; **lean** archives (well under 5 GB here, because the networks are small) | A free account has 15 GB, shared with the forge's archives if both use it. |
| `<<SERVER-RULES-EXTRA>>` | None beyond the prompt | Tell me if there is anything else. |
| `<<REPORT-TEMPLATE>>` | The KB's weekly-note format and status vocabulary (the first note goes out the Monday after the experiment starts); the venue's official IEEE class for the paper | None was supplied. |
| Disk | Project cap 30 GB. A job, download or archive starts only if it leaves at least **63 GB** free on the shared disk (the forge's 60 GB floor plus 3 GB), counting what running jobs will still write. Below 55 GB the programme checkpoints and pauses, and resumes by itself once 60 GB have been free for 30 minutes. | 80 GB were free on 2026-09-23 (91 % used). This programme never pushes the disk below the forge's floor. (Changed after review: a fixed 65 GB gate would have stalled it whenever the forge sat between 60 and 65 GB.) If the install leaves less than 75 GB free, you get one question about freeing space (question 5). |
| Builder mode | **1: full access inside the build jail** (set in your first message) | Verified against Codex 0.153.4 and its source: no Codex mode lets an unattended session install, push and start GPU work while keeping your other secrets out of the model's reach, and Codex's own sandbox can read every file of your account. So the programme puts each unattended session in its own jail (bubblewrap, as the forge's jailed CUDA probe proved) that hides the forge's, the DGIST agents' and the Vast credentials, with a small launcher outside it for installs, pushes and GPU jobs. Option 2 (auto-review, no jail) is more fragile and less contained; option 0 (a dedicated Unix user) is strongest but needs one sudo script at the PC. |
| Seeds | ≥ 3 independent pipelines for L1–L3; ≥ 5 for superiority claims (L4a, L4c, L5, the paper gate); **≥ 10 for any equivalence claim** ("a simpler controller does the same as SMAT") | Your ladder asked for 3; equivalence tests need more power. Part G holds these numbers; this table only quotes them. |
| Vast money | USD 60 per rental and USD 150 per calendar month, counting **only this programme's** rentals | The "UGRP Exp" account is shared with the forge and other people; at M5 you are asked whether 150 is shared. |

## Corrections to the request, found while doing this

1. **The SMAT "Pearson r > 0.92" is left–right symmetry across all joints**, not a hip correlation with the reference
   (O p5, E p6). The L1 gate uses the paper's definition and adds a reference-plausibility floor, labelled as ours.
2. **The "RMSE < 3.6°" compares Stage 2 with Stage 1**, not with the reference.
3. **The 10.1 % activation reduction is confounded** by the Stage-4 reward change (15× effort weight and a new penalty
   on exactly the four reported muscles). The programme adds the reward-matched zero-torque control (B0) the papers
   lack, and the proper "minus r_exo4" ablation (theirs also skipped Stage 3). Beyond the velocity and phase baselines
   you asked for, it also runs a **published simple controller** (Samsung's delayed output feedback, B6), because
   Exo-Plore (ICLR 2026) already tunes that controller inside a simulated human and a reviewer will ask for it.
4. **MyoAssist's own training code has defects that would silently change the experiment** on the 26-muscle model: the
   target speed is randomised up to 5 m/s even when fixed at 1.25 m/s, resets leave 3D joints dirty, and both actors
   share one exploration-noise vector. The environment is therefore written fresh on MyoAssist's composed model.
5. **MuJoCo Warp does not load the composed model as shipped**; one flag (MULTICCD off) fixes it, and must then apply to
   the CPU runs too.
6. **Your phone is not on the lab tailnet**, and there is no RA-L-with-IROS-option track any more (see the table).
7. **The success bands are fixed now and can never be loosened once a Stage-4 result exists**, so check them before
   sending. L3 is judged on the **pooled mean over independent pipelines**, with a three-way verdict (reproduced, not
   reproduced, inconclusive; more pipelines are added automatically, 3 → 5 → 10, while it is inconclusive): peak
   normalised torque 0.83 ± 0.08; negative-power time ≤ 15 % (you wrote "at most about 10 %"; 15 % still separates
   SMAT from its ablations at 32–40 %); four-group activation reduction 10.1 ± 5 points, each group's pooled reduction
   with a one-sided 95 % lower bound above zero. Per seed there are only catastrophe floors (peak ≥ 0.5, negative
   power ≤ 25 %, falls ≤ 30 %). The six-group 6.1 ± 4 points is reported beside it, not accepted as an alternative pass
   (you wrote "or"). L4 (a): the better method may use up to 5 % more RMS torque and positive work (you wrote "equal
   or lower"). The papers report no seed spread, so the bands come from the published values and the gap to the
   ablations, and evaluation is made precise enough for them. See question 9.
8. **You asked for trajectory parity between GPU and CPU physics.** With contacts it is physically impossible:
   identical worlds diverge within about 75 steps, and CPU MuJoCo itself turns a 1e-7 difference into 4e-3 in 100 steps.
   The GPU backend is certified by contact-free parity, statistical parity of every gated metric and learning parity,
   and every reported number is computed on CPU physics.
9. **The dashboard downloads small files** (logs, CSVs, curves, clips); for a checkpoint or a rollout the Watch panel
   shows the one PowerShell line that fetches it.
10. **The sandbox can copy anything from the experiment except the held-out evaluation seeds, partner policies and
    replay data**, so testing can never tune on what the gate judges.
11. **Tokens are never pasted into Telegram**, because chats are stored on Telegram's servers (a pasted secret is
    deleted and you are asked to replace it); a secret-drop page encrypts them on your phone instead.

## Questions for you (you asked me to ask)

1. **Builder mode**: keep 1 (full access inside the build jail), or prefer 2 (auto-review, no jail) or 0 (a dedicated
   Unix user, one sudo script)? Change the last line of the first message.
2. **Author contact**: will you email the SMAT authors for code and checkpoints? The exact-replay mode is ready either
   way.
3. **Drive quota**: how much Google Drive space do you have (a DGIST Workspace account may have more than 15 GB), and
   which Google account should hold the archives?
4. **LLM summaries**: keep at most 3 a day, or none?
5. **Disk**: the old `ugrp-neurips-2027` project uses 47 GB of the shared disk (its `runs/` holds most of it). Freeing
   part of it would give both programmes room. Nothing will touch it unless you say so.
6. **Anything the programme must never do on the shared server** beyond what is written?
7. **Phase 2 start**: wait for your go (default), or start automatically after L3 or L4?
8. **Report template**: is there a lab or UGRP template for the weekly note or the manuscript?
9. **Success bands** (correction 7): should the six-group 6.1 % count as an alternative L3 pass, as your request
   said? Should L4 (a) require torque that is not higher at all? Answer before M1a freezes the gate (in the first days);
   after that a change needs one `sprintctl gate-change` line over SSH, and none is possible once any result on that
   metric exists.
10. **Vast budget**: is USD 150 a month this programme's own cap, or one budget shared with the forge?

You can answer here (tell Claude, or edit this file before sending), or later on your phone: each open question
arrives as one Telegram question during M0, naming the default used until you answer.

## What was verified, and what was not

- **Verified live on 2026-09-23:** the server (host, 5090 idle, 128 threads, 30 GB RAM, 80 GB free disk, systemd 255,
  delegated `cpu memory pids`, lingering, system-wide systemd-oomd active, tool versions, free ports), the forge's
  running units, its `gh` session location and its handoff folder, the DGIST bot's poller, the tailnet peers, the
  repository name, and the Codex thread `01a09685…` of 2026-09-13 (on the PC: it ended with the reproduction audit and
  "No physics or training was started").
- **Measured on the server by a bounded probe** (about 169 s of GPU time; only same-account forge jobs on the GPU;
  its scratch directory was removed afterwards and nothing else was written): the composed model's structure, CPU and
  GPU throughput, memory per process, MuJoCo Warp support and parity (`research-data/probe/`). The probe composed the
  free-root model; the programme composes the planar-root one and re-measures in its first calibration block.
- **Read page by page:** both SMAT papers (`smat_spec.json`), and the other cornerstone papers listed in
  `03_PAPER_DIGESTS.md`; MyoAssist's code at `b1baf69` read on the server (read-only).
- **Checked against primary documentation:** Telegram Bot API behaviour, GitHub device flow and `gh` storage, the
  fine-grained token link, Pages visibility, Google's device-flow scopes and publishing rules, rclone's client
  retirement, Codex exec modes and sandbox limits (from the installed CLI and its source), Vast CLI fields, IROS 2027.
- **Novelty check (2026-09-23, `research-data/direction-check/scoop_checks.json`):** no paper compares a learned hip-exo
  policy with matched simple controllers in simulation, and no simulation of any device reducing sprint time was found
  (both open). The GPU benchmark and partner-transfer directions are narrowed (MyoAssist 1.0, an unpublished staged
  MJX repository, and Assistax), so Part B.9 states what each claim must rest on. One threat was built in: a hip-flexion
  sprint gain could be patching the model's hip-flexor weakness, so Phase 2 reports a diagnostic human with that limit
  relaxed.
- **Adversarial review of the prompt (six lenses, including an attack on lane isolation and an attack on the Telegram
  bridge):** 168 findings, 29 of them critical; 163 were applied and 5 partly (each with the reason), none ignored.
  A final read of the whole edited prompt found 40 cross-part inconsistencies (5 blockers, mostly steps the locked-down
  build sessions could no longer perform); all 40 were fixed.
  The biggest changes: unattended Codex sessions now run in a jail that hides your other secrets; the Telegram bridge
  runs from the first hour, so the build never waits for you at the PC; the sandbox jail has its own process and
  network namespaces; Promote needs your confirmation; the reproduction verdict is three-way (reproduced, not
  reproduced, inconclusive) on pooled means, because the earlier per-seed rule failed faithful reproductions most of the
  time; the controls are matched in reward, stages, budget and delivered work. Details: `research-data/prompt-review/`
  (`APPLIED.md` lists every finding and what happened to it).
- **Not verified, and said so in the prompt:** whether rclone can refresh a token issued to a "TVs and Limited Input"
  client (M6 tests it live), whether Codex's forbidden-command rules apply in bypass mode (M0's canary tests it),
  exact Vast image tags and offer fields at rental time, the IROS 2027 deadline's time zone.
- **Known limits of the research:** digests and paper entries were written by agents from the sources and every
  number carries its location, but numbers should be re-checked against the source before they are cited publicly.
  The field moves fast (UniExo appeared six days ago), so the runner re-queries arXiv monthly.

## Things I noticed on the server (not part of this programme; nothing was touched)

- The old UGRP project's `ugrp-dashboard-forward-51081547.service` is in an auto-restart loop (it forwards to a Vast
  instance that no longer exists).
- The shared disk is 91 % used.
- **Two gaps in the forge's own design** turned up while reviewing the parts copied from it (reported only; the forge
  was not touched). (1) Its emergency stop kills the worker unit but not the job scopes the worker starts, so jobs can
  keep running; a crashed-and-restarted worker can also start a second copy of a job over the same run directory.
  (2) Its epoch-fencing rule ("ignore anything with an older epoch") can drop legitimate checkpoints of paused jobs and
  leave a finished job neither recorded nor re-deliverable. Worth telling the forge's Codex task.
