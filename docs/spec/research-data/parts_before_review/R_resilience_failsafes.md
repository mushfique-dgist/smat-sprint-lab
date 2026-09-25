## PART R — Resilience: failsafes, retries and degraded modes (the runner does not stop)

Adapted from the forge's Part R with the names of this programme; the principles are unchanged.

### R.1 Principles

- **Fail the job, never the runner.** No single experiment, render, check, API outage or bug may halt the queue. The
  worst outcome of any failure is a labelled row in the ledger and the next job starting.
- **Everything restarts by itself**, in the right order, after a crash, a kill or a reboot.
- **Every external dependency has a fallback**, and the dashboard says which fallback is in use.
- **Every retry is bounded and backs off; every give-up is visible.** If something is abandoned, the ledger, the
  dashboard and (when it matters) a need or an alert say so.
- **Nothing valuable is deleted by a recovery path.** Recovery may stop, retry, roll back or quarantine. It never
  deletes results, ledger rows or the only copy of anything.

### R.2 Process supervision

- **Lab units** (all user units, all in `smatsprint.slice` or its children):

  | Unit | Slice | Enabled | Restart |
  |---|---|---|---|
  | `smatsprint-controller.service` | `smatsprint-ctl.slice` | yes | always |
  | `smatsprint-runner.service` | `smatsprint-ctl.slice` | yes | always |
  | `smatsprint-bridge.service` | `smatsprint-ctl.slice` | yes | always |
  | `smatsprint-codexwrap.service` | `smatsprint-ctl.slice` | yes | always |
  | `smatsprint-worker.service` | `smatsprint-exp.slice` | **no** (started only by the controller) | on-failure |
  | `smatsprint-watchdog.timer` (+ `.service`) | `smatsprint-ctl.slice` | yes | — |
  | sandbox transient units `smatsprint-sbx-*` | `smatsprint-sbx.slice` | no | never (idle stop, Part H.7) |

- Unit skeleton, exactly as the forge proved it on this machine: `StartLimitIntervalSec=0` in `[Unit]` (under
  `[Service]` it is ignored); `Type=exec`; `RestartSec=10`; `WatchdogSec=300`; the worker adds `KillMode=mixed` and
  `TimeoutStopSec=50`; absolute paths in `ExecStart=` (`~/.local/bin` is not on a unit's PATH);
  `WantedBy=default.target` only for the enabled units; no `After=network-online.target` (a user unit cannot order
  itself against system units, and with lingering the user manager may start before the network: every service
  must start cleanly with no network, treating "GitHub, Telegram or Vast unreachable" as *unknown*, never as
  "absent"). `UMask=0077` everywhere. Lingering is on (verified 2026-09-23); verify it again in Phase 0. The test
  suite runs `systemd-analyze --user verify` over every unit and fails on any warning.
- **Watchdog heartbeats.** Each main loop writes `WATCHDOG=1` to `$NOTIFY_SOCKET` itself once per iteration with the
  standard `socket` module (an abstract socket path starts with `@`, replaced by a NUL byte); do not spawn
  `systemd-notify`. **No loop body may block**: every long operation (rsync, `tar | rclone`, `uv sync`,
  provisioning, `codex exec`, `git push`, `systemctl --user stop`, Vast calls, checks, renders) is a child process
  polled later; every short subprocess has a timeout of at most 60 s. Call `faulthandler.enable()` at start so a
  watchdog SIGABRT dumps every thread's stack into the journal. Strip `NOTIFY_SOCKET` and watchdog variables from
  every child's environment (the forge found children otherwise impersonate the parent).
- **The worker unit is different.** It has no `[Install]` section, so it is never enabled and a reboot cannot start
  it. `Restart=on-failure`: a crash, SIGKILL, OOM kill or watchdog SIGABRT is restarted, while a clean exit or a
  SIGTERM death is not. Only the controller starts and stops it (`systemctl --user start|stop --no-block`, then
  polled with `is-active`). systemd does not restart a unit it was asked to stop, so the supervisor cannot undo a
  Pause. Never send a raw signal to the worker's process group on the lab.
  - **Desired state is read before every start.** The controller writes and fsyncs
    `state/desired.json = {run: bool, epoch: int}` next to the live work state (over SSH on Vast) before it signals
    anything (Part D.5). The worker entry point, the Vast supervisor and the guard read it before every start and
    before importing torch or touching CUDA; `run=false` or a foreign epoch means exit 0 without touching the GPU.
  - **Pause on the lab** = write the new phase and `run=false`, then `systemctl --user stop
    smatsprint-worker.service`. With `KillMode=mixed` the main worker process forwards SIGTERM to every packed job,
    each job keeps its last update-boundary checkpoint (Part C.5) and exits; anything still alive at
    `TimeoutStopSec=50` is killed and resumes from its last checkpoint. The GPU-free check snapshots every PID in
    `smatsprint-exp.slice` (packed jobs run in transient scopes there) and confirms none is in
    `nvidia-smi --query-compute-apps`. Emergency stop is `systemctl --user kill --signal=SIGKILL
    smatsprint-worker.service` followed by `systemctl --user stop`, which cancels any pending restart.
- **Host-resource fence (30 GB RAM shared with the forge and six other accounts).**
  - `smatsprint.slice`: `MemoryHigh=17G`, `MemoryMax=19G`, `MemorySwapMax=0`, `TasksMax=4096`. Children:
    `smatsprint-exp.slice` (`CPUQuota=4800%`, `MemoryMax=12G`), `smatsprint-sbx.slice` (`CPUQuota=1600%`,
    `MemoryMax=6G`), `smatsprint-ctl.slice` (`CPUQuota=200%`, `MemoryMax=1G`). These are the user's default split
    (`00_README.md`), changed only through the lane-split action (Part H.5) within the ceilings of `limits.toml`.
    The user manager on this host delegates `cpu memory pids` (checked 2026-09-23); `cpuset` and `io` are not
    delegated, so CPU pinning is not a cgroup guarantee: use `CPUQuota` and thread caps, and do not ask for root.
  - The forge's `clforge.slice` has its own caps (`MemoryMax=20G`, worker `CPUQuota=1600%`). Static caps of the two
    programmes add up to more than the machine, so **admission, not caps, is the coordination**: the worker admits a
    job only if `MemAvailable` minus the job's declared RAM stays above 6 GB, exactly the rule the forge uses, so
    neither programme can starve the other or a lab mate. The host panel (Part D.4) shows both programmes' live use.
  - Each packed job runs in its own transient scope: `systemd-run --user --scope --slice=smatsprint-exp.slice
    -p MemoryMax=<declared>G -p MemorySwapMax=0 …` (no `Nice=` property: systemd 255 rejects it for scopes, as the
    forge found; the scope inherits the worker's nice level). A job that leaks host memory dies alone as `host_oom`.
  - **Thread caps.** Each CPU environment process is single-threaded (`OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`,
    `OPENBLAS_NUM_THREADS=1`); the trainer process uses at most 4 threads (`torch.set_num_threads(4)`,
    `TORCHINDUCTOR_COMPILE_THREADS=4`). The job's environment-process count is its declared thread budget.
  - **Bulk work is polite**: archive builds and compression under `nice -n 15 ionice -c3` with at most 8 threads;
    bulk rsync with `--bwlimit` (setting, default 40 MB/s).
  - On Vast there is no systemd; the thread caps and the host-RAM admission rule still apply.
- `smatsprint-watchdog.timer` runs a tiny stdlib-only script that shares no code with the controller: it reads the
  heartbeat files of the controller, the runner, the bridge and the wrapper and alerts directly (Gmail if the bridge
  itself is the silent one) when one has been silent for 10 minutes. A dead lab is reported by the off-lab dead-man
  workflow of Part D.8.
- Vast (a container, no systemd): a small supervisor loop under `setsid` restarts the worker with back-off after an
  abnormal exit only, while `state/desired.json` on that host says `run=true` with the current epoch. The supervisor
  and the worker guard (Part D.6) run in their own process groups and survive Pause.
- **Never reboot the shared server.** A reboot needs root and kills other people's jobs and the forge. The
  cold-start drill of Part E.2 replaces every reboot check: stop only this programme's units, start the controller,
  runner, bridge and wrapper with the network faked down for 60 s, and assert that the controller reconciles and
  starts the worker only if the state says LAB and RUNNING. The controller records
  `/proc/sys/kernel/random/boot_id`; when it changes because the lab rebooted for its own reasons, the recovery is
  logged as a real drill with pass or fail on the dashboard.

### R.3 Failure classes and what happens

| Class | Examples | Policy |
|---|---|---|
| External, transient | GitHub, Telegram or Vast 5xx, 429 or timeout; Drive rate limit; DNS; SSH reset | Exponential back-off with jitter, 5 s up to a 10-minute cap. Status publishing retries forever; alerts and needs queue until a send succeeds (Gmail after 30 minutes without Telegram, Part N.5). Inside a transition step: at most 8 tries, then roll the step back and alert. A call that is not idempotent (renting) is retried only after checking whether the previous try succeeded (adopt the labelled instance, never create a second; Part D.6). A circuit breaker opens after 5 consecutive failures of one service and the matching degraded mode starts (R.4). |
| GPU, recoverable | CUDA out of memory; illegal memory access; a Warp kernel launch failure; `host_oom` | Out of memory: if a same-account or sandbox process grew at the same time, re-queue unchanged without a strike (Part H.4); otherwise retry once with the next smaller declared world count, flagged in the row. Other CUDA errors: restart the worker process and retry once. Still failing: quarantine (R.5). |
| GPU, unusable | `nvidia-smi` fails, Xid errors, the device disappears | SAFE_PAUSE and the need `unexpected` with the exact message (a reboot may be needed, which only the user can arrange). CPU-backend jobs may continue if the controller can prove they do not touch the GPU. On Vast: fence first (Part D.2), then resume from the lab backup on a fresh instance. |
| Physics | MuJoCo instability warnings, NaN or infinite state, contact penetration beyond the declared depth, a muscle force past its bound | Retry once from the last update checkpoint with a new environment seed. If it recurs, record `physics_failure`: a finding about that configuration (it counts against it), not an error of the runner. |
| Numerical (learning) | NaN loss, exploding value loss, KL blow-up past 10× the target | Retry once from the last checkpoint. If it recurs, record `diverged`; it counts against the configuration. |
| Backend | the GPU backend fails parity or compilation for a model version | The backend certificate for that model and code identity is revoked; jobs that required it return to the queue as CPU jobs or wait, as their registration says; the dashboard says why. Never silently switch a certified comparison to another backend. |
| Harness bug | an exception in `runner/`, `control/`, `bridge/` or `codexwrap/` | systemd restarts the process. The same runner traceback 3 times in 10 minutes, or three watchdog kills in 30 minutes, puts the runner in SAFE_RUNNER (R.4): it stops releasing new candidates and sweeps, finishes pipelines in progress, keeps the evergreen queue running, and raises `unexpected` with the traceback. A worker that fails 3 or more *different* jobs within 10 minutes with the same infrastructure error stops popping, and the matching degraded mode starts. |
| Data | a reference-motion or model file hash mismatch | Re-fetch from the manifest (3 tries); otherwise refuse the affected candidates and raise `unexpected`. |
| Disk | project above 90 % of its cap; filesystem free space under `min_free_gb`; ENOSPC | The controller prunes on whichever host holds the live work tree, never during a transition: temporary files, compile caches, then eval rollouts and clips of candidates below L1 older than 14 days, oldest first; new jobs pause; `disk_floor` need. Never prune results, the ledger, `record/`, registered configs, stage-final checkpoints, anything a claim uses, the environment the controller runs from, or `~/.config/smatsprint/`. Below `hard_floor_gb`: SAFE_PAUSE. |
| Needs a human | an expired token, credit under the floor, root needed, an instance that will not die | A registered need (Part N.10) with one exact ask and the safe options as buttons; everything that does not depend on it keeps running. |
| Telegram or build | the bridge cannot reach Telegram; a Codex session fails | Part N.5 and N.8 policies: Gmail fallback, bounded back-off, `build_stuck`. The experiment is never affected. |

### R.4 Degraded modes (a badge on the dashboard, each with one plain sentence)

```text
FULL          everything works
NO_GITHUB     cannot push or fetch                 -> the runner continues; status queues locally; use sprintctl over SSH;
                                                      dashboard commands sent meanwhile expire and are visibly rejected on reconnect
NO_TELEGRAM   the bridge cannot reach Telegram      -> needs and alerts go by Gmail; the dashboard's Needs panel still shows them
NO_VAST       API down or credit under the floor    -> Move to Vast disabled with the reason; the lab is unaffected
NO_DRIVE      token dead or no space                -> Drive buttons disabled with the reason; alert
NO_GPU_BACKEND the GPU backend is not certified      -> jobs run on the CPU backend; GPU-only candidates wait and say so
SAFE_RUNNER   the same runner traceback 3x in 10 min -> no new candidates or sweeps are released; pipelines in progress and
                                                      the evergreen queue continue; traceback on the dashboard; need raised
SAFE_PAUSE    GPU unusable, disk below the hard floor, or an invariant check failed -> checkpointed and stopped; need raised
```

The runner enters and leaves these modes by itself and logs each change. Only SAFE_PAUSE waits for a person.
Pauses that wait for a person are the PAUSED(by: user | lease | safe) phases of Part D.2, not modes; PAUSED(by:
polite) ends by itself.

### R.5 Job-level safety

- A **progress watchdog** per job: no PPO update or evaluation episode completes for 15 minutes → kill and retry
  once from the last checkpoint. A stop requested by the controller, the guard or systemd is not a watchdog event.
- **Three strikes**: a job that failed three times for reasons that belong to it (physics failure, divergence,
  an exception in science code, the progress watchdog) is quarantined in `work/queue/failed/` with its logs, and its
  candidate is marked `failed` with the reason in plain words on the dashboard. Infrastructure events never add a
  strike: ENOSPC, `disk_low`, host loss, any signal from the controller, guard or systemd, a missing code tree, an
  out-of-memory caused by another process growing, and transfer errors re-queue the job unchanged.
- **Idempotence**: job identity is the hash of Part C.3; re-queuing a finished job returns the stored result;
  duplicate rows cannot enter the ledger.
- **Resource fencing**: each job declares CPU threads, host RAM (from the measured per-environment memory) and GPU
  memory; a job that exceeds its GPU declaration by 25 % is killed and re-queued alone.

### R.6 The evergreen queue (the machine is never idle because the queue is)

Part C.4's generator: pre-registered top-up seeds of registered claims, refreshed baseline arms, the periodic noise
and throughput refresh, and clip renders; plus the `queue_empty` need with the catalogue blocks not yet released as
buttons. It never invents a configuration and never adds seeds beyond a claim's pre-registered top-up (an
open-ended stream of seeds would be optional stopping). If even this is empty, the dashboard says the machine is
idle and why, and an alert goes out after 15 minutes.

### R.7 State integrity and recovery on start

- Every state file is written atomically, carries a `schema_version`, and keeps its last 20 versions in
  `state/snapshots/`. A file that fails to parse is replaced by the newest snapshot that parses, with an alert.
- The ledger and the steering log are append-only JSONL, hash-chained, flushed and fsynced per row, committed to git
  every 10 minutes and pushed through the single push function of `control/publish.py` (Part D.3). GitHub is thus an
  off-site copy of the whole scientific record.
- **Reconciliation at every controller start and after any host loss**, before any command is accepted: the live
  `work/queue/running/` against live processes; the ledger's queued and running jobs against `queue/outbox/`,
  `queue/delivered/`, the worker-side queue and `record/` (orphans return to the outbox); leases against the
  instances that exist on Vast under this programme's label (Part D.6); the needs store against the bridge's sent
  messages; the wrapper's state against running `smatsprint-codex-*` units. "Vast, GitHub or Telegram unreachable"
  is *unknown*, never "absent". `work` must resolve to exactly one complete generation; any `*.staging` directory is
  garbage; any half-finished transition is resumed or rolled back from its recorded step.
- Transfers use `rsync --partial-dir=.rsync-partial --timeout=120` (never plain `--partial`) and SSH keep-alives;
  pulls from a worker add `--safe-links --no-devices --no-specials` and land only in staging or the mirror directory.

### R.8 Self-audit

- A daily `doctor` run, results on the dashboard (`tests.json`): the invariants of Parts D.2 (I1–I10) and H.11
  (LI1–LI10); unit states (the worker unit not enabled); disk against the cap and both floors; RAM; clock sync;
  the deploy key; the bridge's last successful send and poll; the drop key; the Drive token (`rclone about`); the Vast
  key and credit; the age of the last push and of the last lab mirror; `GATE_HASH` and `EVAL_HASH`; the ledger and
  steering hash chains; the last run of the off-lab dead-man workflow (Part D.8); registered dashboard-token expiry
  dates; the last cold-start drill.
- A weekly chaos drill in a low-priority slot with a dummy job: `kill -9` the worker (confirm resume and bit-equal
  parameters), kill the runner mid-harvest (confirm no duplicate rows), kill the bridge mid-callback (confirm no
  double effect). A failed drill raises a need. Failsafes that are never exercised rot.

### R.9 Changing the harness while the runner runs

When a later Codex session must patch `runner/`, `control/`, `bridge/` or science code: `sprintctl drain` (running
jobs finish their current update and checkpoint; nothing new starts; then PAUSED) → change on a branch in the dev
tree, which no service runs from → the full test suite → `sprintctl release <tag>` (moves `state/trees/service/` to
the tag and restarts the units) → `sprintctl resume`. A science-code change gives new `code_id`s: registered
candidates keep their old identity and run on their old code; new candidates use the new code; a comparison never
mixes code identities (Part C.10). Never hot-patch a running service, and never edit the service tree in place.

### R.10 What no automatic path may ever do

Delete results, ledger rows, steering rows, registered configs or `record/`. Destroy a Vast instance without a
verified copy elsewhere (an instance under this programme's label whose lease shows no worker ever started there
holds nothing and may be destroyed at reconciliation). Spend beyond a lease cap or under the credit floor. Change
`gate/`, `eval/` or a tolerance. Pull code onto the lab from GitHub, or onto a worker from anywhere but the lab. Run
code on the lab from a tree that has been on a rented host. Put a user credential on a rented host. Message anyone
but the owner. Touch another user's process, the forge's units, files, bot, `gh` session or Vast instances, another
project's unit, or a Vast instance without the `smatsprint-` label.
