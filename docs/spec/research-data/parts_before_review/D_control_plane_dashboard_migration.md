## PART D — Control plane, dashboard, locations, migration, Drive, alerts

Adapted from the forge's Part D. The move semantics are the user's own and are kept exactly; the dashboard panels,
the command set and the names are this programme's.

### D.1 Design rules for the control plane

- The **controller on the lab is the single source of truth** for where the experiment lane's work is, what state it
  is in, and what command is being executed. The dashboard is a view plus a mailbox; a Vast worker is a limb.
- The **control plane never moves**: controller, runner, bridge, wrapper, the git repository, the ledger and every
  credential stay on the lab in every state (a few hundred MB, no GPU). "Moving the experiment" means moving the
  **worker and its work state**. The sandbox lane stays on the lab unless the user ticks "also move the sandbox" in
  the move dialog (Part H.7); then its tree is copied as a second, separately verified work state.
- **Three kinds of state, one owner each.**
  - *Record state* is small, lab only, never moved or evacuated: `ledger/`, `configs/registered/`, `state/`,
    `queue/outbox/`, `queue/delivered/`, `baselines/cache/` and `record/<job_id>/` (each finished or failed job's
    `results.json`, `curves.csv`, `rollouts.npz` when kept, `DONE` or `FAILED`, log tail). The runner writes the
    ledger, the registered configs, the outbox and the baseline cache; the controller writes `state/`, `delivered/`
    and `record/`. The runner harvests only from `record/`, so harvest is identical on LAB and VAST.
  - *Work state* is bulky and moves with the worker, as one directory that swaps with one rename:
    `work/{runs,queue/{pending,running,done,failed},code,compile_cache,refdata}`. Only the worker writes inside the
    live `work/`. `work/refdata/` holds the hashed reference motions and composed models every job loads; it is part
    of every move and every lean archive.
  - *Backup* is a second `work/` tree on the lab disk or on Drive. Only `lab_mirror` and the moves write it.
- **One work directory, one rename.** `work -> work.d/<generation>/`; staging is `work.d/<new>.staging/`; a retired
  generation is `work.d/<old>.retired/`. The doctor asserts that `work.d/`, staging and the backup share one
  filesystem (atomic `rename()` needs that); a mismatch disables moves with the reason. A retried transfer starts a
  fresh staging directory with `--link-dest` pointing at the backup and at the abandoned staging directory. The swap
  after verification: (1) rename `<new>.staging` to `<new>`; (2) `os.symlink` then `os.replace` for `work`; (3) only
  then retire or delete the old generation. No process runs `mkdir -p` on `work/`; a missing `work` is a hard error.
- **The controller is the only process that delivers jobs**, exactly once: from `queue/outbox/` into the live
  `work/queue/pending/` (local rename on LAB; rsync into `pending/.incoming/` plus a remote rename on VAST), only if
  the job id is absent from all four worker-side queue directories and from `record/`; the file then waits in
  `queue/delivered/` until `record/<id>/` holds `DONE` or `FAILED`. On host loss, replacement or restore, every
  delivered job without a record returns to the outbox.
- **Records travel every 60 s** from the live `work/runs/` into `record/<id>.tmp/`, are checked against the sha256
  and size in `DONE`, and are renamed into place. A job whose files do not match its `DONE` is ignored by the record
  copier, the mirror and the runner.
- Every transition is a **state-machine step with a precondition, an action, a verification and a rollback**. No
  step deletes or destroys anything until the copy that replaces it has been verified.
- Every command is **idempotent**, has a UUID, carries `based_on` (D.3), carries a reason if it changes the
  experiment (Part H.5), is acknowledged with a plain-language message, and is logged in
  `state/command_log.jsonl` and in the Ledger panel.
- **Pause is always safe and always fast.** Every worker process keeps its last update-boundary checkpoint and
  exits. **GPU ownership is decided by process, not by memory level**: before signalling, the controller snapshots
  every PID in `smatsprint-exp.slice` on the lab (or the recorded process group on Vast); Pause is verified when
  every snapshotted PID has exited and none appears in `nvidia-smi --query-compute-apps=pid,used_memory` on two
  reads 2 s apart. Memory held by other people's processes, by the forge or by the user's other services never fails
  the check; it is reported in words ("GPU is free of our work; the forge is using 9 GB"). Target: ≤ 60 s from the
  controller seeing the command, ≤ 90 s from the button press. Pause also frees the CPU cores: the environment
  processes are in the same slice and stop with the worker.
- **Resume never loses more than one PPO update** of any job, and a resumed CPU job's parameters equal the
  uninterrupted run's (Part C.5).
- The state machine is a **pure function** `(state, event) -> (state, actions)` with side effects behind interfaces
  (`Vast`, `Drive`, `Shell`, `Git`, `Telegram`), so every path is tested against fakes before a dollar or a byte is
  at risk. The same function computes the `actions[]` the dashboard shows (D.4).
- **Reconciliation** runs at every controller start and after any host loss (Part R.7).

### D.2 Location and run state (persisted atomically in `state/location.json` and `state/worker_state.json`)

```text
location       ∈ { LAB, VAST, DRIVE_ONLY }        where the experiment lane's live work state is
phase          ∈ { RUNNING, PAUSED(by: user | polite | lease | safe), STOPPED, TRANSITION(<name>, <step>), NEEDS_USER(<code>) }
worker_epoch   integer; incremented on every worker start anywhere (epoch fencing, below)
state_version  integer; incremented when location changes or the phase changes kind (never at a step inside a transition)
copies         = { lab_backup: { generation, kind: full | mirror | results_only, verified_at, age } | null,
                   drive_archives: [ { archive_id, kind: lean | full, verified_at, age, bytes } ],
                   sandbox: { where: LAB | VAST, moved_with_experiment: bool } }
backup_covers_stop  bool; true only when a FULL copy completed and verified AFTER the worker's last exit
vast           = { instance_id, label, gpu, cpu, cores, dph, storage_cost, inet_up_cost, inet_down_cost, end_date,
                   started_at, lease: { lease_id, max_hours, max_usd, credit_floor_usd, to_destroy }, cost_so_far,
                   parked, parked_at, measured_transitions_per_usd } | null
transition     = { name, step, n_steps, step_label, started_at, bytes_done, bytes_total, rate_bps, eta_s, can_cancel,
                   end_phase: RUNNING | PAUSED } | null
worker         = { host, pgid, epoch, jobs: [{job_id, candidate, stage, seed, step, total, last_ckpt_at}],
                   last_heartbeat_at, gpu_name, cpu_threads }
actions        = [ { command, group, enabled, reason, confirm } ]   computed by the state machine for the page (D.4)
```

Transitions (name → precondition → steps → verification). The words in **bold** are the user's own requirements.

- **pause** (any RUNNING; `paused_by=user`) → none → (1) write `phase=PAUSED(by: user)` to `state/location.json`
  and `run=false` to `state/desired.json` beside the worker (over SSH on Vast), fsynced, BEFORE any signal; (2) stop
  the worker (lab: `systemctl --user stop smatsprint-worker.service`, `--no-block`, then poll `is-active`; Vast:
  SIGTERM to the worker's process group over SSH, SIGKILL after 45 s; the supervisor and the guard survive). Pause is
  delivered to every host that can hold a worker: the lab unit and every instance with an open lease. → GPU-free
  check by PID snapshot (D.1); PAUSED. **The GPU and the CPU cores are freed for other members within about a
  minute, and nothing is lost.** *On Vast* the instance keeps billing while paused, so the banner shows the running
  cost and a countdown: after `park_after_min` (default 30) the controller **parks** it (below).
- **polite_pause** (LAB RUNNING; automatic) → a GPU compute PID of **another Linux account** holds more than
  `polite_min_mib` (default 1024) for more than 60 s → pause as above with `paused_by=polite`; the bridge sends
  `polite_pause_long` after `polite_alert_hours` (default 6) naming the owner, process and memory, offering Move to
  Vast. **polite_resume** (PAUSED(by: polite); automatic) → no such process for `polite_resume_min` (default 10)
  consecutive minutes → resume. Only a polite pause ends by itself. Same-account processes (the forge's
  `clforge-*` jobs, `llama-swap`, `open-webui`, the 11434 server) are not lab mates: they coexist by default
  (`same_account_gpu: coexist | pause`), the packer's GPU budget is re-read before every admission, and an
  out-of-memory that coincides with their growth is retried without a strike. Never stop, restart or reconfigure
  those units.
- **resume** (PAUSED at LAB or VAST) → live copy present and consistent; on the lab, the polite check finds no other
  account's process on the GPU, or the user confirmed the override → increment `worker_epoch`, write
  `desired.json = {run: true, epoch}` beside the worker, start it; heartbeat within 120 s; RUNNING. **Resume continues
  exactly where it stopped.** *If the Vast instance was parked:* request the start; if it is not up within 10
  minutes and `backup_covers_stop` is true, **fence first** (destroy the stuck instance, confirm it is absent), then
  rent a fresh instance and restore from the lab backup; if the flag is false, never replace it: keep the start
  request open and copy the data off the stopped instance (Vast's billing documentation says a stopped instance's
  data can still be copied off; `vastai copy` from a stopped instance is verified in the rehearsal); set the flag
  when the copy verifies. After 60 minutes with neither, `vast_instance_wont_start` with "Keep waiting" and "Resume
  from the backup and lose N minutes".
- **move_to_vast** (LAB, RUNNING or PAUSED) → Vast credit ≥ floor + 2 h of the offer's price; lease caps set and
  under the `limits.toml` ceilings; rentals in the last 24 h under their ceiling → (1) pause; **the lab GPU and CPU
  cores are now free and verified free**; (2) write the lease file first, then rent an offer chosen by D.6 under
  the label `smatsprint-<lease_id>` (adopt an existing instance with that label before any create or retry);
  (3) provision (idempotent; ≤ 15 minutes or abort and destroy); (4) copy the work state (`work/runs/` with pruned
  checkpoints excluded, `work/queue/`, `work/refdata/`; not `code/` or `compile_cache/`, which are regenerated, the
  code from the lab's archive) with `rsync -a --partial-dir=.rsync-partial --timeout=120 --info=progress2` over SSH;
  and the sandbox tree too if ticked; (5) verify: checkpoint files against their manifests, a `--checksum` pass over
  small files without a manifest entry, the regenerated state manifest equal to the lab's; (6) increment
  `worker_epoch`, write `desired.json`, start the worker on Vast; heartbeat; (7) `location=VAST`,
  `copies.lab_backup={kind: full, age: 0}`, `backup_covers_stop=false`. **The lab keeps a full backup of the files on
  disk, its GPU and CPU are freed, the files copy to Vast and the experiment continues there from the same state.**
  On any failure before step 6: destroy the instance, keep the lab copy, resume on the lab, report why.
- **lab_mirror** (automatic while VAST, every `mirror_interval_min`, default 30; 120 when the offer charges for
  bandwidth). It carries checkpoints only (results travel by the 60 s record copier), driven per run by the
  worker's own checkpoint manifest: fetch `ckpt/latest` and its manifest into a temp dir; copy exactly the listed
  files with `rsync --files-from=… --partial-dir=.rsync-partial --safe-links --no-devices --no-specials` (never
  `--inplace`, `--append` or `--delete`); sha256 them on the lab; only then write the backup's manifest and flip its
  `latest` last; only then delete backup checkpoints older than the previous verified one. A run's backup always
  holds at least one complete, hash-verified checkpoint. Anything with an older `worker_epoch` is ignored. *If the lab
  has no room* (under the free-space floor of Part A.5): mirror results and logs only
  (`kind=results_only`), stream the latest verified checkpoints to Drive every `drive_refresh_h` (default 6), and say
  on the banner how old the newest off-Vast checkpoint is.
- **move_to_lab** (VAST) → lab free disk ≥ (bytes that differ from the backup × 1.3), from the last mirror → (1)
  pause on the worker; (2) rsync worker → a fresh `work.d/<new>.staging/` with `--link-dest=<current lab backup
  generation>`; (3) verify; (4) the one-rename swap: the old backup generation becomes `work.d/<old>.retired/`,
  `work` flips to `<new>`, then the retired copy is deleted. **Everything moves back, the old lab backup is replaced
  by the new files**; `backup_covers_stop=true` when the swap verifies; (5) **destroy the Vast instance** and confirm
  it is absent from the account; delete its `state/known_hosts/<instance_id>`; (6) increment `worker_epoch` and start
  the worker on the lab (polite check first); (7) `location=LAB`, `copies.lab_backup=null` until the next move.
  **At the next move to Vast, the latest state of the lab files becomes the new backup**, by construction. Failure
  before step 5 leaves the instance alive and the backup untouched; failure at step 5 raises
  `vast_instance_wont_die` with the exact instance id and retries the destroy every 5 minutes.
- **backup_to_drive** (LAB or VAST) → Drive free space ≥ the estimated archive size (D.7) → build, upload, verify;
  nothing is deleted; `copies.drive_archives` gains an entry.
- **evacuate_lab_to_drive** (**emergency: the lab disk must be given up**; args `archive: lean | full`, `free_venv`)
  → a verified Drive archive newer than the copy being deleted that contains everything about to be deleted that is
  not regenerable (made first if needed) → delete only (a) files the archive contains, (b) regenerable files
  (`work/code/`, `work/compile_cache/`, project caches, `*.staging/`, `*.retired/`), (c) the disposable list of D.7.
  The dialog shows three lines with sizes ("kept in the archive", "rebuilt automatically later", "dropped for good;
  results stay") and leads with "This frees about X GB on the lab". **Never delete the environment the controller
  runs from, the repository, the ledger, record state, registered configs or `~/.config/smatsprint/`.** If the live
  copy was on the lab the state becomes DRIVE_ONLY; if it was the backup while Vast runs, the state stays VAST and the
  mirror runs in its no-room mode.
- **evacuate_vast_to_drive** (**emergency: Vast is out of space, or the user must stop**) → pause; archive from the
  worker to Drive (D.7, part by part through the lab without touching the lab disk); verify; `backup_covers_stop=true`;
  **destroy the instance so it is gone**; any lab copy is now stale and marked so; DRIVE_ONLY, unless the lab mirror
  covers the stop, in which case `location_event` offers "resume on the lab from the lab copy (N min old)" and
  "restore from Drive".
- **restore_from_drive {target: lab | vast}** (DRIVE_ONLY, or any state if the user insists) → *Target lab:*
  download into a fresh staging generation, verify every part against `MANIFEST.json`, unpack, regenerate and
  compare the state manifest, the one-rename swap (what it replaces is kept as `.retired` until the next verified
  backup exists), `uv sync --frozen`, PAUSED; the user presses Resume. *Target vast:* the move_to_vast
  preconditions; rent and provision; on the lab `rclone cat smatsprint-gdrive:<part> | ssh worker 'cat >
  staging/<part>'` part by part, so nothing is written to the lab disk and the Google token stays on the lab; verify
  each part on the worker; unpack; `location=VAST`, PAUSED. On any failure destroy the new instance (it holds nothing
  that is not on Drive), stay DRIVE_ONLY and report why. **The dashboard can restore from Drive to either location.**
- **destroy_vast** (VAST PAUSED, or after a failed move) → I2 → if reachable, park it first (pause, full copy,
  verify, set `backup_covers_stop`), so the dialog can truthfully say nothing is lost; destroy; confirm absent; LAB
  PAUSED (if the lab copy is full) or DRIVE_ONLY.
- **parked_destroy** (VAST PAUSED, `parked=true`, `backup_covers_stop=true`; automatic) → after
  `parked_destroy_after_h` (default 48, 0 = never), with a need 6 h before → `destroy_vast`; the state becomes LAB
  PAUSED. If the flag is false or the lab disk floor is breached, a need instead, repeated daily with the accrued
  storage cost.
- **lease_cap** (VAST RUNNING; automatic; D.6) → `max_hours` reached → alert only; 90 % of a money cap → alert;
  `cost_so_far + dph × estimated_sync_hours ≥ max_usd`, the monthly cap, or credit at the floor → if
  `at_cap = come_home_if_lab_free` (default) and no other account's compute process is on the lab GPU and the
  move_to_lab disk precondition holds, run move_to_lab by itself; otherwise park and raise `lease_cap_reached` with
  "Raise the cap by $X and continue" (below the ceiling only) and "Bring it home when the lab GPU is free". It never
  destroys without a verified copy elsewhere (I2). Six hours before the offer's `end_date` the same choice is made.
- **stop** → pause, then STOPPED: neither the worker nor the runner's release of new candidates runs until Resume.
- **drain** (RUNNING) → none → undelivered jobs return from `work/queue/pending/` to `queue/outbox/`; running jobs
  finish their current PPO update and checkpoint; then PAUSED(by: user). Resume undoes it (Part R.9).
- **emergency_stop** → write PAUSED and `run=false`, then on the lab `systemctl --user kill --signal=SIGKILL
  smatsprint-worker.service` followed by `systemctl --user stop`; on Vast SIGKILL the worker's group and the
  supervisor (the guard survives); no destroy, no delete; PAUSED with a warning that the current update of each job
  is lost. During a move it kills transfers and worker processes, destroys and deletes nothing, records the step and
  raises `location_event` with "Continue the move from step k" and "Undo the move", stating whether a Vast machine
  is billing meanwhile.
- **cancel_move** (TRANSITION(move_to_vast, step < 6) or TRANSITION(move_to_lab, step < 4)) → a user-requested
  failure: before the point of no return the state machine runs the rollback already specified above. After that
  point the button is disabled with "too late to cancel safely; finishes in about N min".
- **run_replication {claim_id}** (LAB; a claim whose only missing gate is G5, Part G.7) → the move_to_vast
  preconditions with the lease sized to the estimate the dialog shows → move_to_vast; the runner serves that claim's
  replication jobs first; when the last one records, move_to_lab by itself under the polite rule. `auto_replicate:
  ask | auto` (default `ask`).
- **register_device {client, token_expires_on}** and **settings {key, value, old_value, reason}** change no location
  or phase.

**Pause never abandons a transition.** `pause` and `emergency_stop` never abort a move; every move already frees the
GPU at its step 1. The controller records `transition.end_phase=PAUSED`; the transition runs to its commit point or
rolls back; it skips its "start the worker" step if that has not run yet, and if a worker was already started it is
stopped on that host. The acknowledgement says what will happen: "Paused. The move to Vast will finish copying (step
4 of 7) and then stay paused there; the lab GPU is already free."

**Park.** Parking, lease-cap handling, `destroy_vast`, `move_to_lab` and `evacuate_vast_to_drive` always run in this
order: pause, full copy, verify, set `backup_covers_stop`, and only then stop or destroy. A parked instance keeps its
disk and bills storage only; the banner shows that rate and the `parked_destroy` countdown.

**Replace = fence first.** The controller gives up on an instance when the API says running but SSH (direct and
proxy address) has failed for 15 minutes or more, or when a parked instance is not up 10 minutes after a start
request; it destroys the instance through the API first and confirms it is absent (allowed only under the
covering-backup flag or the unreachable clause of I2), and only then rents the replacement. There is never more than
one instance with an open lease. If the Vast API is down, the lease is flagged `to_destroy` (persisted) and retried
every 5 minutes, and nothing is ever pulled from that instance again.

**Epoch fencing.** `worker_epoch` is incremented on every worker start anywhere, written into the worker-side
`desired.json`, stamped into `worker_state.json`, every `DONE`/`FAILED` and every checkpoint manifest. The mirror,
the record copier and the moves ignore anything with an older epoch, so a partitioned host that returns after its
replacement can never overwrite newer files.

Invariants, each with a test that tries to break it (Part E.2): **I1** at most one worker holds the current
`worker_epoch`, across lab and Vast, and the output of any other worker is never read; **I2** a Vast instance is
destroyed only when `backup_covers_stop` is true, or the API reports it running yet it has been unreachable over SSH
for 15 minutes or more (the dialog and the need state the exact minutes of work lost); an instance the API reports as
stopped is never "lost"; **I3** lab work state is deleted only when every file being deleted is inside a verified
Drive archive, is the retired copy after a verified swap, is regenerable, or is on the disposable list the user
confirmed; record state is never deleted; **I4** resume loses at most one PPO update per job; **I5** every command
is logged with an outcome; **I6** after Pause is acknowledged, no process of `smatsprint-exp.slice` holds the GPU;
**I7** no transfer writes a file of a live or backup copy in place; **I8** at a lease cap, GPU billing stops within
one check interval without destroying data; **I9** no user credential (the Codex login, the Google token, any GitHub
key or token, the Telegram or Gmail secret, the account's Vast key, the drop private key) is ever present on a Vast
host (the instance-scoped key Vast pre-installs is not a user credential); **I10** the controller acts only on Vast
instances whose label starts with `smatsprint-`.

### D.3 Command channel (GitHub, no server ports exposed)

- Private repository **`mushfique-dgist/smat-sprint-lab`** (free on 2026-09-23). Branches: `main` = code and small
  ledger files; `ledger` = the runner's ledger commits; `status` = one orphan commit force-pushed by the controller
  when content changes (minimum interval 60 s; command-state, phase and transition-progress changes publish at once,
  at most one push per 5 s; heartbeat at least every 120 s); `control` = the mailbox; `gh-pages` = the dashboard
  shell. The `status` commit is built in a separate bare repository `state/status.git`, pruned daily with
  `git gc --prune=now`. Every `git push` goes through one function in `control/publish.py` under a flock with a
  minimum spacing of 30 s. It pushes `main` and `ledger` (fast-forward only), `+status` (the only forced ref) and
  `control` (plain, never forced). Every push from the lab uses the deploy key.
- **The Pages site is public even though the repository is private** (GitHub Pro; Part A.4). So `gh-pages` holds
  only the static shell (`index.html`, `app.js`, `style.css`, vendored chart library, `drop.html`, `drop-key.json`,
  a generic `privacy.html`, `.nojekyll`, `<meta name="robots" content="noindex">`), with no data, names, ids, lane
  contents or research text. The page derives the owner and repository at runtime (editable in the token dialog).
  Without a token the page shows only the token prompt.
- **Reading:** `GET /repos/{owner}/{repo}/contents/<file>?ref=status` with `Accept: application/vnd.github.raw+json`,
  `cache: no-store` and self-managed ETags (`If-None-Match`; a 304 costs no rate limit). Layout of the status branch:
  `status.json` (≤ 150 kB, enforced by a publish-side test that also fails if any file on the branch exceeds 1 MB)
  feeds the first screen of every panel: banner, lanes, `actions`, `commands`, the reproduction table, the ladder
  counts, open needs, jobs, resources, the host view, mode; `recent.json` (the last 50 rows with cards);
  `candidates/<cand>.json` (versions, jobs, per-seed tables, steering refs); `claims/<claim_id>.json`;
  `runs/index.json` plus `runs/<page>.json` (500 rows per page, closed pages immutable); `series/<page>/<job>.json`
  (downsampled curves); `clips/<id>.webm` (each under 1 MB); `steering/<page>.json`; `sandbox.json` (the sandbox
  lane's own status, published separately and labelled); `needs.json`; `glossary.json`; `weekly/<week>.md`. Charts
  are drawn in the browser from JSON series; clips are fetched as blobs. Polling: every 60 s, every 5 s while one of
  this device's commands is unfinished, and at once when the tab becomes visible.
- **Writing:** the dashboard `PUT`s `inbox/<uuid>.json` on `control` (`{id, command, args, reason, based_on,
  created_at, client}`), one at a time, then follows the command in `status.json` (`commands: [{id, state:
  received|running|done|failed|rejected, message, step}]`). On a 409, 5xx or network error it re-sends the same
  UUID up to 5 times; after the fifth failure a red "NOT SENT" strip shows the `sprintctl` line. If no `received`
  state appears within 60 s: "The server has not picked this up. It may be offline or unable to reach GitHub. Over
  SSH, `sprintctl pause` always works." The controller never force-pushes `control`; processed ids live in
  `state/command_log.jsonl`; once a day it deletes inbox files older than 24 h in one commit.
- **Ordering and staleness:** commands run in the commit order of `control` (dashboard) merged with `sprintctl` and
  Telegram commands as they arrive. A state-changing command runs only if `based_on` equals the current
  `state_version` and its commit time is under 15 minutes old by the lab clock; otherwise it is rejected, never
  silently, with a plain message, and an aged rejection sends one alert. `pause`, `stop`, `emergency_stop` and
  `cancel_move` ignore `based_on`; an aged `pause`, `stop` or `emergency_stop` is still executed up to 24 h old when
  no later `resume` follows it. At most one transition command is in progress; another is rejected with "busy: <what
  is running>". Steering actions (Part H.5) are ordered the same way and additionally require their reason.
- **The enumerated command set is exactly the dashboard's controls**: the D.2 transitions, the H.5 steering
  actions, Promote, the settings keys, `register_device`, and `drop` (Part N.6). A unit test fails if a command or
  setting in the schema has no dashboard control, or the reverse.
- **Dashboard auth:** one fine-grained personal access token per device, limited to this one repository with
  *Contents: read and write*, expiry 366 days. The page offers a "Create a token" link built at runtime from GitHub's
  documented template parameters (`name`, `description`, `target_name`, `expires_in=366`, `contents=write`; verify
  the parameter names in M2 against GitHub's current documentation); repository selection cannot be pre-filled, so
  the need's steps say "Only select repositories → smat-sprint-lab". The dialog also asks for the expiry date the
  user chose (the page cannot read it cross-origin), stores it beside the token, warns from 14 days before, and sends
  `register_device` so `token_expiring` can reach the phone. **Shared origin:** Pages sites of one account share the
  `mushfique-dgist.github.io` origin and its `localStorage` (the account already publishes `course_monitor`, and the
  forge's dashboard will join it). Default: the page stores the token AES-GCM-encrypted (WebCrypto, PBKDF2) under a
  short PIN typed once per browser session, so another site on the origin reads only ciphertext. Optional (one phone
  need, offered in M2): publish the shell from a dedicated free organisation so the origin is the dashboard's alone.
- **Hardening the shell** (a public page that holds a write token): CSP `default-src 'none'; script-src 'self';
  style-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src https://api.github.com;
  base-uri 'none'; form-action 'none'`; no inline scripts or handlers, no `eval`; every fetched string inserted with
  `textContent` or `createElement`, never `innerHTML`; a small vendored allow-list Markdown renderer for the weekly
  note; a grep test over `dashboard/` for banned calls; the Playwright hostile-status test.
- **Controller auth:** one read/write **deploy key** for this repository only (`~/.config/smatsprint/deploy_key`),
  created with the build's own `gh` session (Part N.7), which is logged out when M2 ends. A Vast worker holds no
  GitHub credential of any kind.
- **Threat model** (as the forge's): a leaked dashboard token can write to the repository, so the controller treats
  inbox files as untrusted data (strict schema, enumerated commands, bounded settings, reasons stored as text and
  never reaching a shell); the lab never pulls code from GitHub; two repository rulesets created by API in M2
  (verify against current docs): ruleset A on every branch except `control` restricts creations, updates and
  deletions with the deploy key as the only bypass actor; ruleset B on `control` restricts deletions and blocks force
  pushes with no bypass. Tests with the real dashboard token: a PUT to `gh-pages`, `main`, `ledger` and `status` is
  refused, deleting `gh-pages` is refused, creating a branch is refused, a PUT to `control` succeeds, and the
  controller's force-push to `status` still works. What a stolen token can do is bounded on the lab by
  `~/.config/smatsprint/limits.toml`, written at install and changed only over SSH (`sprintctl limits …`): Vast spend
  per calendar month (default USD 150), max $/h (default 1.00), rentals per 24 h (default 4), the host resource
  ceilings for the lane split, and the LLM summary ceiling (3 per day). Destructive commands keep what they replace as
  `.retired` until the next verified backup exists.
- **Gate and tolerance changes never travel through the mailbox.** A gate epoch is opened only by
  `sprintctl gate-change <key> <value> --reason "…"` over SSH, and never for a claim that already has a result under
  the current epoch (Part G.8). It bumps `GATE_HASH`, appends to `ledger/epochs.jsonl`, raises `gate_epoch_opened`
  and is shown on the dashboard permanently.
- **Fallback without GitHub:** `sprintctl <command>` on the lab writes the same command into the same queue;
  `sprintctl status` prints the banner the dashboard would show. SSH plus `sprintctl pause` always works.

### D.4 The dashboard (GitHub Pages, static, plain language, PC and phone)

Requirements: no build step and no CDN (vanilla JS or one vendored ES module); dark and light themes; one screen of
summary at the top of each panel; on a phone a sticky panel bar; every number from the status branch, never typed by
hand; **the page never re-implements a precondition**: every button, its enabled state, its reason when disabled and
the numbers in its dialog come from the `actions[]` the controller publishes (computed by the same pure state machine
the model tests cover); a button whose tests are not green is visible, disabled and says "not built yet"; Pause and
Emergency stop are rendered enabled even when the status is stale or missing; plain words first, codes second
(ladder, gates, invariants and lanes always with their plain names; the glossary on tap).

**Lane banners and chips everywhere** (Part H.3): the Watch, Steer and Ledger panels carry the EXPERIMENT banner;
the Sandbox panel carries the SANDBOX banner; every experiment-changing control carries "changes the experiment" and
a required one-line reason field; every sandbox control carries "testing only, cannot change the experiment".

**The top banner** answers, in this order, with one colour and one icon per location: WHERE ("RUNNING on the lab: 48
CPU threads and the GPU" / "RUNNING on a rented Vast machine (64 cores, $0.41/h, $3.20 so far)" / "PAUSED on the lab:
GPU and CPU verified free at 14:02" / "PAUSED on Vast: still billing $0.41/h, parks in 18 min" / "NO LIVE COPY: the
work is on Drive only" / "MOVING lab → Vast, step 4 of 7: copying checkpoints" / "NEEDS YOUR DECISION: (the need's title)");
WHAT (the phase and who paused it; for a move the step sentence, a byte bar and minutes left, and "You can close this
page. The move runs on the server; you will get a Telegram message when it finishes or if it needs you."); MONEY
(every value from `vast`, none typed by hand); COPIES (`live: Vast · backup: Lab (12 min old, covers the last stop) ·
archive: Drive (2 d old, lean) · sandbox: Lab`). When the status is over 5 minutes old, the LAST KNOWN banner and the
two explanations of the forge's D.4 (device offline, or server silent) appear, with `ssh sail-gpu` then `sprintctl
status` as the way to the truth.

**Panels** (the user's list):

1. **Watch** (read-only, EXPERIMENT). Part H.6: what is running where; plain-language status; learning curves per
   stage; **the live reproduction table** (every published simulated number of Part G.3 beside ours with our
   interval, the band and the status word; the human numbers listed separately as "not simulation targets"); the
   ladder position of every candidate with the missing evidence in plain words; clips of the running policy and of
   the best per stage; the plain-language reason a candidate was killed; per-seed tables; logs and downloads.
   First-screen paragraph, template-built and validated like a card: "So far: 23 candidates run, 7 finished Stage 1,
   2 reached L1 (walking reproduced), 0 at L3. Closest: [candidate in plain words]; it still needs [missing evidence
   in plain words]. Nothing is proven yet."
2. **Steer** (EXPERIMENT; every control "changes the experiment", with a reason field). The queue in the order the
   runner will follow, draggable (reorder), with each candidate's purpose, budget, ETA, version and state; per
   candidate: pause, kill, requeue, edit for next run (a form over the registry choices of Part B.3, showing the
   resulting new version), add seeds (with the post-hoc label explained), change budget; add a catalogue candidate;
   launch a sweep (choose registry choices and options, method, tiers, budget with the wall-clock estimate, seeds, and
   a selection rule from the library, shown in plain words before confirming); stop a sweep; the lane split
   (sliders within the ceilings, with the host view beside them); a read-only list of what steering can never do.
3. **Sandbox** (SANDBOX; "testing only"). The sandbox's own status (running trials, the viewer's state and URL hint,
   idle countdown), its configs, copies, runs, clips and compare views; start or stop a trial run with its budget;
   copy a config or checkpoint in; render; compare; and **Promote**, the one control on this panel that carries
   "changes the experiment" and a reason field, with the validation result shown before confirming.
4. **Ledger** (read-only). Every run (queued, running, done, failed, killed) with its candidate version, seeds,
   backend, budget, the ladder word and the card; every steering action with its reason, source and outcome; every
   Promote with its provenance; every gate or evaluation epoch; rejected and expired commands with their reasons.
   Filter and search; pages on demand; the DOM never holds more than 500 rows.
5. **Needs** (mirrors Telegram). Every open need with its steps and buttons (the same actions as the Telegram
   buttons, through the command channel), and the resolved ones with how they resolved.
6. **Locations and settings.** The map line; Pause, Resume, Stop, Drain; Move to Vast (with the "also move the
   sandbox" tick box), Move to Lab, Cancel move, Destroy Vast; Backup to Drive, Evacuate Lab → Drive, Evacuate Vast →
   Drive, Restore from Drive (→ Lab / → Vast); Emergency stop alone in its own group; destructive commands require a
   typed word (DELETE, RESTORE, KILL). **Host view**: live CPU, RAM, GPU memory and utilisation, and disk, split by
   owner: this programme's experiment lane, its sandbox lane, the forge (`clforge.slice`, read-only), the user's
   other services, and other lab members (by account), with the disk floors of both programmes. **Settings** (each
   with its allowed range, "pending" until confirmed, the worst-case spend where money is involved, ceilings shown but
   not editable): polite mode, resume delay and alert hours; same-account GPU services coexist or pause; disk cap and
   floors; Vast offer policy (CPU jobs by transitions per dollar, GPU jobs 5090-class), max $/h, per-instance and
   monthly caps, credit floor, lease-hours alert, `at_cap`, park-after minutes, parked-destroy hours; mirror interval;
   Drive refresh hours; keep-finished days; clip interval; sandbox idle stop; LLM summaries per day (0–3); after the
   paper gate (park or continue); replication ask or auto; Phase 2 start (Part B.8); alert channel. Gate thresholds
   appear read-only with their epoch history.

**Fixed texts, each with one Playwright test**, as in the forge (token rejected; token cannot see the repository;
server has never published; stale status; rate-limited; first boot: "The runner is measuring throughput and noise
floors and training the first Stage-1 candidates. Stage 1 takes about N hours per candidate on the CPU backend;
there is nothing to judge yet."; this device offline).

### D.5 Worker ↔ controller protocol

As in the forge: `state/desired.json = {run, epoch}` beside the live work state, written and fsynced before any
signal, read by the worker entry point, the Vast supervisor and the guard before every start and before importing
torch; `state/worker_state.json` and `work/runs/<id>/live.jsonl` every 30 s, stamped with the epoch; the controller
pulls them (SSH on Vast) and copies finished jobs into `record/`; SIGTERM = keep the last update checkpoint and exit
within 45 s; SIGUSR1 = checkpoint now and continue; a single-worker lock plus the lease record; checkpoints atomic
(`write tmp → fsync → rename → fsync dir`), with a manifest of sha256 and `worker_epoch`, falling back to the
previous checkpoint if the latest is damaged; **checkpoints are never pickles** (`safetensors` and JSON; a unit test
greps the resume path for `torch.load(`, `pickle.load`, `weights_only=False`, `allow_pickle=True`); anything that has
been on a rented host is untrusted data when it returns (`rsync --safe-links --no-devices --no-specials`, strict
schemas, staging only; code a lab worker runs always comes from the lab's own git objects).

### D.6 Vast.ai worker policy

- **Verify the CLI and API against the current Vast documentation and `vastai --help` before writing the
  integration** (`vastai` 1.8.0 is installed at `~/.local/bin/vastai` by the forge build; use it read-only for the
  forge's purposes and with this programme's own label for ours). The account is the shared team account "UGRP Exp"
  (id 577762); its key is at `~/.config/vastai/vast_api_key`. **Only instances labelled `smatsprint-` are ever
  listed for action, started, stopped or destroyed (I10).** Never list-and-kill.
- **Offer choice by what the job needs.** CPU-physics work (the default until the GPU backend is certified) is
  chosen by **measured transitions per dollar**: an offer's expected throughput is estimated from its effective CPU
  cores and CPU RAM against the per-environment memory and per-core rate measured on the lab (Part C.11), then
  replaced by the rate measured on the first job of each rental; the ranking is `transitions/s ÷ dph_total`,
  subject to RAM for the declared environment count. GPU-backend work uses RTX 5090-class offers (sm_120 parity with
  the lab). Mixing hardware classes within one comparison's seeds is forbidden (the worker records host, CPU and GPU
  per seed; the runner refuses cross-class comparisons). Filters (`ops/vast/offer_filter.json`, editable from
  Settings; verify every field name with `vastai search offers --help`): `num_gpus=1`, `verified=true`, reliability
  ≥ 0.95, on-demand only (interruptible is forbidden: it would violate I4 without warning), disk ≥ 60 GB, a driver
  that runs the pinned CUDA wheels, `dph_total` ≤ the setting and never above `limits.toml`, caps on bandwidth and
  storage prices, rental duration ≥ 7 days. Vast stops an instance at the offer's end date, so the controller shows
  it and acts 6 h before (D.2 `lease_cap`).
- **Renting is idempotent and counted**: the lease file first, its id in the label `smatsprint-<lease_id>`; before
  every create and every retry, list instances with that exact label and adopt one that exists; at most one billable
  instance with the prefix; rentals per 24 h capped by `limits.toml`; orphans with no worker ever started are
  destroyed at reconciliation; instances that ever ran a worker are only reported. Rehearsals use their own lease
  (`max_hours=2`, `max_usd=5`) and a dead-man switch (`systemd-run --user --on-active=3h sprintctl destroy-labelled
  smatsprint-rehearsal-`).
- **SSH** uses a dedicated key pair for workers only (`~/.config/smatsprint/vast_ssh_ed25519`), attached per
  instance (never to the shared account's key list), `authorized_keys` rewritten to that one key after
  provisioning, `-o ForwardAgent=no -o IdentitiesOnly=yes -o UserKnownHostsFile=state/known_hosts/<instance_id>
  -o StrictHostKeyChecking=accept-new`; every connection starts from the lab.
- **Image**: a CUDA base image whose tag is verified in M5 (the forge verified
  `nvidia/cuda:13.0.2-cudnn-runtime-ubuntu24.04` on 2026-09-22; re-verify); onstart installs `uv` and `vastai`,
  receives the code archive from the lab, `uv sync --frozen --no-install-project`, writes no credential, starts the
  supervisor and the guard. The first job on a new host is the smoke plus a short physics parity check against the
  lab's stored reference trajectory (same seed, same actions), so a broken host is caught before it burns a lease.
- **Lease and billing** exactly as the forge: `max_hours` (default 48, an alert threshold), `max_usd` (default 60),
  the monthly cap (default USD 150), `credit_floor_usd` (default 5); GPU time, storage (which continues while
  stopped) and bandwidth are all billed; `cost_so_far` uses billed figures where the API has them; checked every 5
  minutes; 90 % alerts; 100 % runs `lease_cap`.
- **Worker self-guard** (`ops/vast/worker_guard.py`, own process group, no user credentials) stops the instance
  itself with the instance-scoped key Vast pre-installs (`vastai stop instance $CONTAINER_ID`) at 90 % of the local
  money cap, after `lab_silence_stop_h` (default 6) without the controller, or after 30 minutes of an empty queue with
  a silent controller. The rehearsal proves the self-stop and that this key cannot touch other instances.
- **G5 second-machine reproduction** runs through `run_replication` (D.2); no second worker is ever started for it.

### D.7 Google Drive archives (emergency space, and a third copy)

- The programme's own rclone config, `RCLONE_CONFIG=~/.config/smatsprint/rclone.conf`, remote `smatsprint-gdrive:`
  with **scope `drive.file`** (rclone sees only the files it creates). Authorisation follows Part N.7 (device flow
  from the phone if Google allows `drive.file` on it; otherwise one PC-only need). The user needs their own OAuth
  client (rclone's shared client is being retired during 2026, per rclone's documentation checked by the forge on
  2026-09-21; re-check); **the consent screen must be "In production"** (in "Testing", Google expires the grant after
  7 days and the emergency evacuation would fail exactly when needed); its homepage and privacy links point at the
  Pages site's `privacy.html`. The forge's future rclone setup is separate and untouched.
- **Token health is monitored**: `rclone about smatsprint-gdrive:` daily and before offering any Drive button; a
  failure disables the Drive buttons with the reason and raises `drive_token_dead`.
- **Space first.** A free Google account has 15 GB; the user's quota is unknown (`00_README.md` asks). The dashboard
  shows free space beside the estimated archive size and refuses an archive that would not fit, offering the lean
  one. **Lean archive** (the default) = everything that cannot be regenerated bit for bit: record state (ledger,
  registered configs, results, curves, kept rollouts), the work queue, `work/refdata/`, the latest verified
  checkpoint of every unfinished run, every stage-final checkpoint that a candidate at L1 or above uses, and the
  claim-backing rollouts. Typically well under 5 GB here, because the networks are small. **Full archive** adds every
  remaining checkpoint, rollout, clip and log. The sandbox tree is archived only if ticked.
- Folder `SMATSPRINT-archives/<archive_id>/`, `archive_id = <utc timestamp>-<location>-<git short sha>-<lean|full>`;
  `tar --zstd` under `nice -n 15 ionice -c3`, split into 1.9 GB parts, `SHA256SUMS` and `MANIFEST.json`; upload with
  `rclone copy --checksum --transfers 4 --retries 5`; verify with `rclone check` and `rclone checksum sha256` before
  anything may be deleted; keep the two newest verified archives.
- **From a Vast worker** the Google token stays on the lab (I9): build the parts on the paused worker's disk, then
  from the lab `ssh worker 'cat <part>' | rclone rcat --size <bytes> smatsprint-gdrive:…` one part at a time with
  our own per-part retries; verify on Drive; only then destroy. If the worker has no room, the single-stream fallback
  of the forge's D.7 with whole-stream and per-part verification.
- **Restore** into a fresh staging generation, verify, swap, `uv sync --frozen`, PAUSED; **cold restore** from
  nothing but GitHub and Drive is a documented, tested path.

### D.8 Alerts ("call the user when")

Alerts go through the bridge (Part N.5) as messages, or as needs when the user can act, with the `[SMAT-Sprint]`
prefix and the lane tag; Gmail is the fallback. One per condition per hour; a daily digest for the rest.
Conditions: a candidate crossed a ladder level (L1 and up); a claim reached the paper gate; a candidate failed or was
quarantined; every need; a move, backup or evacuation finished or failed; a command rejected for age or a changed
state; a polite pause started, then every `polite_alert_hours`; the machine idle more than 15 minutes with queued
work; disk within 5 GB of `min_free_gb` on either host; Vast lease hours at `max_hours`; Vast cost at 90 % of a cap or
credit under the floor; a Vast instance paused and still billing; a parked instance 6 h before its automatic destroy;
the offer's end date within 6 h; a gate or evaluation epoch opened; the "modified outside the steering API" flag
(Part H.4); a dashboard token within 14 days of expiry; a controller, runner, bridge or wrapper restart; any heartbeat
missing for 10 minutes (from the independent watchdog timer); **the lab silent for 45 minutes (from GitHub, not from
the lab)**.

**One alert path that does not run on the lab.** `.github/workflows/deadman.yml` on `main` runs hourly at an
off-peak minute (for example `23 * * * *`), with only the built-in `GITHUB_TOKEN` (`contents: read`, `issues: write`),
no secret and no project code. If the `status` branch is older than 45 minutes it opens (or comments on) one issue
`[SMAT-Sprint] lab silent since <time>` assigned to the owner, whom GitHub e-mails, adding "a Vast instance may be
billing" when the last location was VAST; it closes the issue when the status is fresh again. Commit it through the
deploy key in M2 and make it fire once on purpose to prove delivery. (The M0 secret-drop issues are titled
`secret-drop …` and are ignored by this workflow.)

### D.9 Documents the programme keeps current without anyone asking

- `docs/weekly/<year>-W<week>.md` (Part C.14), in the KB's status vocabulary, with the user's steering decisions.
- `ledger/ladder.json` and `ledger/paper_gate.json`, regenerated from the live ledger on every harvest.
- `status.json` and the files beside it on the `status` branch, including the glossary; the same text feeds
  `sprintctl status` and the bridge's `/status`.
- `docs/HANDOFF.md`: how everything runs, how to stop it, move it, reproduce a result, and the exact state at the
  last milestone; one file, rewritten at every milestone end. Build progress lives in `docs/PROGRESS.md`.
- `docs/HOP_IN_HOP_OUT.md` (Part H.10), re-tested whenever a command it documents changes.
- `docs/paper/` and `docs/REPRO.md` (Part C.14) once a claim reaches L3.
