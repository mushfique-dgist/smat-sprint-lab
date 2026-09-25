# Decisions for applying the adversarial review (2026-09-23)

Every editor of `parts/` uses exactly these names and numbers, so the parts stay consistent. Finding ids refer to
the lens files in this folder (TB = telegram_bridge, IM = implementability, SM = state_machine_coexistence,
UX = fidelity_ux, LI = lane_isolation, RD = research_design). Where a later decision replaced an earlier one, the
later text is the one kept here.

## Paths and trees

- `SMATSPRINT_HOME=/home/aurnab/smatsprint-home` is the **record root**, **outside** the dev tree
  `/home/aurnab/projects/smat-sprint`. It holds `ledger/`, `configs/registered/`, `state/`, `queue/`, `record/` and
  `work.d/` (with the `work` symlink) as plain directories: **record state never lives in a git worktree**, `main` tracks
  no ledger file, and the ledger branch is built from a copy in a bare repository, as the status branch is. The service
  tree (`state/trees/service/`) is a git worktree of code only. Every `state/…`, `queue/…`, `record/…`, `work/…`,
  `ledger/…` and `configs/registered/…` path in the prompt is relative to it. Project caches stay in `<project>/cache/`.
  (TB-07, LI-04)
- The sandbox tree is `/home/aurnab/projects/smatsprint-sbx/` (renamed so no root is a string prefix of another).
  Every containment check resolves both paths and uses `Path.is_relative_to`; a grep test bans `startswith` on path
  strings. (LI-20)
- `ledger/` and the runner-written documents (`docs/generated/weekly/`, `docs/generated/paper/`,
  `docs/generated/REPRO.md`) exist only on the `ledger` branch (built from a copy in a bare repository, never a
  worktree); `docs/` on `main` (PLAN,
  PROGRESS, HANDOFF, USER_ACTIONS, spec/, HOP_IN_HOP_OUT) is written only by Codex sessions. (IM-23)
- The forge's handoff folder (read-only reference for "as in the forge"): `/home/aurnab/projects/ugrp-autoresearch-handoff/`
  (exists, verified 2026-09-23). (IM-30)
- Pinned tool copies: `~/.local/share/smatsprint/bin/{gh,rclone,vastai,uv}`, sha256-checked at start and by the doctor;
  never call `~/.local/bin/{gh,rclone,vastai,uv}` (the forge may upgrade them). (SM-29)

## Slices and units (R.2 is the source of truth)

- `smatsprint.slice` (`MemoryMax=19G`, `MemorySwapMax=0`, `TasksMax=4096`; no `MemoryHigh`, so the sandbox cannot
  throttle the experiment through the parent; LI-14), children:
  - `smatsprint-exp.slice` (`CPUQuota=4800%`, `MemoryMax=12G`): the worker, its job scopes, and
    `smatsprint-exp-build.slice` (child) for detached build jobs marked `--gpu-work` or `--heavy`;
  - `smatsprint-sbx.slice` (`CPUQuota=1600%`, `MemoryMax=6G`, VRAM cap 4 GB);
  - `smatsprint-ctl.slice` (`CPUQuota=400%`, `MemoryMax=2G`, `MemoryLow=768M`): only the controller, runner, bridge,
    wrapper, launcher, lane watcher and watchdog;
  - `smatsprint-bulk.slice` (`CPUQuota=800%`, `MemoryMax=2G`, `Nice=15`, idle I/O): rsync, tar/zstd, rclone, `uv sync`,
    summary calls, as transient units with `--collect`. (SM-21)
- `smatsprint_build.slice`, a **top-level sibling** of `smatsprint.slice` (`CPUQuota=800%`, `MemoryHigh=5G`,
  `MemoryMax=6G`, `MemorySwapMax=0`, `TasksMax=2048`, `OOMScoreAdjust=900`): Codex build sessions and CPU-only detached
  build jobs. (IM-03, SM-21, TB-07)
- New unit: `smatsprint-launcher.service` (ctl slice; named operations only; Part N.8).
- Worker unit: `OOMScoreAdjust=800`, `Nice=10`, `IOSchedulingClass=idle` (job and sandbox scopes inherit); controller,
  bridge and watchdog stay at 0. The forge's worker uses 600. (SM-09)
- systemd-oomd is active system-wide on sail-gpu (checked 2026-09-23); Phase 0 records what it would kill.

## Pause, stop and the GPU-free check

- Job scopes are named `smatsprint-job-<job_id>-<worker INVOCATION_ID>` and created with
  `-p BindsTo=smatsprint-worker.service -p After=smatsprint-worker.service` (verify on systemd 255; if refused, the
  steps below are the guarantee). Every environment process sets `PR_SET_PDEATHSIG=SIGKILL`; every trainer holds an
  exclusive flock on `runs/<job_id>/.lock`; at every start the worker stops scopes whose invocation id is not its own;
  the worker re-reads `desired.json` before every admission and spawn. (SM-01, IM-14)
- **Pause** = write `run=false`, `systemctl --user stop smatsprint-worker.service`, then
  `systemctl --user stop smatsprint-exp.slice`; sandbox runs and renders in `smatsprint-sbx.slice` are stopped too (the
  viewer stays only if `pause_keeps_viewer=true`, default false). **Emergency stop** = write 1 to the exp slice's
  `cgroup.kill`, then stop the slice. **Verified** when `smatsprint-exp.slice/cgroup.events` reads `populated 0` and two
  `nvidia-smi` reads 2 s apart show no GPU PID whose cgroup is under `smatsprint.slice` (except a permitted viewer). At
  55 s without that: `cgroup.kill`. At 75 s still populated: need `pause_not_verified` with the PIDs and an Emergency
  stop button. I6 becomes: "after Pause is acknowledged, `smatsprint-exp.slice` holds no process and no GPU process
  belongs to it". Resume restarts only the experiment. (SM-01, SM-11)
- **Failsafe pause**: `sprintctl pause` and `sprintctl emergency-stop` queue the command; if the controller heartbeat is
  older than 60 s or the command is not received within 30 s, they act directly, write `state/failsafe_pause.json`
  `{at, by, reason}` (written only by this path; the controller turns it into `PAUSED(by: user)` and deletes it once
  recorded; the worker and the Vast supervisor refuse to start while it exists). The watchdog applies the same failsafe
  when the controller has been silent 15 minutes and another account holds GPU memory above the polite threshold or a
  Vast lease reached 100 % of its cap. Telegram `/pause` falls back to it after 60 s without acknowledgement. (SM-12)
- Pause, Stop, Emergency stop, cancel_move, settings, register_device and the automatic polite_pause and lease_cap are
  **never busy-rejected**. (SM-04)
- Commands are ordered by their `created_at`; a Telegram command's `created_at` is the message date. (TB-14)
- The controller fetches the `control` branch every 15 s (`git ls-remote`) and the local queue every 1 s. (SM-24)

## Disk

- Lab admission: start a job, download or archive only if
  `free − Σ(reserved-but-unwritten bytes of running jobs) − the item's declared max_disk_growth ≥ forge_floor_gb (60) +
  margin_gb (3)`. Every lab disk-writing transition (move_to_lab, restore to the lab, come-home, lab_mirror, lab-side
  archive builds) requires `lab_free − bytes_to_write × 1.3 ≥ 63`, checked at start and before each writing step.
  Below `hard_floor_gb` = 55: checkpoint and enter **`PAUSED(by: disk)`**, which clears by itself once free ≥ 60 has
  held for 30 minutes (not SAFE_PAUSE). Checkpoint rotation that does not grow usage is always allowed. Project cap
  30 GB stays. Vast hosts use their own floors: `min_free_gb = max(10, 3 × declared checkpoint-and-rollout size)`,
  `hard_floor_gb = 5`. Phase 0: if free space minus the install estimate is under 75 GB, one decision need quoting
  README question 5. (SM-07, SM-08, IM-19)
- Caches: add `CUDA_CACHE_PATH` and `PYTHONPYCACHEPREFIX` to the project-cache list. The uv wheel cache is shared
  between the lanes as a read-only bind, and every venv is built with `UV_LINK_MODE=copy`; compiled/runtime caches stay
  separate. (SM-29, IM-19, LI-12)
- Lab-side archives and restores stream (`tar | zstd -T8 | split` with a filter running `rclone rcat` per part; restore
  with `rclone cat` per part through `sha256sum` and `zstd -d | tar -x`), writing no scratch parts. (SM-07)

## Memory and GPU coexistence with the forge

- Admission: `MemAvailable − Σ(declared − current RSS of this programme's still-ramping jobs) − forge_reserve −
  new job's declared RAM ≥ 6 GB`, `forge_reserve = min(4 GB, memory.max − memory.current of clforge.slice)` read only
  from its cgroup files; after each admission wait until the job's RSS stays within 10 % for 60 s; after a boot_id
  change, a polite resume or any worker start, the first admission waits a random 2–6 minutes; sandbox trials use the
  same rule; need `memory_starved` after 2 h waiting on memory. (SM-09)
- `same_account_gpu: coexist | yield_gpu_jobs | pause_all` (default coexist; offered at M4 with measured contention);
  setting `exp_vram_cap_gb` (this programme's GPU share, shown beside the forge's live use); no-strike re-queues after a
  coincident OOM back off 5, 10, 20 … minutes, at most 6 per job per day, then need `gpu_contention`. The OOM fallback
  never changes the world count: re-queue unchanged and admit when free GPU memory exceeds the declaration by 20 %; a
  second OOM at that margin is a strike. (SM-10, SM-23)
- Polite mode classifies by **UID**, not service name; on a user override the other accounts' GPU PIDs present at that
  moment go to `state/polite_ignore.json`; after 3 polite pauses in 6 h `polite_resume_min` doubles (cap 60); setting
  `polite_scope: all | gpu_jobs` (default all). (SM-13)

## Seeds, claims, hashes, identity

- Seed pools: training 0–899; partner 900–949 (reserved, never drawn for training); evaluation 10,000–10,999 (claims
  and final reporting only); sandbox 20,000–20,999; **selection 30,000–30,999** (every sweep's selection rule,
  controller tuning grids, the precision-rule noise measurement, the proxy-tier calibration). A unit test proves the
  five pools disjoint. (IM-10, UX-07)
- Seeds per claim: L1–L3 ≥ 3; superiority claims (L4a, L4c, L5, paper gate) ≥ 5; **equivalence and non-inferiority
  claims (L4b, the mechanism path's two one-sided tests, B.5 learning parity) ≥ 10**. Gate numbers live only in Part G;
  the README quotes them and never overrides them. (IM-20)
- The old positive controls P1–P3 are replaced by the **known-answer controls K-exo3, K-exo4, K-effort, K-env and
  K-metric** (Part B.6; RD-14), each with a numeric pass rule; a Stage-1 non-reproduction needs K-env and K-metric, a
  Stage-4 non-reproduction needs all five plus L0–L2. The proxy tiers stay P0–P3; the schedule contrasts stay K1–K3.
  (IM-30, RD-14)
- Claims form **families** (`family_id` from claim type, arm-defining keys, primary metric, comparator); verdicts use
  Holm-adjusted α across a family; a claim is registered before its seeds' first job; claims stay pending until every
  gating arm is complete. `gate-change` refuses any change in either direction once any experiment-lane row or the
  sandbox run index reports the metric; held-out asset definitions are immutable after M1a; a claim's verdict is its
  verdict under the epochs in force at its registration. (RD-02, RD-09, LI-05, LI-10)
- Hash families (final, after FC-02): `gate/core/` (shared code, pools, held-out assets, hardware classes, rules/) plus
  `gate/families/{walk,method,sprint}/`; `GATE_HASH[f]` = sha256(core, families/f); walk = L0–L3, method = L4 and the
  walking paper paths, sprint = L5. `EVAL_HASH` per protocol = sha256(eval/core, eval/protocols/p). A build session
  may only first-freeze a family or protocol with no frozen version (launcher `first_freeze`). Assets enter
  `work/refdata/` only through the `refdata_install` job and are checked against `ledger/refdata.jsonl`. A claim records the hashes it uses. A family is frozen
  before the first result it judges. When an epoch opens, every registered candidate version with no started job is
  re-registered as v+1 under the new epoch automatically (one steering row, `source: epoch`); paired blocks move
  together; started pipelines finish under their own epoch. Code fixes to `gate/` or `eval/` go through
  `sprintctl gate-release <commit> --reason …` or `sprintctl eval-release <commit> --reason …` (SSH only), which open an
  epoch and re-judge affected claims under both epochs. (IM-13, UX-02)
- The evaluation episode count E is computed by a frozen function in `eval/protocols/walk_eval.py` from the latest
  registered noise-floor calibration row and the band half-width in `gate/criteria.yaml`:
  `E = min(200, max(20, ceil(20 · (4 σ̂ / h)²)))`; no hash changes; a claim's E is fixed when the claim is created. (IM-11)
- Hardware class: CPU-physics jobs = (ISA level avx512 or avx2; mujoco, numpy and torch wheel versions; the learner
  GPU's compute capability when `learner_device=cuda`); GPU-backend
  jobs = (compute capability, driver major, warp and mujoco-warp versions). A job whose stages ran on two classes is
  "mixed" and not comparable in any paired block. The GPU certificate names its GPU class. (SM-14)
- `code_id = sha256(tree(smatsprint/), tree(eval/), sha256(uv export --frozen --only-group science --no-hashes))`; the
  science dependency group is fully pinned in M1 (Warp packages included); dev and ops groups hold everything else.
  (IM-12)
- The PPO update runs on the GPU by default (resource class `cpu_env+gpu_learner`, about 1 GB VRAM per job); a 4-thread
  CPU learner is a registered alternative; rows record `learner_device`. (IM-08)

## Milestones

- M0 → **M1a** (start counting runs: pause path first, walk26, trainer, walking eval and gate L0–L3, registration,
  ledger, runner, worker, polite mode; exit: L0 recorded and Q0–Q2 started) → **M1b** (while Q2 runs: S2–S4, the B.6
  controls, the `method` gate family, offline-replay and partner-transfer protocols, the full crash matrix,
  the cold-start drill, the host-fence tests; register Q3–Q7 before the first Q3 S2 job starts) → M2 → M3 → M4 → M5 → M6 →
  M7 → **M8** (Phase 2 build, launched by the wrapper when the user taps "Start Phase 2"; after M7 the wrapper stays
  `ARMED(M8)` instead of DONE). (IM-05, UX-02, UX-03)
- Campaign-start gate (end of M1a): the Unit, Gate and Trainer groups; L0; one real pause/resume cycle with the GPU and
  CPU verified free; one SIGKILL-resume bit-equality check. The full Integration and Crash groups and the cold-start
  drill then run detached in `smatsprint-exp-build.slice` while the campaign runs; any red result → SAFE_PAUSE and
  `unexpected`. (IM-06)
- Trainer correctness task: Gymnasium HalfCheetah-v5, 1 M steps, 3 seeds, band = CleanRL `ppo_continuous_action`'s
  published mean return at 1 M steps minus 2 SD (recorded in `tests/fixtures/ppo_band.json`); gymnasium in the dev
  group. "Network faked down" = the adapters run with `SMATSPRINT_FAULT=offline:60`. (IM-06)
- The out-of-band watcher is built in M3 (with the sandbox); until then the build jail, hash checks at job start and the
  hash chains protect the lane. (IM-05)

## Needs, Telegram, sessions (Part N is the source of truth)

- New need codes: `pause_not_verified`, `memory_starved`, `gpu_contention`, `build_milestone`, `secret_rotation`,
  `telegram_gap`.
- Registered decision buttons (N.10) act as the D.2 or H.5 command they name, with `source: telegram_need`, reason
  `<need title>: <option label>`, `based_on` = the state version when the need was sent (a changed state gets "The
  situation changed; here is the new choice" and a fresh need); every such decision appears in the Ledger panel. (UX-09)
- `quiet_hours` (default 23:00–08:00 KST): non-urgent needs and alerts are held until morning; Pause confirmations,
  money alerts and lab-silent alerts are never held. Detached build jobs that finish OK, restarts caused by a release,
  and L1–L2 crossings go into the daily digest or the next milestone message. (UX-22)
- After DONE the wrapper stays installed; `unexpected`, `build_stuck` and the Phase 2 go carry a button "Start a build
  session", which launches one Codex session (in the build jail) with a fixed prompt built from the need's recorded
  data, never from chat text. (UX-10)
- Dashboard command set adds: `sbx_copy_in`, `sbx_config_new`, `sbx_config_set`, `sbx_run`, `sbx_stop`, `sbx_render`,
  `sbx_compare`, `need_action {need_id, action, nonce}`, `paper_upload`. (UX-05, UX-10)
- `drop` ignores `based_on` and has a 24-hour age limit. (TB-21)

## Vast and Drive

- Labels: production `smatsprint-prod-<lease_id>`, rehearsal `smatsprint-reh-<id>`; each controller acts only on its
  configured prefix; production treats `smatsprint-reh-` as foreign; `sprintctl destroy-labelled` accepts only the
  hard-coded rehearsal prefix and never destroys an instance whose lease shows a worker start. An instance without a
  lease, or a lease without an instance, is reported and never destroyed automatically. (SM-19)
- The monthly Vast cap counts only this programme's spend (lease records labelled `smatsprint-`, UTC calendar month); an
  M5 need asks the user once whether USD 150 is this programme's own cap or a budget shared with the forge. Credit
  precondition: `credit ≥ credit_floor_usd (default 20) + max_usd of the new lease + parked storage`, re-read right
  before the create call. The controller's lease_cap trigger is `cost_so_far + dph × estimated_sync_hours ≥ 0.9 ×
  max_usd`; the guard stops at 100 % of a lower-bound cost and never destroys. (SM-05, SM-17)
- This programme's Google Cloud project is separate from the forge's; a lean `backup_to_drive` runs daily at 04:00 KST
  when Drive has room; never prune an archive holding a file whose lab copy an evacuation deleted and that no newer
  verified archive holds. (SM-18)
