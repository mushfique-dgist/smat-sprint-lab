## PART H — Human in the loop: two lanes, steering, the sandbox, and the hop-in/hop-out guide

### H.1 The design in one paragraph

The user is the human in the loop without sitting in it. Experiments run unattended for days as a queue in the
**experiment lane**, the only thing that produces results. The user decides what goes into that queue and in what
order, hops in whenever they like to watch and steer, and tests ideas in a **sandbox lane** that cannot change the
experiment. The only bridge from sandbox to experiment is **Promote**, which copies a config (never a checkpoint,
never a result) into the experiment lane as a new pre-registered candidate that then trains from scratch under the
same rules as everything else. **Steering changes what runs next; it never changes what already ran, or how
results are judged.** The system protects the results from the user in the same way the forge protects them from
its loop, and it says so in plain words when someone tries.

This is the feature the user will use most. It is built in M3 (Part E.4), but its invariants shape M1: the
experiment lane is laid out, hashed and audited from the first job so that the sandbox can later be added without
touching it.

### H.2 The two lanes

| | EXPERIMENT lane | SANDBOX lane |
|---|---|---|
| Purpose | the only source of results | the user's testing and tweaking |
| Label and colour | `EXPERIMENT`, deep blue `#1E4FD8`, a filled-circle icon | `SANDBOX`, amber `#B45309`, a dashed-square icon |
| Root | `/home/aurnab/projects/smat-sprint/` (code, record and work state, Part C.2) | `/home/aurnab/projects/smat-sprint-sandbox/` (a separate tree) |
| Processes | runner, controller, worker and its jobs: systemd user units | the sandbox viewer, sandbox runs, the sandbox shell: transient units in the sandbox slice, each inside the sandbox jail (H.4) |
| Resource slice | `smatsprint-exp.slice` (default `CPUQuota=4800%`, `MemoryMax=12G`) | `smatsprint-sbx.slice` (default `CPUQuota=1600%`, `MemoryMax=6G`, VRAM cap 4 GB) |
| Environment | the pinned venv of the released code (Part C.2) | its own venv built from the same lock, its own caches |
| Ports | none (the dashboard is GitHub Pages) | the viewer on `127.0.0.1:8801` (H.7), token-protected |
| May write | its own record and work state, through the runner and the worker only | only its own tree |
| May read | its own tree | its own tree, plus read-only copies it asked for (H.7) |
| Crosses to the other lane | nothing | one config, through Promote (H.8) |

Colours are never the only signal: every place that shows a lane also shows its word and its icon. The default
resource split is the user's (`<<CPU-RAM-GPU-SPLIT>>` in the request, confirmed in `00_README.md`) and is adjustable
from the dashboard (Part D.4) within the host limits of Part A.5.

### H.3 The lane name is printed everywhere

- **Dashboard:** a full-width lane banner on every page and panel header (`EXPERIMENT` or `SANDBOX`, colour, icon);
  every control on the experiment side carries the chip "changes the experiment" and asks for a one-line reason;
  every control on the sandbox side carries the chip "testing only, cannot change the experiment" and asks for
  nothing.
- **Terminals:** `sprintctl sbx shell` opens the sandbox shell with a prompt `[SANDBOX] aurnab@sail-gpu01:…$` in
  amber and prints a banner: "SANDBOX. Nothing you do here can change the experiment. Promote is the only way to
  send a config to the experiment." Every `sprintctl exp …` command prints a one-line blue banner
  "EXPERIMENT — this command changes the experiment; it is logged with your reason." Read-only experiment commands
  (`status`, `attach`, `ls`) print "EXPERIMENT (read-only)".
- **Logs:** every log line starts with `[EXP]` or `[SBX]`; journald identifiers are `smatsprint-exp-*` or
  `smatsprint-sbx-*`.
- **Files and artefacts:** sandbox files start with `sbx_`; every artefact (checkpoint manifest, result, clip,
  config) carries `"lane": "EXPERIMENT" | "SANDBOX"` in its metadata; clips carry a burned-in corner label with the
  lane word; sandbox configs carry `lane: SANDBOX` and are refused by every experiment entry point except Promote,
  which rewrites it (H.8).
- **Telegram:** messages about the sandbox start `[SANDBOX]`; messages about runs start `[EXPERIMENT]`.

### H.4 How the separation is enforced

Both lanes run as the same Unix user (`aurnab`), so Unix permissions alone cannot separate them. The enforcement is
therefore in layers, each tested (H.11):

1. **The sandbox jail.** Every sandbox process (viewer, sandbox run, sandbox shell, sandbox render, sandbox copy)
   starts through `smatsprint/lanes/jail.py`, a `bwrap` jail (bubblewrap is installed and was proven with CUDA by
   the forge build): `--ro-bind` for `/usr`, `/etc`, `/lib*`, the sandbox venv, and the `copies/` it asked for;
   `--bind` read-write only for the sandbox tree; **no bind at all** for the experiment tree's `state/`, `queue/`,
   `ledger/`, `record/`, `work/`, `gate/`, `eval/`, `configs/registered/`, the command queue directory, the git
   directory, `~/.config/smatsprint/`, `~/.ssh`, `~/.codex`, `~/.config/gh` and every other project; `--tmpfs $HOME`;
   `--dev-bind /dev/nvidia*`; `--die-with-parent`; `--new-session`. The viewer keeps the host network namespace
   because it listens on `127.0.0.1:8801`; sandbox runs and renders use `--unshare-net`.
2. **Read-only experiment files.** After the runner writes a registered config, a result, a record or a checkpoint
   manifest, it removes write permission (`chmod a-w`); only the runner and worker re-grant it for the one write
   they own. This stops accidents (an editor save), not a determined same-user process; layers 3 and 4 catch those.
3. **Hashes checked at every start.** A job refuses to start unless its config file, its code tree (`code_id`), the
   eval tree (`EVAL_HASH`), the gate (`GATE_HASH`) and its parent checkpoint all hash to the values recorded when
   the candidate was registered (Part C.3). The ledger and the steering log are hash-chained (each row carries the
   previous row's hash); the runner verifies the chain at start and every 10 minutes.
4. **Out-of-band edit detection.** A watcher (inotify on the experiment tree, plus a periodic hash sweep) attributes
   every write to a PID and its cgroup. A write from outside `smatsprint-exp.slice` and `smatsprint-ctl.slice`
   raises, within 60 s: the dashboard flag **"experiment lane modified outside the steering API"** (with the path,
   the time and the process name), an alert, and a refusal of every job whose inputs changed. The runner never
   "repairs" such an edit; the user sees it and decides (restore from the ledger's recorded version, or register the
   change properly).
5. **Separate caches and environments.** The sandbox has its own `XDG_CACHE_HOME`, `TMPDIR`, Warp/Triton/Torch
   Inductor caches and `__pycache__`; nothing compiled in the sandbox is ever loaded by an experiment job.
6. **Resource fences.** Slices enforce CPU and memory. GPU memory is capped in-process (the sandbox API computes the
   largest number of parallel worlds that fits the VRAM cap from the measured bytes per world, and sets PyTorch's
   per-process memory fraction), and an NVML watchdog (every 5 s) stops any sandbox process whose GPU memory exceeds
   the cap for more than 10 s. An experiment job that runs out of GPU memory while a sandbox process grew is
   re-queued without a strike and the event is logged as sandbox interference.
7. **No steering from inside the sandbox.** The jail cannot reach the local command queue, the `control` branch
   credentials, the bridge's state, or any secret. The only thing the sandbox can emit toward the experiment is a
   promotion request file in its own `promote_outbox/`, which the runner reads and validates (H.8).

The user's own SSH shell is outside the jail and can, like any shell, edit anything its user owns. The guide
(H.10) says to use `sprintctl sbx shell` for testing, and layers 2 to 4 make any edit from a plain shell visible and
harmless to results: the affected jobs refuse to run and the dashboard says why.

### H.5 The steering API (the only way the experiment changes)

One module, `runner/steer.py`, serves the dashboard (through the command channel of Part D.3), the CLI
(`sprintctl exp …` over SSH) and the Telegram subset (`/pause`, `/resume`, Part N.5). Every call is validated
against a strict schema, carries a **reason** (1–200 characters, required; the Telegram pause and resume default to
"sent from Telegram"), carries `based_on` (the `state_version` the sender saw, Part D.3), and is appended to
`ledger/steering.jsonl` (hash-chained) as `{action_id, action, args, reason, source, based_on, before, after,
outcome, at}`, and shown in the Ledger panel. The runner is the only writer.

| Action | CLI (over SSH) | What changes |
|---|---|---|
| Reorder the queue | `sprintctl exp queue move <cand> --top` · `--before <cand>` | the order in which queued candidates start |
| Pause / resume a candidate | `sprintctl exp cand pause <cand>` · `resume` | whether its next job may start; a running job checkpoints and stops |
| Kill a candidate | `sprintctl exp cand kill <cand>` | its running job stops; its rows stay, marked `killed` with the reason |
| Requeue a candidate | `sprintctl exp cand requeue <cand>` | a killed or failed candidate re-enters the queue, same version |
| Edit a candidate for its next run | `sprintctl exp cand edit <cand> --set key=value …` | creates version v+1 with a new config hash, registered now; earlier versions and their runs stay |
| Add seeds | `sprintctl exp cand seeds <cand> --add N` | queues N more seeds from the pre-drawn training-seed pool (Part C.10); see the rule below |
| Change a budget | `sprintctl exp cand budget <cand> --stage S1 --transitions 320M` | the budget of stages not yet started; a changed budget is a new version |
| Add a catalogue candidate | `sprintctl exp cand new --from <catalogue entry>` | registers and queues a pre-written config (Part B.7) |
| Launch a sweep | `sprintctl exp sweep launch --space <choices> --method grid|random|evolutionary --n N --budget <B> --tiers P1,P3 --rule <rule id> --seeds K` | registers the sweep with its declared selection rule and budget before its first job (Part C.7) |
| Stop a sweep | `sprintctl exp sweep stop <sweep>` | no new members start; finished members stay |
| Change the lane split | `sprintctl host split --exp-threads 48 --exp-ram 12 --sbx-threads 16 --sbx-ram 6 --sbx-vram 4` | slice properties and the packer's limits, within the host ceilings of Part A.5 |
| Settings | `sprintctl settings set <key> <value>` | the Part D.4 settings (polite mode, disk, and so on) |
| Pause, Resume, moves, Drive actions | `sprintctl pause`, `resume`, `move vast`, `move lab`, `backup drive`, … | Part D.2 transitions |
| Promote (from the sandbox) | `sprintctl sbx promote <sbx config> --reason "…"` | registers a new experiment candidate (H.8) |

**What steering can never do** (the API has no such operation, and a test tries each): change `eval/` or `gate/`;
relax a tolerance, before or after a result exists; delete or hide a run, a candidate, a sweep, a steering action
or a ledger row; edit a running job; edit a registered config in place (edits create a new version); change a
sweep's selection rule, budget or seed set after its first job has started (stop it and launch a new one); move a
checkpoint, result or cache from the sandbox into the experiment; start anything in the experiment lane that is not
a registered candidate.

**Seeds added after results exist.** Adding seeds is allowed at any time, but seeds added after a candidate's first
result are recorded as `seeds_added_post_hoc` with the steering action id. The gate (Part G) judges a claim on the
seed list fixed when the claim was registered; post-hoc seeds are reported beside it and never replace a seed or
decide a gate. This lets the user look closer without enabling optional stopping.

**Results carry their history.** Every result row stores the ids of the steering actions that touched its
candidate or sweep before its job started, whether its config came through Promote, and the candidate version.
The weekly note and the paper package list them (Part D.9).

### H.6 Watching (no effect on anything)

The Watch panel (Part D.4) and read-only CLI commands show:

- what is running where (lab or Vast), which candidate, stage, seed and version, progress and a measured ETA;
- a plain-language status line per running job and for the programme as a whole;
- learning curves per stage (return, each reward term, episode length, fall rate, KL, entropy), drawn from the
  downsampled `live.jsonl` series;
- **the live reproduction table**: every published simulated number of Part G.3 beside ours, with our interval,
  the pre-registered band, and the status word (Part G.2);
- each candidate's position on the ladder L0–L5, with the missing evidence in plain words;
- short rendered clips of the currently running policy and of the current best per stage, rendered off-screen on a
  schedule (Part C.12), each labelled with its lane, candidate, stage, seed and checkpoint;
- the plain-language reason a candidate was killed or failed;
- per-seed tables for every candidate, logs, and downloads of small artefacts (logs, CSVs, curves).

Over SSH: `sprintctl status` (the dashboard banner as text), `sprintctl exp ls` (candidates and their states),
`sprintctl exp show <cand>`, and `sprintctl exp attach <job>`, a read-only follow of the job's log (Ctrl-C detaches;
the job is unaffected). None of these can change anything.

### H.7 The sandbox

Ready on day one: at the end of M3 the build copies into the sandbox the catalogue's baseline configs (the SMAT
four-stage default, the matched velocity-proportional controller, the matched phase profile, the Stage-1
reconstruction default), one Stage-2 and one Stage-4 checkpoint from the first campaign runs (or clearly labelled
smoke checkpoints if none exist yet), and a `README_SANDBOX.md`. The user's first hop-in needs no setup.

What the user can do there (each command runs inside the jail and prints the SANDBOX banner):

- `sprintctl sbx copy-in config <exp candidate>[@version]` and `sprintctl sbx copy-in ckpt <exp checkpoint>`:
  read-only copies into `copies/` (copying from the experiment is always allowed and changes nothing there). The
  copy-in allow-list excludes the held-out evaluation assets (held-out human partner policies and the final
  evaluation seed pool, Part G.5), so sandbox tuning cannot touch what the gate evaluates on.
- `sprintctl sbx config new --from <copy or catalogue entry>` and edit the YAML in `configs/` with any editor.
- `sprintctl sbx run <config> --budget 5M` for short trials (sandbox budget and resources; a sandbox run can use the
  same CPU and GPU backends as the experiment, within the sandbox caps; it evaluates on sandbox evaluation seeds,
  which are disjoint from the experiment's).
- **The interactive viewer**: `sprintctl sbx view <checkpoint> --port 8801` starts the viewer and prints a URL with a
  one-time token (`http://127.0.0.1:8801/?t=…`); the viewer binds to 127.0.0.1 only and requires the token on every
  request (other accounts on the machine can reach 127.0.0.1). From the PC (PowerShell 5.1):
  `ssh -N -L 8801:127.0.0.1:8801 sail-gpu`, then open the printed URL. Controls: load any sandbox checkpoint or
  copy; Step, Pause, Run, speed; **change the torque scale live** (a slider; it affects only this rollout);
  exoskeleton on or off; show muscle activations as bars, hip angle, velocity and torque traces; reset to a chosen
  gait phase; render a clip to `clips/`; save the current settings as a new sandbox config. Build it from the
  existing `/home/aurnab/projects/sail-sprint-20260905/reproduction/2026-09-13/viewer/user_controlled_viewer.py`
  as a starting point only (copy it; do not modify the old project), harden it (the token, the jail, the lane
  banner), and add what is missing.
- `sprintctl sbx render <checkpoint> --seconds 10` renders a clip off-screen (EGL) to `clips/`.
- `sprintctl sbx compare <a> <b>` puts two checkpoints or runs side by side: the reproduction metrics of Part G.3,
  their curves, and two clips.
- `sprintctl sbx ls`, `sprintctl sbx stop [<job>]`, `sprintctl sbx clean --older-than 14d`.

**Idle stop.** Sandbox processes report activity (viewer requests, run progress). After `sandbox_idle_stop_h`
(default 2 h) without activity, a sandbox run checkpoints and stops and the viewer exits; the bridge sends
`sandbox_idle_stopped` with a "Restart it" button. The sandbox never runs in the background for days by accident.

**Its own queue.** Sandbox runs have a small queue of their own (default at most 2 concurrent) inside the sandbox
slice; they never enter the experiment queue and never delay an experiment job beyond the resource split.

**The sandbox travels only if ticked.** Moves (Part D.2) carry the experiment lane. The sandbox stays on the lab
unless the user ticks "also move the sandbox" in the move dialog.

### H.8 Promote: the only bridge from sandbox to experiment

`sprintctl sbx promote <sandbox config> --reason "<why>"` (or the Promote button on the Sandbox panel, labelled
"changes the experiment") writes a promotion request into the sandbox's `promote_outbox/`. The runner, outside the
jail, then:

1. validates the config against the experiment config schema: every field must be a registered choice of the
   running code (Part B.3 registry); **any path, any checkpoint reference, any `init_from`, any result reference, any
   sandbox-only component or any unknown key rejects the promotion with the reason in plain words**;
2. rewrites `lane` to `EXPERIMENT`, adds provenance `{promoted_from: <sandbox run or config id>, sandbox_diff: <what
   the user changed relative to the copy it came from>, reason, promoted_at}`;
3. hashes it, registers it as a new candidate (version 1) with the budget rules of Part C.3 and the standard
   pipeline for its kind, and queues it at the bottom of the user's order (the user can move it);
4. logs the steering action with the reason, and replies with the new candidate id.

The candidate then trains from scratch in the experiment lane like everything else. Nothing else crosses in that
direction. **Code** written in the sandbox cannot be promoted: a config that needs new code is rejected with the
message "This config uses code that exists only in the sandbox. New code enters the experiment through a reviewed
build change (Part R.9), then the config can be promoted." Checkpoints and results never cross.

### H.9 Exact replay (only if author materials arrive)

If the SMAT authors send code, models or checkpoints (the user may write to them; Part A.4), the programme runs them
in a separate, labelled mode: `mode: exact_replay`, dashboard label **"EXACT REPLAY (author materials)"**, its own
candidate kind, its own rows, never pooled with independent retraining and never counted toward L1–L4 of the
reconstruction. Build only the label, the schema and the refusal to pool in M1; build the runner for their
materials when they exist.

### H.10 The guide: `docs/HOP_IN_HOP_OUT.md`

Codex writes this guide in M3 for the user, in plain language, with every command in a fenced block tagged `bash`
(runs on the server) or `powershell` (runs on the user's Windows PC, **PowerShell 5.1**: no `&&`, no `||`, no
`2>/dev/null`, sequence with `;` or `if ($?) { }`). It must cover, in this order:

1. **Opening the dashboard** on the PC and on the phone; how to read each panel (Watch, Steer, Sandbox, Ledger,
   Needs, Locations and settings); what the lane banner and the two chips mean.
2. **Hopping in over SSH** (`ssh sail-gpu` from PowerShell) and the read-only commands: `sprintctl status`,
   `sprintctl exp ls`, `sprintctl exp show`, `sprintctl exp attach`.
3. **Steering, action by action** (every row of H.5): the exact command, the dashboard button, what it changes,
   what it cannot change, and an example reason.
4. **The sandbox:** opening a sandbox shell and what the banner means; copying a config or a checkpoint in; running
   a short trial; the interactive viewer through an SSH tunnel (the exact PowerShell line, the URL with its token,
   what each control does); rendering a clip; comparing two candidates.
5. **Promote:** how, what it checks, what happens next, and why code and checkpoints cannot be promoted.
6. **Hopping out:** there is nothing to do. What keeps running (the experiment queue), what stops by itself (sandbox
   jobs after the idle time), and how to check later from the phone.
7. **What can never be done from either lane** (the list at the end of H.5, and why).
8. **Recipes for the typical tweaks:** change a torque scale; change a reward weight; add seeds; swap the reference
   gait; try another observation vector; run the matched velocity-controller baseline; launch a small sweep with a
   declared selection rule; each as sandbox trial → compare → promote.
9. **Telegram from the user's side:** what a need looks like, the buttons, how to answer, `/status`, `/pause`,
   `/resume`, `/needs`, the secret-drop page, and what never happens (no password asks, no secrets in chat).
10. **When something looks wrong:** the "modified outside the steering API" flag; a stale dashboard; a need that
   will not resolve; a sandbox that will not start; a job that refuses to start; with the exact commands to see why
   and who to ask (open a Codex session on the server with `docs/HANDOFF.md` and the message).

**Tested, not trusted.** `tests/guide/test_guide.py` extracts every fenced block. Each `bash` block runs against a
throwaway instance (`SMATSPRINT_HOME` in a temp directory, fake worker and fake backends) and must exit 0 with the
output the guide shows (normalised for times and ids). Each `powershell` block is linted against the PowerShell 5.1
rules above and its `ssh` command line is executed from Linux as the equivalent call. A guide command with no test
fails the suite. The acceptance rehearsal (H.11) then performs every documented action once for real.

### H.11 Lane invariants, the fuzzer and the acceptance rehearsal

Invariants, each with a test that tries to break it:

- **LI1** No sandbox process can create, modify or delete any file under the experiment roots.
- **LI2** Every experiment job's config, code, eval, gate and parent-checkpoint hashes equal the values registered
  for its candidate version; otherwise the job refuses to start and says why.
- **LI3** The ledger and the steering log are append-only with an intact hash chain.
- **LI4** Every result row carries `lane=EXPERIMENT`, its candidate version, its steering refs and its Promote
  provenance.
- **LI5** No experiment job references a sandbox artefact (path or hash) at registration or at start.
- **LI6** Promote transfers exactly one schema-valid config and nothing else; a config with any path, checkpoint,
  result or unknown key is rejected.
- **LI7** From inside the jail, the command queue, the `control` branch credentials, the bridge state and
  `~/.config/smatsprint/` are unreachable.
- **LI8** A sandbox process that exceeds its CPU, RAM or VRAM cap is contained within the watchdog interval; an
  experiment job hurt by it is re-queued without a strike and the event is logged.
- **LI9** Held-out evaluation assets never appear in the sandbox tree.
- **LI10** Any write to the experiment tree from outside the experiment and control slices raises the "modified
  outside the steering API" flag within 60 s and refuses the affected jobs.

**The fuzzer** (`tests/lanes/test_fuzz_isolation.py`, `hypothesis` stateful): while a dummy experiment job runs,
issue random sequences of sandbox commands (copy-ins, runs, viewer actions through its HTTP API, promotions with
valid and invalid configs, shell commands inside the jail that try to write, rename, symlink, hard-link or chmod
experiment files, fill the disk of the sandbox tree, allocate GPU memory past the cap), and after every step assert
LI1–LI10 plus: the experiment's registered hashes, the ledger's chain and row count (except rows the dummy job adds
by itself), and the dummy job's state and trajectory are unchanged.

**The acceptance rehearsal** (end of M3, one detached script, one report `tests/hop_in_out_rehearsal.md`, one
Telegram message): with a real experiment job running, a scripted stand-in for the user performs every action the
guide documents, once: dashboard steering actions through the real command channel, CLI steering over SSH, every
sandbox command, the viewer through its HTTP API, a render, a compare, a successful Promote and three refused ones
(a checkpoint path, sandbox-only code, an unknown key), a `/pause` and `/resume` through the fake Telegram backend.
After each action it verifies that the experiment's hashes, ledger and job state changed exactly as that action
promises and in no other way. The Sandbox panel's buttons are enabled only after this rehearsal passes.
