## PART C — The runner: queue, worker, trainer, evaluation, sweeps, honesty checks, throughput

This part replaces the forge's self-driving loop. Nothing here invents experiments. There is no LLM proposer and
no autonomous director. The **runner** executes the queue the user steers (Part H.5) and the campaign pre-loaded
from Part B.7; it is the sole ledger writer, the gate evaluator and the endpoint for steering commands.

### C.1 Shape of the system

```text
 GitHub private repo smat-sprint-lab  <-- status branch (pushed on change, >= every 120 s) --  CONTROLLER (lab, CPU only)
   main | status | control | gh-pages -->  control branch (dashboard commands, drops)      -->  locations, moves, publish, alerts,
                                                                                               job delivery, record copying
   RUNNER (lab, CPU only): the queue and the ledger. Applies steering (Part H.5), expands candidates into jobs,
   releases the pre-loaded campaign, runs sweeps by their declared rules, harvests records, computes metrics
   through eval/core, evaluates the ladder through gate/check_gate.py, writes cards. Sole writer of ledger/.
        |  queue/outbox/<job_id>.json                                   ^  record/<job_id>/ (results, curves, rollouts, DONE)
        v                                                               |
   WORKER (lab, or a rented Vast host): runs training stages, evaluations, renders, parity and throughput jobs on
   the CPU env pool and, once certified, the GPU physics backend. No credentials, no ledger writes.

   BRIDGE (lab): Telegram needs and commands (Part N).  WRAPPER (lab): Codex build sessions (Part N.8).
   SANDBOX services (lab): the user's testing lane, jailed, separate slice (Part H).
```

- **controller** (`control/controller.py`, unit `smatsprint-controller.service`, enabled, `Restart=always`): as in
  the forge. It never touches the GPU. It polls commands (dashboard `control` branch, `sprintctl`, Telegram through
  the bridge), drives the location state machine of Part D, starts and stops the worker (on the lab only through
  `systemctl --user start|stop smatsprint-worker.service`, after writing and fsyncing `state/desired.json`, Part
  D.5), publishes `status.json`, enforces polite mode, budgets and disk floors, delivers jobs exactly once (Part
  D.1), copies finished jobs' small files into `record/` every 60 s with hash checks, and does finished-run
  retention. It forwards steering commands to the runner's command queue.
- **runner** (`runner/runner.py`, unit `smatsprint-runner.service`, enabled, `Restart=always`, `Nice=10`): runs on
  the lab in every location state, from the service tree (C.2). Single writer of `ledger/`, `queue/outbox/`,
  `configs/registered/` and `baselines/cache/`. Harvests only from `record/`, never from the work tree. Refuses to
  start on a `GATE_HASH` or `EVAL_HASH` mismatch. Keeps the outbox deep enough (default 12 hours of work) that the
  worker never waits for the runner, the lab link or the user.
- **worker** (`runner/worker.py`; on the lab the unit `smatsprint-worker.service`, installed but **never enabled**,
  `Restart=on-failure`, `KillMode=mixed`, started and stopped only by the controller; on Vast a `setsid` process
  group with a supervisor and the guard of Part D.6): owns the experiment lane's CPU env pool and GPU work. Reads
  `state/desired.json` before importing torch and exits 0 without touching the GPU if `run=false` or the epoch is
  not its own. Killable at any instant, resumable from disk. The only writer inside the live `work/`.
- **dashboard** (static files on `gh-pages`, Part D.3–D.4), **bridge** and **wrapper** (Part N), **sandbox**
  (Part H).

Why the brain and the muscle are separate processes on possibly separate machines is unchanged from the forge:
credentials never leave the lab; the record has one writer on one machine; the worker never idles behind the
runner; every connection starts from the lab.

### C.2 Repository layout and the three kinds of tree

```text
smat-sprint/                      (/home/aurnab/projects/smat-sprint; GitHub mushfique-dgist/smat-sprint-lab, private)
  README.md, AGENTS.md (<= 60 lines, E.9), pyproject.toml, uv.lock (Python 3.12; pinned torch, mujoco, myosuite, …)
  smatsprint/          science library: envs/ (the walking and sprint environments, backend-agnostic, C.8),
                       backends/ (native_cpu, warp_gpu after M4), models/ (composed MJCF, device models, actuator
                       models), refs/ (reference-motion loaders), agents/ (actor/critic networks), train/ (PPO, stages,
                       freezing, checkpoint), controllers/ (velocity-proportional, phase profile, fixed sprint profiles),
                       choices/registry.yaml (every unspecified choice and its options, Part B.3)
  eval/                FROZEN evaluation: core/ (gait segmentation, every metric a gate reads, bands are NOT here),
                       protocols/ (walk_eval, sprint_eval, parity, partner_transfer), EVAL_HASH; diagnostics/ additive
  gate/                FROZEN success criteria: criteria.yaml, check_gate.py, GATE_HASH, tests (Part G)
  runner/              runner.py, worker.py, steer.py, candidates.py, pipelines.py, sweeps.py, rules.py (selection-rule
                       library), cards.py, clips.py, ledger.py, summaries.py (optional LLM, C.13), schemas/
  control/             controller.py, state_machine.py, commands.py, locations/{lab,vast,drive}.py, publish.py,
                       alerts.py, guard.py, host.py (the host budget view), sprintctl (CLI)
  bridge/, codexwrap/  Part N
  lanes/               jail.py, watchers (out-of-band edit detection), sandbox API (Part H)
  dashboard/           index.html, app.js, style.css, drop.html, vendor/, explain/ (Part D.4)
  catalogue/           pre-written candidate configs and pipelines (Part B.7), and the campaign plan campaign.yaml
  configs/registered/  RECORD state: every registered candidate version, hashed, read-only (runner-written)
  experiments/         notes only; no code runs from here
  ledger/              runs.jsonl (hash-chained), results.tsv, steering.jsonl (hash-chained), candidates.jsonl,
                       sweeps.jsonl, claims/<claim_id>.yaml, ladder.json, paper_gate.json, epochs.jsonl, killed.md
  docs/                PLAN.md, PROGRESS.md, HANDOFF.md, USER_ACTIONS.md (mirror of open needs), HOP_IN_HOP_OUT.md,
                       REPRO.md, calendar.md, spec/ (this prompt and its companions), weekly/, paper/, papers_pdf/
  ops/                 systemd/*.service|*.slice|*.timer, vast/ (provision.sh, onstart.sh, image.txt, offer_filter.json,
                       worker_guard.py), drive/, root/ (vetted sudo scripts), scripts/ (install.sh, doctor.sh, chaos.sh,
                       detach.sh, notify.sh)
  tests/               unit, integration, crash, chaos, gate, lanes, bridge, guide, dashboard (playwright), migration
  cache/               git-ignored project caches (TMPDIR, UV_CACHE_DIR, XDG_CACHE_HOME, WARP/TRITON/INDUCTOR caches)
  state/  queue/  record/   git-ignored RECORD state, lab only (Part D.1)
  work -> work.d/<gen>/     git-ignored WORK state: runs/<job_id>/{ckpt/,logs/,live.jsonl}, queue/{pending,running,
                            done,failed}/, code/<code_id>/, compile_cache/, refdata/ (reference motions, hashed)
```

Every git-ignored directory is addressed through one absolute `SMATSPRINT_HOME`. The sandbox lives in its own tree
(`/home/aurnab/projects/smat-sprint-sandbox/`, Part H.2).

**Three kinds of tree, never mixed (as in the forge).** The *dev tree* is the project directory on `main`; only a
Codex build session edits it and no service runs from it. The *service tree* is `state/trees/service/`, a
`git worktree` at a release tag `svc-<n>`; controller, runner, bridge and the worker harness run from it; R.9's
drain, tests and `sprintctl release <tag>` move it. *Run trees*: for each job the worker materialises the science
code of the job's commit into `work/code/<code_id>/` (`git archive <sha> smatsprint eval uv.lock`), runs with that
directory as `cwd` and as the only project entry on `PYTHONPATH`, in a venv keyed by the hash of `uv.lock` and built
with `uv sync --frozen --no-install-project`. At start every job asserts that `smatsprint.__file__` and
`eval.__file__` lie under its own run tree. `code_id` is the sha256 of the git tree hashes of `smatsprint/`,
`eval/` and `uv.lock`; job identity uses `code_id`, never the commit sha, so ledger and docs commits never change
it.

### C.3 Candidates, pipelines and jobs (the object model)

- A **candidate** is a registered config plus a pipeline, a seed list and a budget. It is created by the
  pre-loaded campaign (Part B.7), by the user (catalogue entry, edit, Promote, Part H.5 and H.8) or by a sweep
  (C.7). **Registration** writes `configs/registered/<cand>@v<k>.yaml` (read-only), records its sha256, the
  `code_id` it needs, its seeds and budget, its purpose (reproduction arm, baseline arm, ablation arm, sweep
  member, calibration, sprint condition) and, if any, the claim it serves; it appends a row to
  `ledger/candidates.jsonl`. A registered version never changes; an edit is a new version.
- A **pipeline** is a small DAG of stage jobs plus evaluation jobs, written in `catalogue/pipelines/*.yaml`. The
  SMAT pipeline is `S1 → S2 → S3 → S4` with evaluations after S1, S2 and S4; ablation and baseline pipelines branch
  from a registered S2 checkpoint of the same seed (paired design, Part B.6). A candidate may name a **symbolic
  parent** resolved by a declared rule ("the S2 checkpoints of the configuration that sweep X's rule R selects");
  the rule is part of the registration, so the resolution is mechanical.
- **Job kinds:** `stage_train` (a training stage with a parent checkpoint or none), `eval` (Part C.9 protocols on a
  checkpoint with evaluation seeds), `ctrl_tune` (tuning a non-learning controller by a declared grid and rule),
  `render` (clips), `throughput` and `parity` (Part C.11, Part B.5), `calibration` (noise floors and proxy-tier
  calibration, C.7).
- **Job identity** = sha256 of (`code_id`, registered config hash, stage, seed, parent checkpoint hash,
  `EVAL_HASH` for eval jobs, backend id). Re-queuing a finished job returns the stored result; duplicate rows cannot
  enter the ledger.
- **Transitions** are counted in aggregate across all parallel environments (SMAT's "320M" means 320M environment
  steps summed over its 32 environments; the per-environment reading is a registered alternative, Part B.3). Every
  stage records transitions, PPO updates per actor, wall-clock, backend, CPU threads, GPU name, and peak RAM and
  VRAM.
- **Budgets** are in transitions per stage, with a wall-clock estimate shown from measured throughput. A budget
  change is a new version.
- **Seeds.** Training seeds are drawn per candidate from `sha256(candidate_id)` over a universe of 1,000 seeds
  (0–999), with independent pipelines using distinct seeds at every stage. Evaluation seeds come from a disjoint
  pool (10,000–10,999) and sandbox evaluation seeds from another (20,000–20,999). A reserved set of human-partner
  seeds (900–949) trains the held-out human policies of the partner-transfer test (Part G.5) and is never used as a
  co-training partner of any evaluated device actor. `eval/core/seeds.py` owns these pools; a unit test proves they
  are disjoint.

### C.4 The runner loop

```text
RUNNER, every 30 s:
  0. sync      load ledger and state; verify GATE_HASH and EVAL_HASH against the current epochs (refuse on mismatch);
               verify the ledger and steering hash chains (every 10 min); apply queued steering commands through
               runner/steer.py in arrival order (Part H.5), each logged before it takes effect
  1. harvest   for each new record/<job_id>/: check files against the hashes in DONE; for eval jobs compute metrics
               with eval/core from the saved rollouts (never trust numbers computed on the worker); append rows to
               ledger/runs.jsonl and results.tsv with every provenance field of C.10; build the card (C.12);
               re-evaluate the ladder and the claims through gate/check_gate.py (a pure function, Part G.8) and write
               ledger/ladder.json and paper_gate.json; raise ladder_crossed needs when a candidate reaches a new level
  2. plan      expand registered candidates into jobs whose parents exist, in the user's queue order; fill the outbox
               to the target depth; pack by resource class (cpu_env, gpu_backend, cpu_light); release the next block
               of the pre-loaded campaign when the queue runs under target (Part B.7), in the order the user left it;
               advance sweeps by their declared methods and rules (C.7); resolve symbolic parents by their rules
  3. evergreen if nothing is queued for more than 5 minutes: run the pre-planned evergreen generator (below) and
               raise queue_empty once (Part N.10) with the pre-planned options as buttons; never invent a new config
  4. publish   write status inputs; commit ledger/ and docs/ from state/trees/ledger/ on the ledger branch; the
               publisher pushes at most once a minute and at least every 10 minutes (Part R.7)
  5. housekeep rotate logs; report disk against the caps and floors (Part A.5)
```

**The evergreen generator** (deterministic, no LLM, no new configs): the pre-registered top-up seeds of registered
claims (the claim declared them at registration; Part G.5), refreshing baseline arms whose code identity changed,
the periodic evaluation-noise and throughput refresh (C.7, C.11), and clip renders of the current bests. Its options
for the `queue_empty` need are exactly the catalogue blocks not yet released, listed by name, plus "Wait".

### C.5 The worker

```text
WORKER, forever:
  read state/desired.json before importing torch (Part D.5): run=false or a foreign epoch -> exit 0, GPU untouched.
  admit the highest-priority job from work/queue/pending/ whose resources fit: CPU threads within the lane's quota;
  host RAM (MemAvailable minus the job's declared RAM, from the measured per-env RSS of C.11, must stay above 6 GB);
  GPU memory (free minus 10 % of total, re-read before each admission; other processes of the same account, such as
  the forge and llama-swap, are counted as used, never as ours); disk (free space above the floors of Part A.5 and
  3x the job's checkpoint size)
  -> materialise its run tree -> smoke (<= 90 s: build the env, one rollout, one update, checkpoint and resume round
  trip, bit-equal parameters after resume) -> run, checkpointing at every PPO update boundary (network, optimiser,
  normaliser, RNG states, the full simulator state of every environment, episode counters and reference phases),
  keeping the last two -> write results.json, curves.csv and, for eval jobs, rollouts.npz, then an atomic DONE marker
  with the sha256 and size of each file and the worker_epoch -> next job.
  SIGTERM: stop collecting, discard the partial rollout, keep the last update-boundary checkpoint, exit within 45 s.
  On start with run=true, resume every job in work/queue/running/ from its latest verified checkpoint.
```

- Checkpoints are never pickles: tensors in `safetensors`, everything else in JSON (Part D.5); MuJoCo states are
  saved with `mj_getState(…, mjSTATE_INTEGRATION)` as arrays. A resumed CPU run reproduces the uninterrupted run's
  parameters bit for bit on the same machine (tested, Part E.2); a resumed GPU run reproduces it within the
  backend's stated tolerance.
- Retention is the worker's: keep the last two update checkpoints while running; at DONE keep the final checkpoint
  of every stage (they are the parents of later stages and the objects the user replays), delete intermediate ones;
  keep everything for candidates that back a claim at L2 or above. Eval rollouts of candidates below L1 are pruned
  after 14 days (their metrics stay in the ledger). Checkpoints here are small (the networks are a few hundred
  thousand parameters), so the budget is dominated by rollouts and clips.

### C.6 Scheduling

The user's queue order comes first. Within it the runner (a) finishes pipelines already in progress before starting
new candidates at the same position, (b) backfills a smaller job when the head job cannot fit (a GPU job waiting for
memory while CPU cores are free), (c) keeps **paired blocks** together: the arms of one comparison (for example SMAT
S3/S4, the velocity controller and the phase profile branching from the same S2 checkpoint and seed) are released
together so they run on the same code, backend and conditions, and (d) never runs a comparison's arms at unequal
budgets (a budget change to one arm of a paired block is refused unless applied to every arm). There is no hidden
priority system: the dashboard shows the order the runner will follow and why a job is waiting.

### C.7 Sweeps over the unspecified choices, and the proxy tiers

- **The registry.** `smatsprint/choices/registry.yaml` lists every implementation choice the SMAT papers leave
  open (Part B.3), each with an id, its options, the default, the stages it affects and a one-line note. A config
  names a value for each; a sweep space is a subset of choices with a subset of options.
- **Methods.** `grid` (full or declared fractional factorial), `random` (N seeded draws), `evolutionary` (population,
  generations, tournament selection and one-choice mutation over the registry, deterministic given its seed). All
  three are LLM-free. A sweep is launched by the user (Part H.5) or pre-loaded (Part B.7), never by the runner.
- **Registration before the first job:** the space, the method and its parameters, the seeds per member per tier,
  the tiers, the total budget (with the wall-clock estimate), and the **selection rule**, chosen from the fixed
  library in `runner/rules.py` with its parameters, all hashed. Nothing about a sweep can change after its first job
  starts (Part H.5).
- **Tiers.** P0 plumbing (at most 2M transitions), P1 screen (default 40M for Stage-1 work), P2 short (default 120M),
  P3 full (the published stage budget). Successive halving keeps the top third by the declared rule at each tier.
  Members that pass the last tier are re-run on **fresh** seeds at P3 as part of the sweep's own budget before any
  result is called more than "screening" (the winner's curse: the best of many screened configs is biased upward by
  construction).
- **Calibrated tiers, so a sweep does not optimise noise.** Before a sweep's P1 selection is trusted for a stage,
  the **tier calibration** for that stage must exist (it is part of the pre-loaded campaign, Part B.7 Q1): at least 8
  configurations spanning the registry, each at P1 and P3 on 2 seeds; report Spearman ρ between the P1 and P3
  values of the selection metric with a bootstrap 95 % interval, and the top-third recall. Trust P1 when the lower
  bound of ρ exceeds 0.3 and recall is at least 0.6; otherwise the sweep's rule falls back to P2 as its screening
  tier (declared at registration), and the dashboard says why. The **evaluation noise floor** (the same checkpoint
  evaluated with 5 disjoint evaluation-seed sets) is measured for every metric the gate reads; a P1 difference
  smaller than 3 standard errors of that floor plus the seed spread is "too close to call" regardless of sign.
- Sweep members are ordinary candidates (they appear in the queue, the ledger and the Watch panel with their sweep
  id), so every honesty rule applies to them.

### C.8 The environment and the trainer

- **One environment specification, two backends.** `smatsprint/envs/walk26.py` defines the Phase 1 environment
  (the composed `myolegs26` + device MJCF of Part B.2, observations, actions, rewards, resets and terminations as
  registry choices) against a small array interface, so that the native CPU backend (MuJoCo, float64, one process
  per environment, shared-memory batching) and, from M4, the GPU backend (MuJoCo Warp, Part B.5) compute the same
  observation and reward functions. MyoAssist supplies the model composition, reference data and cross-checks, not
  the training loop (its SB3 trainer has no staged freezing; Part B.2). The sprint environment follows the same
  pattern in Phase 2.
- **The trainer** is a custom PPO in PyTorch (CleanRL-style, one file per concern) because SMAT needs two actors, a
  shared critic, per-stage freezing and both backends:
  - networks from the registered config (defaults from the SMAT papers: human MLP 256/128 to 26 excitations; exo
    MLP 128/64 with the 18 inputs of Part B.2 to 2 outputs; shared critic 256/128), activation functions, output
    mappings and log-std handling as registry choices;
  - per-stage hyper-parameters from the papers (learning rate 5e-5 in S1 and 3e-5 later, clip 0.15, 2,048-step
    rollouts on 32 environments, minibatch 16,384, 20 epochs, discount 0.99, GAE 0.95, target KL 0.01, gradient norm
    0.5, entropy 0.001 in S1–S2 and 0.003 in S3–S4), with everything the papers leave open taken from the registry;
  - **freezing**: a frozen actor's parameters have `requires_grad=False`, are excluded from the optimiser, and its
    log-probabilities and entropy are excluded from the loss; its weight hash is recorded at the start and end of
    the stage and must be identical (the job fails loudly otherwise); whether a frozen actor samples or acts by its
    mean is a registry choice recorded in every row;
  - stage transitions per the registry (new optimiser per stage by default; critic and observation normaliser
    carried over; normaliser frozen or continued);
  - the reward-to-actor assignment and the critic's target are registry choices (one advantage on the summed reward
    by default; the two-head alternative is registered);
  - logged per update: every reward term, returns, episode lengths, falls, KL, clip fraction, entropy, value loss,
    gradient norms, per-actor update counts.
- **Trainer correctness before science** (Part E.2): PPO on a standard continuous-control task reaches the return
  band of a reference implementation within a fixed budget; the frozen-actor hash test; gradient-routing probes (a
  frozen actor receives no gradient; the exo actor sees only its 18 inputs); masked log-probabilities; checkpoint
  resume equality. A registered **trainer cross-check** (Part B.7 Q1) trains Stage 1 at P1 once with our trainer and
  once with MyoAssist's own trainer on the same composed model, as a sanity comparison, not a gate.

### C.9 Evaluation (eval/core, frozen)

- **All reported metrics are computed on the reference physics:** native MuJoCo in float64 on the CPU, whatever
  backend trained the policy. A GPU-trained policy is therefore evaluated where its numbers mean the same thing as
  every other number, and any float32 backend effect shows up as a difference, not as a changed metric.
- **Walking protocol** (`eval/protocols/walk_eval.py`): deterministic actions (each actor's mean), `E` episodes
  (default 20) of 12 s at the target speed, the first 2 s discarded, evaluation seeds from the evaluation pool,
  device condition as the stage defines it (same device mass in Stage 2 and Stage 4 comparisons); the rollout
  (joint angles and velocities, muscle excitations and activations, actuator forces, exoskeleton commands and
  torques, contact forces, pelvis position and velocity) is saved at the control rate as `rollouts.npz`. Metrics
  are computed from the rollout by `eval/core/` functions with the exact definitions of Part G.3. If the measured
  evaluation noise of a gated metric exceeds a quarter of its band's half-width, the episode count `E` is raised,
  never the band (Part G.4).
- **Sprint protocol** (`eval/protocols/sprint_eval.py`, Phase 2): the common standing start, 200 m of forward
  displacement with the finish interpolated between control steps, the 100 m split and maximum speed; falls,
  timeouts, invalid contacts and numerical failures are failures with no time; completion rate and the time
  distribution are both reported (Part G.6).
- **Other protocols:** `parity` (Part B.5), `partner_transfer` (held-out human policies, Part G.5), `offline_replay`
  (the SMAT offline replay on recorded walking, Part B.6).
- `EVAL_HASH` = sha256 over `eval/core/` and `eval/protocols/`. It is frozen in M1 before the first registered
  result; a change opens an evaluation epoch (logged, alerted, shown permanently) and re-evaluates every stored
  checkpoint that a claim uses under the new epoch before any new comparison. `eval/diagnostics/` is additive and
  never gates.

### C.10 Honesty checks (automatic, every harvest)

- Every result row stores: commit, `code_id`, `EVAL_HASH` and `GATE_HASH` epochs, registered config hash and
  version, stage, seeds (training and evaluation), parent checkpoint hash, backend and its version, physics
  timestep and control rate, muscle count, the composed model's hash, device model and actuator model ids,
  transitions and per-actor updates, wall-clock, CPU threads, GPU name, driver, torch and mujoco versions, peak RAM
  and VRAM, `worker_epoch`, host, lane, steering refs, Promote provenance and `seeds_added_post_hoc` (Part H.5).
- **Seeds:** evaluation never uses a training seed or a sandbox seed; the partner-transfer test never uses a human
  policy that co-trained with the evaluated device actor; a claim is judged only on its registered seed list.
- **Checkpoint selection:** the reported checkpoint of every stage is chosen by the registered rule (default: the
  final checkpoint; the registered alternative: the best exponential moving average of training return), **never by
  the metric being reported**, and never by any evaluation-pool metric.
- **Equal budgets:** arms of a comparison must have equal transitions per stage (and, where the comparison is about
  optimisation effort, equal per-actor updates, reported both ways), equal torque budget (the same stage torque
  scale and command limit; RMS torque and positive work reported beside it), the same code identity and backend
  class. Shared pretraining (S1, S2) is counted in every arm's total cost. An unmatched comparison is labelled
  "not comparable" and never promoted.
- **All failures kept:** a seed that falls, diverges or times out stays in the pooled statistics with its failure
  (Part G.4); nothing is reported on survivors only.
- **Suspicious results:** an activation reduction above 40 %, a negative-power fraction below 1 %, a normalised peak
  above 1.0, or any metric outside the physically possible range flags the row `suspect`; it cannot count toward a
  level until a fresh seed reproduces it and a short clip has been rendered for the user.
- **Physics sanity:** NaN or infinite states, contact penetration beyond a declared depth, muscle forces beyond their
  maximum isometric force times the model's force-length-velocity bound, and implausible ground-reaction impulses
  each abort the job with a labelled failure.
- **Model identity:** a comparison between backends or models is refused unless muscle count, timestep, control rate
  and contact set are equal or the comparison is declared as a parity study (Part B.5).

### C.11 Throughput engineering (the lever)

- **Native CPU first, measured.** In M1 measure, for the composed model: single-environment steps per second,
  control transitions per second at 50 Hz, resident memory per environment process, and aggregate transitions per
  second at 1, 8, 16, 32 and 48 environment processes (Part B.5 records what the handoff's probe measured). The
  worker packs jobs from this table. The paper's 32 environments are the default geometry; more environments per
  job are a registered choice.
- **The GPU backend** (MuJoCo Warp, milestone M4) sits behind the same environment interface and is certified by the
  parity gates of Part B.5 before any experiment job may use it; until then every job runs on the CPU backend. A GPU
  job declares its world count, its rollout geometry and its VRAM; the packer admits it against measured bytes per
  world.
- **Throughput is data.** Every job logs transitions per second, per-actor updates per second, and, on Vast, dollars
  per million transitions. The dashboard shows transitions per day and the forecast time for each queued candidate.
  A change that makes every run twice as fast is worth a milestone.

### C.12 Plain-language cards and clips

- **Cards** (template-built, no LLM), six fields per run and per candidate: *What we ran* (plain words: "the human
  learned to walk with the device on but switched off"), *Why*, *What happened* (one number beside the published
  one, with unit, direction and interval), *What it means*, *How sure we are* (wording from the table of Part G.2),
  *What runs next*. Every number equals the ledger's number; the card validator checks it and enforces the ladder
  words (Part G.2).
- **Clips** (`runner/clips.py`, EGL off-screen, 640×360, 10 s, WebM under 1 MB, lane label burned in): the currently
  running policy of each active candidate every `clip_interval_h` (default 6 h) and at every stage end; the best per
  stage by the declared rule whenever it changes; the ablation arms and baselines side by side at their stage ends.
  Clips are published on the `status` branch for the Watch panel.

### C.13 LLM use inside the programme (optional, bounded, never inventive)

The default, from the user's request, is **plain-language summaries of finished runs only, at most 3 per day**,
settable from 0 to 3 on the dashboard; zero must work, and at zero the template cards stand alone. A summary call
runs on the lab only, through `codex exec` with a read-only profile, no shell, no web, and its inputs on stdin (the
card fields and numbers); the output is at most 120 words, and every number in it must appear in the input or the
summary is discarded. It never proposes a config, never touches a file, never sees a secret. The flags banned for
programme calls: `--dangerously-bypass-approvals-and-sandbox`, `-s danger-full-access`, `--approve-for-me`, and any
network or shell grant; a unit test greps the recorded command lines.

### C.14 After the gate, the weekly note, and the paper package

- **Stop condition.** When a claim passes the paper gate (Part G.7), the runner finalises the paper package from the
  ledger, flips the dashboard to "PAPER GATE PASSED: review needed", sends `paper_gate_decision`, and **parks the GPU
  and alerts** (`<<AFTER-GATE>>` default; `after_gate: park | continue` is a setting). It submits nothing.
- **The weekly research note** (`docs/weekly/<year>-W<week>.md`, assembled from the ledger every Monday 09:00 KST,
  sent as a document on Telegram): what was tried, in the KB's status vocabulary only (proposed, prepared, executed,
  validated, rejected, externally blocked; never "promising"), the reproduction table, ladder movements, failures and
  why, the user's steering decisions of the week with their reasons, resources used, and what is queued next.
- **The paper package** (`docs/paper/`): IEEE conference template (IROS/RA-L, Part G.9), every figure and table
  regenerated from the ledger by script, the steering history and Promote provenance in the reproducibility
  statement, `docs/REPRO.md` with exact commands.
