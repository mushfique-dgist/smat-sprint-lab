## PART E — Testing, acceptance, milestones and stop points, handoff, anti-patterns

### E.1 Testing philosophy

Nothing is deployed until it has been attacked. The user asked for no bugs or errors in anything they will press, so:
every state transition has a test that runs the real code path (with a dummy experiment and, where money is
involved, the cheapest real Vast instance for a few minutes); every invariant (I1–I10 of Part D.2, LI1–LI10 of Part
H.11, the needs invariants of Part N.2) has a test that tries to violate it; the state machine is tested as a model
against thousands of random command-and-failure sequences with fake Vast, Drive, Git, Shell and Telegram back ends;
every dashboard control has an end-to-end browser test; every command in the user's guide is executed by a test; a
chaos script runs weekly after handoff and reports on the dashboard. Tests live in `tests/` and run with `pytest`;
browser tests use Playwright. A red test blocks its milestone and keeps the control it covers disabled. Write tests
that assert what Parts D, G, H and N promise, not what the code happens to do.

### E.2 The test matrix (each group gates what it covers; all green before the final handoff)

**Needs and bridge (CPU; gates M0).** The whole N.11 list against the fake Bot API server, the secret-drop tests,
and the wrapper tests; then the real-bot smoke of N.9 step 7.

**Unit (CPU, seconds; gates M1).** Config and registry schema (every registry choice has options, a default and a
note; every catalogue config validates); registration (a registered file is read-only and its hash is recorded;
an edit makes version v+1); ledger and steering hash chains (append, verify, a tampered row breaks the chain);
job identity (a docs-only commit leaves it unchanged; a science change changes it); seed pools disjoint; the reward
terms of Part B.2 on hand-computed states (each term, each stage weight); the Stage-4 exo-reward optimum (for
|w| ≤ 0.8 the maximiser of the instantaneous term is u = w; at |w| = 1 it is about 0.814); observation builders
(shapes, ordering, the exo actor's 18 inputs and their three-sample history); action mappings (clip, squash, the
[0,1] excitation range); the velocity-proportional and phase controllers (Part B.6) on synthetic traces; checkpoint
round trip including simulator states; the "no pickles" grep; command parsing and hostile-input rejection (shell
metacharacters, oversized fields, unknown commands, out-of-range settings, missing reasons); schema/control parity;
lease arithmetic; archive manifests; card validator and ladder words; glossary coverage; every need raise site uses
a registered code; `systemd-analyze --user verify` with no warnings.

**Gate (CPU, seconds; gates M1).** `gate/check_gate.py` against synthetic ledgers, one suite per path of Part G.7:
a clean L1, L2, L3, L4 and L5 each pass; a clean reproduction-path, mechanism-path and benchmark-path paper gate each
pass; and **each single violation fails alone**: a band edited after a result exists, a claim judged on post-hoc
seeds, a checkpoint chosen by the reported metric, an evaluation on a training seed, unmatched transitions or torque
budget between arms, a comparison across backends or hardware classes, a failed seed dropped from the pool, a
suspect row counted, an eval-hash or gate-hash mismatch, a Promote config counted without its provenance, a sandbox
artefact referenced by a job, an ablation run on a different S2 checkpoint than its SMAT arm, a GPU-trained policy
evaluated on the GPU backend. Run twice on the same ledger, byte-identical output. The runner refuses to start, and
`check_gate.py` refuses to run, on a `GATE_HASH` mismatch.

**Trainer correctness (CPU/GPU, minutes; gates M1).** PPO reaches the reference return band on a standard
continuous-control task within a fixed budget; a frozen actor's weight hash is identical before and after its
stage; a frozen actor receives no gradient; masked log-probabilities; the exo actor sees exactly its 18 inputs
(input-gradient probe); stage transitions follow the registered rules; resume from checkpoint gives bit-equal
parameters on the CPU backend.

**Integration (CPU and GPU, minutes; gates M1).** The smoke of every registered job kind; a tiny full pipeline
(S1→S2→S3→S4 plus evaluations, a few hundred thousand transitions) end to end through outbox → worker → `record/` →
harvest → ledger → ladder → `status.json` (this is L0, Part G.2); **Pause holds** (desired state written before any
signal; after an acknowledged Pause and after an emergency stop the worker unit stays inactive for 10 minutes with
no new restart, and no process of the experiment slice is on the GPU or burning CPU); `kill -9` of a running worker is
restarted and resumes; 100 alternating pause/resume commands never leave the unit in `start-limit-hit`; **GPU and
CPU ownership fixtures** (fake `nvidia-smi` and process tables): another account's process above the threshold →
polite pause within 60 s naming the owner, automatic resume only after the quiet period; a forge process or
`llama-swap` growing mid-run → no pause, the packer shrinks its budget, an out-of-memory adds no strike; **host
fences**: a job that allocates past its declared RAM dies alone as `host_oom`; the worker refuses a job when free
disk is under the floors.

**Crash consistency (CPU and GPU; gates M1).** Kill worker processes with SIGKILL at 50 random moments (during
rollout, update, checkpoint write, evaluation, results write, queue rename); every time the job resumes, its
parameters equal a never-killed twin's at the same update (CPU backend), and the ledger has no duplicate or
half-written row. Kill the runner during harvest, planning and git commit the same way. Also a full disk, a corrupt
latest checkpoint (falls back to the previous one and says so), a clock jump, a missing reference file. **The
cold-start drill, instead of a reboot** (Part R.2).

**State machine as a model (CPU, minutes; gates M2, and the Vast and Drive transitions of M5 and M6).** As in the
forge: the full `(state, command)` table (every D.2 command, every H.5 steering action, Promote, every settings key,
`register_device`, `drop`), each pair a defined transition or a plain rejection; stateful property tests with random
command sequences interleaved with random back-end faults (fail, hang, stale data, succeed-but-lie) and controller
crashes at every step, asserting I1–I10 and LI1–LI10 after every step; every shrunk counterexample kept as a
regression test; `actions[].enabled` equals "the state machine does not reject"; pause, cancel and emergency stop
injected at every step of every transition; a Vast instance stopped behind the controller's back; a partitioned
instance returning after its replacement; a create call that times out after the fake accepted it; foreign instances
under other labels (never touched); evacuate + restore preserving the set of registered configs, stage-final
checkpoints and queue entries; a lease cap reached with the lab free and busy.

**Controller chaos (real code, fake money; gates M2, M5, M6).** As in the forge: the controller killed at every step
of every transition and between the three steps of the atomic swap; command storms; stale inboxes (a 6-hour-old
inbox with move + resume + evacuate changes nothing and raises one alert); two devices with skewed clocks ordered by
the `control` branch's commit order; a 3-hour GitHub outage during which dashboard commands are written and
`sprintctl` is used locally; rsync interrupted at 30, 70 and 99 %; an injected checksum mismatch; the manifest-driven
mirror under checkpoint rotation; a hostile worker returning a pickle, a symlink to `~/.ssh` and a result with extra
fields; host loss mid-run; Drive too small; a Drive upload interrupted at part k; the watchdog under a long transfer
and a real deadlock.

**Lanes (CPU and GPU; gates M3).** The LI1–LI10 tests, the isolation fuzzer and the acceptance rehearsal of Part
H.11; the jail's permission tests (from inside the jail: write, rename, symlink, hard-link, chmod on every experiment
root fail; `~/.config/smatsprint/`, `~/.ssh`, `~/.codex`, `~/.config/gh`, `~/.config/ugrp-forge/` and the forge
project are invisible); the VRAM watchdog; the viewer rejects requests without its token; Promote's validator
against every rejection class.

**Guide (gates M3).** `tests/guide/test_guide.py` (Part H.10): every `bash` block executed against a throwaway
instance, every `powershell` block linted for PowerShell 5.1 and its `ssh` line executed; no untested command.

**Backend parity and throughput (GPU; gates M4).** The parity gates of Part B.5 (physics parity, learning parity,
evaluation on the reference physics), the feature-support canary, and the throughput table; a certificate is issued
only when all pass, and a job requiring the GPU backend cannot run without a valid certificate for its model and code
identity.

**Migration rehearsal (real money, small; gates M5 and M6).** One detached script drives every hop through
`sprintctl`, asserts after each, writes `tests/rehearsal_report.md` and notifies once. It runs from its own checkout
with its own `state/` root, queue and lease under `smatsprint-rehearsal-*`, pausing the live runner only for hops that
use the lab machine. Before renting it arms the dead-man switch (`systemd-run --user --on-active=3h sprintctl
destroy-labelled smatsprint-rehearsal-`). Lease `max_hours=2`, `max_usd=5`. With a dummy job that writes a
recognisable counter every 30 s: LAB → VAST → pause/park → resume → LAB → VAST → DRIVE → LAB, then DRIVE → VAST with
the lab staging directory read-only; at each hop verify the counter continued without a gap larger than one update,
the hashes match, old copies were replaced or deleted exactly as D.2 says, the instance was destroyed and confirmed
absent, no credential was left on the worker (scan before destroy), and the dashboard showed the right banner. Also:
the guard's self-stop with the lab link blocked; the instance key cannot touch other instances; `vastai copy` from a
stopped instance; whether `nvidia-smi` lists PIDs inside the container. Record timing and cost per hop. Budget ≤ USD
5; when the script ends no `smatsprint-rehearsal-*` instance exists.

**Dashboard end to end (Playwright; gates M2 and each later control).** Against a local fake of the GitHub API
(sending the real API's CORS headers, recorded with one curl in M2) and once against the real repository: desktop
and phone viewports; token entry with PIN encryption, persistence, wrong and expired tokens; every fixed text; every
control of D.4 with its dialog text, its reason field where it changes the experiment, its typed word where
destructive, and its disabled-with-reason state for every precondition; a control whose tests are not green shows
"not built yet"; Pause and Emergency stop enabled on stale status; the command file written with the right schema,
`based_on` and reason; the lane banners and chips on every panel; the reproduction table's numbers equal the
ledger's; 20,000 runs across 40 pages with the first screen interactive in under 3 s on a throttled phone profile;
the status branch size budget; the hostile-status test (every string an injection attempt renders as text, no
request leaves for any host but `api.github.com`); nothing in `gh-pages` matches a data or secret pattern or any
research keyword; `drop.html` makes no request except to `api.github.com` and never to GitHub with the plaintext.

**Security (gates M2; the jail gates M3).** No secret in the repository, the status branch, `gh-pages`, a command
line, a unit file or a journal excerpt (pattern scan as a test and as a pre-push hook); rulesets tested with the real
dashboard token (D.3); the deploy key is the only GitHub credential on the lab after M2 and the build's `gh` session
in `~/.config/smatsprint/gh` is logged out while the forge's `~/.config/gh` is untouched; a settings command above a
`limits.toml` ceiling and a gate change through the mailbox are rejected; hostile inbox files cannot reach a shell;
the bridge never loads another bot's token.

### E.3 Acceptance checklist (each line tagged with the milestone that turns it green; paste the filled copy into `docs/HANDOFF.md`)

- [ ] (M0) The needs store, CLI, bridge, secret drop and wrapper pass their tests; the programme's own bot is live;
      the user tapped a real button; the wrapper launched M1.
- [ ] (M1) `uv sync --frozen` on a clean clone works on the lab; `ops/scripts/doctor.sh` is green.
- [ ] (M1) `gate/` is frozen for every path of Part G.7 and passes its synthetic-ledger suite; `eval/` is frozen;
      `GATE_HASH` and `EVAL_HASH` are verified at runner start and by the daily doctor.
- [ ] (M1) L0 reached: the tiny four-stage pipeline ran end to end with actor freezing verified by weight hashes,
      and the reference motion, body model and device model recorded by hash.
- [ ] (M1) Controller, runner, bridge, wrapper and the watchdog timer enabled; the worker unit installed but not
      enabled; lingering confirmed; the cold-start drill passes; the pre-loaded campaign is running and `/status`
      answers on Telegram.
- [ ] (M2) Dashboard live on Pages; the user entered a token on the PC and on the phone and pressed Pause and Resume
      from the phone; the GPU and CPU were verified free within 90 s and the phone showed it within 120 s; the
      off-lab dead-man alert fired once on purpose and reached the user; the build's `gh` session is logged out.
- [ ] (M3) The sandbox is ready with the day-one contents; the viewer works through the SSH tunnel; the guide passes
      its tests; the acceptance rehearsal report is green; the user opened the viewer once (a phone need asked).
- [ ] (M4) The GPU backend certificate exists (or a documented, evidenced reason why not, and the programme
      continues on CPU); the throughput table is on the dashboard.
- [ ] (M5, M6) The rehearsal report exists with timings and cost; no `smatsprint-rehearsal-*` instance exists; the
      Move, Destroy, Backup, Evacuate and Restore buttons are enabled only where their hop is green.
- [ ] (final) All tests of E.2 pass; `docs/HANDOFF.md`, `docs/HOP_IN_HOP_OUT.md` and `docs/USER_ACTIONS.md` are
      current; secrets only under `~/.config/smatsprint/`; nothing of the forge was touched.

### E.4 Milestones and stop points

Work straight through. End a session only when one of three things holds, and then give the E.7 report as the final
message (the wrapper sends it to the user):

- (a) the next step needs something only the user can do, it is already a need on their phone, and nothing
  independent is left to build;
- (b) everything left depends on a detached job with more than ten minutes to run;
- (c) a milestone is complete.

**Waiting, exactly.** Up to about 10 minutes: one foreground blocking tool call with an explicit timeout. Longer:
`ops/scripts/detach.sh <name> [--gpu-work] -- <command>` (a transient `systemd-run --user` unit, because a
`setsid nohup` child of a sandboxed shell inherits the sandbox and has no GPU and no network; the forge proved this
recipe on this machine), which writes a pid file, a log, an exit-code file and a progress file under
`state/detached/<name>/`, and on exit sends one Telegram message through the bridge ("[SMAT-Sprint build] (job name)
finished OK in 3 h 12 min"; no reply needed; the wrapper or the next session picks it up). Never `sleep` in a loop,
never repeated reads of `tail` or `nvidia-smi`, never "I will check again in a minute". Anything with several slow
hops is one detached script that asserts after each hop, writes its report and notifies once. Logins and anything
else that waits for the user are needs (Part N), created the moment the code or link exists; then take the next
independent task.

**The machine does science from the first day of M1.** Order M1 so that throughput calibration and the first
Stage-1 candidates run as detached jobs as soon as the environment and the trainer pass their smoke and crash tests,
under the `sprintctl pause` that M1 provides, while the rest of M1 is built.

**Phase 0 — read and plan (≤ 2 hours).** Read `00_README.md` (its defaults and open questions), this prompt once in
full, then `02_RESEARCH_DIRECTIONS.md`. Open `01_PAPERS.md` and `03_PAPER_DIGESTS.md` only by cluster or paper when
you need them. Probe once and record in `docs/PLAN.md`: `nvidia-smi` and a one-line torch CUDA check from your shell
and from a `systemd-run --user` unit; `systemctl --user status` and the forge's units (read-only); the delegated
cgroup controllers; bubblewrap with CUDA (a jailed `nvidia-smi`); EGL off-screen rendering of the composed model; the
`codex exec` canaries for the builder profile and the summary profile (Part N.8, C.13); disk, RAM and the free-space
floors; the tailnet peers (is the phone there now?); that `dgist-course-telegram` long-polls the shared bot (so the
programme only sends through it). Write `docs/PLAN.md` (build order, risks, pinned versions, the chosen `codex exec`
lines, ports reserved in 8800–8809 after `ss -ltn`, your harness's maximum tool-call time) and create
`/home/aurnab/projects/smat-sprint` with a local git repository; the first commit copies this prompt, the README,
`01_PAPERS.md`, `02_RESEARCH_DIRECTIONS.md`, `03_PAPER_DIGESTS.md` and `research-data/` into `docs/spec/`, plus
`AGENTS.md` and `docs/PROGRESS.md` (E.9).

**M0 — Needs, bridge, secret drop, wrapper** (Part N; the bootstrap order of N.9). Exit: the Needs-and-bridge group
green; the programme's bot live and verified; the private repository and the Pages shell with `drop.html` exist; the
wrapper is armed for M1. Send the user the `sprintctl pause` line and the `/pause` command before any job runs.

**M1 — The experiment lane on the lab, and the campaign running.**
- The composed Phase 1 model (Part B.2) with its hashes; `smatsprint/envs/walk26.py` on the native CPU backend; the
  reference-motion loader; the device model with the stage torque scales; the registry of choices (Part B.3).
- The trainer (Part C.8) with its correctness tests; the stage pipeline with freezing verified by weight hashes.
- `eval/core` and `eval/protocols` (Part C.9, Part G.3), then **freeze `eval/`**; `gate/` complete for every path
  (Part G), then **freeze `gate/`**, both before the first registered result.
- The runner, worker, controller, the file queue, `record/`, the 60 s record copier, the ledger with hash chains,
  registration, the catalogue and `campaign.yaml` (Part B.7), cards, `sprintctl pause|resume|status|exp …` with the
  GPU-and-CPU-free check and polite mode, the out-of-band edit watcher (Part H.4 layer 4), the host-resource fence.
- The four enabled units and the watchdog timer; the worker unit installed but not enabled.
- Throughput calibration on the CPU backend (Part C.11) and L0 (the tiny pipeline).
- Exit: the Unit, Gate, Trainer, Integration and Crash groups green, including the cold-start drill; L0 recorded;
  then **start the pre-loaded campaign** and leave it running. `/status` works from the phone.

**M2 — Dashboard, steering and command channel.** The controller as the pure state machine with fakes and
model-based tests; the command channel; status publishing (including the reproduction table, ladder, clips, needs,
host view); the steering API complete (Part H.5) with the Steer, Watch, Ledger, Needs and Locations-and-settings
panels; alerts and the dead-man workflow (fired once on purpose); the two rulesets; the glossary and fixed texts;
PIN-encrypted token storage; then `gh auth logout` for the build's own `gh` config. Moves and Drive buttons visible
and disabled ("not built yet"). Exit: the State-machine, Controller-chaos, Dashboard and Security groups green; a
phone need asked the user to press Pause and Resume from the phone, and it worked within the targets. At the end of
M2 send a pick-one need: "Next: the sandbox (recommended, the tool you asked to use most) or the GPU physics track?";
default: the sandbox.

**M3 — The sandbox lane and the guide** (Part H). The jail, the sandbox slice and VRAM watchdog, the sandbox API and
CLI, the interactive viewer, render and compare, Promote, the day-one contents, `docs/HOP_IN_HOP_OUT.md`, the Lanes
and Guide groups, and the acceptance rehearsal. Exit: those groups green, the rehearsal report green, the Sandbox
panel enabled, and a phone need that invites the user to open the viewer once (with the exact PowerShell line).

**M4 — The GPU physics track** (Part B.5). The MuJoCo Warp backend behind the environment interface; the feature
canary; physics parity; learning parity; evaluation on the reference physics; the throughput table; the certificate.
Then re-plan the campaign's remaining blocks on the certified backend (a pick-one need showing the new estimates).
Exit: the Backend-parity group green, or an evidenced negative with the programme continuing on CPU.

**M5 — Vast.** Pure state machine, fakes and model-based tests first (they need no money and may be written any
time); then the real integration (offer choice by transitions per dollar, rent, provision, sync, launch, monitor,
mirror, park, restart-or-replace, destroy, leases, the guard); then the scripted rehearsal. Move and Destroy turn on
when the rehearsal is green.

**M6 — Drive.** Authorisation by Part N.7; archive, evacuate, restore, lean and full, streamed from Vast; cold
restore from GitHub plus Drive; the DRIVE → VAST rehearsal hop. Backup, Evacuate and Restore turn on when green.

**M7 — Built when needed.** The paper-package writer, the weekly note (start it in M1 as a simple template if easy),
the optional LLM summaries, the monthly arXiv novelty re-query (UniExo and its successors included; Part G.6), the
weekly chaos drill, and optional Mode B. Build when a claim reaches L2 or when M1–M6 are green, whichever is first.
None of these touches `gate/` or `eval/`.

**Unattended operation.** From M1 the runner runs by itself. After the last milestone the wrapper goes to DONE and no
Codex session runs until the user starts one (for example to review a paper draft). A session opened later follows
E.9.

### E.5 Sudo, installs, and everything else that needs the user

- **User space first, always:** `uv` tools, Python wheels (including CUDA wheels), static binaries in `~/.local/bin`,
  Playwright's browser download, user systemd units, EGL rendering through the NVIDIA driver's libraries. The forge
  build already installed `gh` 2.101.0, `rclone` 1.75.1, `vastai` 1.8.0 and ShellCheck into `~/.local/bin` and
  bubblewrap with its AppArmor profile system-wide (verified 2026-09-23); reuse the binaries, never their configs.
- **Root, only if user space is impossible**: one idempotent script `ops/root/<date>-<purpose>.sh` (`set -Eeuo
  pipefail`, an ERR trap printing `FAIL <step>`, every action through a `step` wrapper printing `PASS <name>`, stops
  at the first failure, lists what did not run, touches nothing outside its purpose); prove it parses (`bash -n`,
  `shellcheck`) and dry-run its non-root parts; then a **PC-only need** (`root_needed`) that says in one sentence what
  it does and why user space was not enough, and gives the one line
  `sudo bash ops/root/<script> 2>&1 | tee -a state/root/<script>.log`. Carry on with everything else; read the log
  when you reach the step that needs it; the check `sudo_script_ok` resolves the need. Never ask for, store or echo
  the password; never over Telegram; never a sudoers rule. Expected: none (bubblewrap is already set up).
- **The user's accounts** (GitHub login, dashboard tokens, the bot, Drive, Vast credit, paywalled PDFs, decisions):
  always needs, phone-doable wherever a flow allows (Part N.7), sent the moment they are live, mirrored in
  `docs/USER_ACTIONS.md`, and never waited on.
- **Papers:** almost everything in `01_PAPERS.md` is open access. If a paywalled paper is needed, create a phone need
  asking the user to drop the PDF into `docs/papers_pdf/` (the user has a DGIST login and will fetch it); never
  automate a library login.

### E.6 Anti-patterns (each of these ended an earlier attempt; do not repeat them)

- Being the loop: goal mode, thread goals, auto-continuation pings, staying alive to watch a run, a transfer or a
  rental. Detach, notify, stop.
- Narrating a file transfer a gigabyte at a time.
- Audits, decks, viewers, coverage ledgers, receipts, seals or revision-numbered notes instead of runs. Git, the
  ledger and the tests are the audit trail; one `HANDOFF.md`, rewritten.
- A week of infrastructure before the first experiment; a critical path that stalls whenever the user is not at the
  keyboard.
- Printing a one-time code in a terminal and waiting for the user at the PC, when a Telegram message with the link
  and the code would do. Asking for a password over Telegram.
- Specification and security spirals with nothing executed on the server.
- A novelty filter that kills every direction before it is tested. Occupied territory is a comparator to add.
- Tuning until the paper's number appears. Bands are fixed first; the number is what it is.
- Pooling participant counts, or relabelling walking results as sprint results.
- A loop that decides the research for the user: nothing proposes or launches experiments on its own.
- A sandbox that quietly becomes the experiment, with untracked tweaks leaking into results.
- Running one seed and writing a page about it; calling a screening number a result; reporting an unmatched
  comparison without the words "not comparable".
- Touching the forge: its units, slices, files, bot, `gh` session, Vast instances or disk margin.

### E.7 Reporting style (the final message of every session; the wrapper forwards it)

Lead with the outcome and what needs the user (it is already a need on their phone; the report repeats it, it does
not replace it). In the first report, list the defaults assumed. Then: what exists now (paths), what was tested
(numbers of tests; rehearsal cost), what is running detached (names, ETA, how the user will be notified), what the
next session will do. Plain language, short sentences, no receipts. If something failed, say so first with the error
text in a code block.

### E.8 First actions, in order

1. Read `00_README.md`, this prompt once, then `02_RESEARCH_DIRECTIONS.md`. If this is not the first session, follow
   E.9 instead.
2. Confirm you are not in goal mode and no thread goal is set.
3. Re-verify the environment facts of Part A.4 you will rely on (one command each) and run the Phase 0 probes.
4. Write `docs/PLAN.md`, create the project directory and its first commit (E.9).
5. Start M0 in the order of Part N.9. The first need (GitHub login) should reach the user's phone within the first
   hour.

### E.9 Working across many sessions

- **The spec lives in the repository** (`docs/spec/`, copied in the first commit; the handoff folder is read-only).
  Where code enforces a rule, cite the Part in a comment (`# Part H.4 layer 3`).
- **`AGENTS.md` at the repository root**, at most 60 lines: first, "If your prompt arrived on stdin from
  `runner/summaries.py`, you are a bounded summary call: ignore this file and follow only that prompt."; then the rules
  of Page one; "read `docs/PROGRESS.md` next"; the map from component to governing Part; absolute paths of `uv`, the
  venv, the project, the sandbox tree, `docs/spec/` and the secrets directory; the waiting rule of E.4; "create needs
  with `sprintctl need create`; never wait for one".
- **`docs/PROGRESS.md`**, one file rewritten in place with these sections only: *Current milestone and task* (one
  line, with the governing Part), *Done* (one line each, with the test that proves it), *Next* (ordered, at most 10),
  *Detached jobs* (name, pid file, log, started, ETA, what to do with the result), *Open needs* (ids and titles only;
  the needs store is the truth), *Red tests / open bugs*. Update it before every end of session and whenever a
  detached job starts.
- **Every session after the first is launched by the wrapper** with the standard continue prompt (Part N.8) and
  starts by reading `AGENTS.md`, `docs/PROGRESS.md` and the governing Part. Before launching anything, check
  *Detached jobs* against live pid files so a running job is never started twice.
- **User decisions:** `00_README.md` lists the defaults and open questions; the user answers through needs or by
  editing the README. Unless they have, use the defaults and do not ask again.
