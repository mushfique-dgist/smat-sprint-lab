# What was done with each finding of the adversarial review

Six lenses reviewed the master prompt on 2026-09-23 (the lens files are beside this one). Every finding is
listed with its severity, the first sentence of its problem, and what was done. Where a status names a part,
the fix text is in that part of `parts/` and in the assembled `CODEX_MASTER_PROMPT.md`. The canonical names
and numbers the editors used are in `DECISIONS_FOR_APPLYING.md`.

## Telegram bridge attack (TB): 29 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| TB-01 | critical | Until N.9 step 6 no process runs the bridge loop, yet the bootstrap depends on it. | applied: N.9 (bridge in send-only mode from step 2, wrapper in BOOTSTRAP, 24 h fallback to M1a), E.8 step 0, README step 3 |
| TB-02 | critical | During the bootstrap the notifier sends through the DGIST bot 'with no buttons' (N.9 step 2). | applied: N.3 (send-only reissue schedule without a cap, quiet hours), N.9 |
| TB-03 | critical | The only guard against a second session is 'a flock plus a check that no smatsprint-codex-* unit is active'. | applied: N.8 launch rule (d) (armed_by, rollout cwd check, build hold), N.9 step 9, E.9 |
| TB-04 | critical | The launch rule has no notion of what the ended session is waiting for. | applied: N.8 (end.json, launch conditions (e)–(g), capped back-off, usage-limit events, build_sessions_per_day), E.4 |
| TB-05 | critical | The recommended Option 1 runs codex exec with --dangerously-bypass-approvals-and-sandbox as user aurnab, with no outer boundary. | applied: N.8 build jail and launcher, canaries, honest decision text, options 0–2 |
| TB-06 | major | Codex loads rules from the rules/ directory of every active config layer, including the user layer ~/.codex/rules/. | applied: N.8 (rules only in the project's .codex/rules, config hashes checked) |
| TB-07 | major | Build sessions run inside smatsprint-ctl.slice. | applied: N.8 smatsprint-build.slice, C.2 record root outside the dev tree, H.4 layers 4 and 9 |
| TB-08 | major | Text from outside the programme reaches two trusted consumers, and nothing separates data from instructions. | applied: N.8 (ids-only continue prompt, inputs.json), N.4 (labelled external text, PC-line registry) |
| TB-09 | major | The owner filter and the dedupe key are written for messages. | applied: N.5 (message and callback rules, dedupe by update_id, Done bypass, closed-need answer) |
| TB-10 | major | A bare reply is bound to 'exactly one open need that expects a text-like reply' at the moment the bridge processes it, not to the message the user was looking at. | applied: N.5 text replies (reply-to binding, ForceReply, consequential needs, unique short ids, edits, forwards) |
| TB-11 | major | Need files are written by writing a temporary file and renaming it, which does not give compare-and-set. | applied: N.2 (request files, versions, snoozed sub-state, pending_action), N.5 (flows as adopted units) |
| TB-12 | major | Two promises have no mechanism behind them: 're-adopted, never launched twice' and 'processed exactly once (its ended_at file is the marker)'. | applied: N.8 (LAUNCHING state, file stdin/stdout, ExecStopPost, RuntimeMaxSec, cap message) |
| TB-13 | major | The wrapper's buttons (continue, pausebuild, report) bypass the need machinery. | applied: N.8 build_milestone need and /build commands, N.5, N.10 |
| TB-14 | major | D.3 orders Telegram commands 'as they arrive' and judges a command's age by its commit time, which a Telegram command does not have. | applied: N.5 commands (created_at = message date, 15-minute rule, 90 s edit), D.3 ordering |
| TB-15 | major | The Bot API returns 409 in two cases: another getUpdates call on the token (the newer poll wins and the older one gets the 409), and a webhook set on the token. | applied: N.5 (poll lock, the two 409 causes, leak path), N.4 device-code warnings, H.10 item 9 |
| TB-16 | major | Only network errors are handled: they back off, and after 30 minutes the bridge falls back to Gmail. | applied: N.5 outages (403, 400, 401, 429, polling-gap message) |
| TB-17 | major | The scrubber refuses a whole message for patterns that routine messages contain. | applied: N.5 outbound safety in two tiers |
| TB-18 | major | The scrubber is a list of patterns applied to outgoing text. | applied: N.5 (known-secret matching after normalisation, all payload types, no request URLs, redactor, minimal child environments, LimitCORE=0) |
| TB-19 | major | N.5 says the bridge 'never opens ~/.config/dgist-agents/ except for the one-variable copy at bootstrap', and a test greps bridge/ for that path. | applied: N.5 (ops/fallback/dgist_send.py is the only reader of the DGIST files; Gmail batching; GMAIL_TO check), A.4, R.2 |
| TB-20 | major | A drop is accepted if the need is open, the kind matches and the value passes a format regex. | applied: N.6 (staged drops, username check, known bots refused, issue author check, Confirm for later drops) |
| TB-21 | major | drop.html runs 'under the CSP of D.3 with connect-src https://api.github.com'. | applied: N.6 (CSP, fingerprint in the fragment, key id, plain refusals, every read issue deleted, issue_path, drop age), E.2, D.3 |
| TB-22 | major | A secret pasted into the chat is deleted, but deletion is best effort: the facts say to treat it as cleanup, not confidentiality. | applied: N.5 inbound secrets (hard classes, rotation need, soft classes kept), N.2 code detail |
| TB-23 | major | The checks prove that a login exists, not whose login it is. | applied: N.3 (gh_auth checks the login and scopes; rclone_about checks the account e-mail), N.7 |
| TB-24 | minor | There is no link format for a message in a private chat with a bot: t.me/c/... | applied: N.5 /needs as quoted replies, N.8 |
| TB-25 | minor | N.2 says device-code expiries come 'from the provider's expires_in, never guessed'. | applied: N.2 and N.7 (approximate gh expiry, no timer kills a flow), N.4 (KST, Seoul time), N.3 quiet hours |
| TB-26 | minor | Several details of the page and of key handling are unspecified. | applied: N.6 (masked textarea, clipboard, crypto_box_seal with pinned vendored code and a known-answer test, markers, lenient parsing, retired keys deleted) |
| TB-27 | minor | GitHub keeps at most 10 tokens per user, OAuth app and scope set; an eleventh revokes the oldest unused or least recently used token, which can be the forge's or the PC's gh token. | applied: N.7 (environment isolation, the ten-token limit, a distinct scope set, at most 3 logins) |
| TB-28 | minor | The bootstrap sends device codes through the DGIST bot to the copied TELEGRAM_OWNER_CHAT_ID before anything confirms that the value is the owner's private chat. | applied: N.5 owner-id copy rule, N.9 steps 2 and 5 |
| TB-29 | minor | Neither the persistence nor the order of the outbound queue is specified. | applied: N.5 rate, order and persisted outbox |

## Lane isolation attack (LI): 25 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| LI-01 | critical | The revised jail adds a private /tmp and /dev/shm, hides /run/user/<uid> and drops capabilities. | applied: H.4 layer 1 (PID/IPC/UTS/cgroup namespaces, read-only /sys, clearenv, no network, viewer through a forwarder) |
| LI-02 | critical | The revision moved copy-in out of the jail. | applied: H.4 layer 8 (sbxfs.py with openat2, jailed copy-in writer, shared-inode check) |
| LI-03 | critical | Moving from process attribution (IM-15) to write intent was right, but the intent is unauthenticated. | applied: H.4 layer 4 (intents authenticated by SO_PEERCRED and cgroup, all operations, ledger-anchored sweep, lanewatch unit), R.2 |
| LI-04 | critical | The new build jail keeps secrets out but does not keep the build away from the experiment lane. | applied: N.8 (sandbox and record read-only in the build jail, tmpfs over /run, /tmp and /dev/shm, launcher limited to templates, drain and release), H.4 layer 9, C.2 record root |
| LI-05 | critical | gate-change refuses a change only to a band 'that a claim with an existing result is judged on'. | applied: G.8 (no change in either direction once any row reports the metric; held-out assets immutable; verdict under the registration epochs), D |
| LI-06 | major | A Promote request is a file in a directory that the sandbox jail, build sessions (their jail binds the sandbox tree read-write) and any plain-shell process can all write. | applied: H.8 (a request changes nothing until the user confirms it from a TTY or a signed dashboard command; daily cap; expiry), H.5 |
| LI-07 | major | Promote stops paths and checkpoints, but learned state can still cross as numbers or through the choice of parent. | applied: H.8 (scalars only, no arrays over 8, assets by id and hash, no seeds or parent selectors, runner-computed diff) |
| LI-08 | major | Promote is the only path that records sandbox provenance, but not the only way a sandbox-tuned value enters the experiment. | applied: H.8 (config_key and sandbox_origin on every registration; catalogue manifest) |
| LI-09 | major | Training seeds belong to the candidate id, not the config, and they are derived from a string. | applied: C.3 (seeds from os.urandom, config identity, retries keep their seed), G.5, H.5 |
| LI-10 | major | The spec never says what check_gate does when an arm of a registered claim is killed, paused, failed or still running. | applied: G.5 (pending until complete; pre-declared comparisons; post-hoc label), H.5 |
| LI-11 | major | The only thing keeping the sandbox from held-out assets is a copy-in allow-list, but those assets can be regenerated; they are not stored secrets. | applied: H.7 (lane-salted seeds, sandbox seed pools, no network), H.11 LI9 by content |
| LI-12 | major | A job runs much more than its hashes cover. | partly: C.2 exec_id (run tree, venv, environment and unit manifests), UV_LINK_MODE=copy, env -i with an allow-list, PYTHONNOUSERSITE, the module-location check, R.8 drift check, H.4 layers 3 and 5; lane-specific uv caches were not adopted (one shared wheel cache, read-only, is safe with copy mode) |
| LI-13 | major | Layer 3 checks each input's hash when the job starts, and the job then reopens the file by path. | applied: H.4 layer 3 (verify-then-use, model/reference/device hashes in job identity), C |
| LI-14 | major | Sharing resources with the sandbox can change verdicts, not only wall-clock times. | applied: H.4 layer 6, C.5, C.10, R.2, R.5 |
| LI-15 | major | The two lanes share one filesystem and one 30 GB cap, and neither lane has a quota, because quotas need root. | applied: H.7 (sandbox disk budget, stop before the experiment's floor, sandbox pruned first) |
| LI-16 | major | A hash chain only proves that its rows agree with each other. | applied: R.7 ledger head, D.3 ruleset C, D.8 dead-man ledger check, H.4 layer 3 |
| LI-17 | major | The mailbox authenticates a token, not a person or a device. | applied: D.3 (per-device signing keys confirmed on Telegram) |
| LI-18 | major | D.5 declares data returning from Vast untrusted, but the spec then harvests it as a first-class result. | applied: C.4 (gating metrics from lab evaluations only), D.2 move_to_lab exclusions |
| LI-19 | major | Exact replay keeps its rows apart, but not the author materials or what they reveal. | applied: H.9 (author materials converted in their own jail; source: author; informed_by_author_materials) |
| LI-20 | major | The experiment root is a string prefix of the sandbox root, so any containment check written with startswith treats sandbox files as experiment files. | applied: H.2 (sandbox root renamed; is_relative_to; grep test), C |
| LI-21 | major | A sweep hashes its rule's id and parameters, but the code that evaluates the rule lives in runner/rules.py. | applied: G.8 (selection rules and parent resolver in gate/rules/ under GATE_HASH), C.7 |
| LI-22 | major | From inside the jail, where the experiment paths are not mounted, the fuzzer tries to write, rename, symlink, hard-link and chmod experiment files. | applied: H.11 (fuzzer against the real worker with the real attack surfaces) |
| LI-23 | minor | Metrics are recomputed from rollouts, but the facts behind equal budgets come from the worker's results.json: transitions per stage, per-actor update counts, and the torque limit, which the worker asserts against the con | applied: C.4 harvest cross-checks |
| LI-24 | minor | sbx compare computes the G.3 metrics with the sandbox's own code, which the user may have edited, and shows them beside the experiment's numbers. | applied: H.7 (amber warning when sandbox metric code differs) |
| LI-25 | minor | The spec does not say which version a paused candidate resumes as after an edit, or whether a new version may continue from an older version's intermediate checkpoint. | applied: H.5 (pause and resume act on jobs; edits never touch a started job) |

## Research design and gate (RD): 28 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| RD-01 | critical | The L3 verdict is a conjunction of about twenty per-seed and pooled conditions, judged against published values that are single runs with no seed variance. | applied: G.2 L3 (pooled magnitudes, three-way verdict, 3 → 5 → 10 escalation, catastrophe floors, ablations as separate claims, prediction interval), G.4 |
| RD-02 | critical | Every protection is per claim, and claims are cheap. | applied: G.5 families with Holm, killed arms count as failed, G.8, G.9 (every family), B.7 Q8, C.14, D.3 |
| RD-03 | critical | The mechanism path, described as the almost guaranteed paper, is not machine-decidable and is biased in places. | applied: G.6 G2 split by path (B7 never a rival), G.7 mechanism outcomes M-reward/M-velocity/M-simple/M-learned, 02 §6 |
| RD-04 | critical | The decisive controls are not matched in the ways that matter, and the design's own rules would reject them. | applied: B.6 matching (reward, stages, budget, dose; B2-w), G.6 G1 exemption, C.10 |
| RD-05 | critical | (1) The assistance gate compares the assisted condition with 'the same human wearing the passive device'. | applied: G.2 L5 (C1-matched comparator; own gate family frozen in M8), B.8 route (b) |
| RD-06 | major | Tuning effort and tuning conditions are asymmetric in SMAT's favour. | applied: B.6 tuning on tuning blocks with co-adapted screening, B.7 Q3t |
| RD-07 | major | Under the default aggregate reading, Stage 3 is 1.1 M transitions: 16.8 PPO updates, about 1,344 minibatch steps at lr 3e-5, each update cut short by target KL 0.01. | applied: B.7 Q4 (S3 reading chosen by a known answer before any S4 job), Q7, G.2 L4b |
| RD-08 | major | The registry defaults are good practice, but unlike SMAT's probable implementation. | applied: B.6 and B.7 Q4e era-faithful pipeline, B.2, G.2 L2 report |
| RD-09 | major | (1) The 'P3 on 3 fresh seeds' are used both to choose among the three finalists and as the L1 claim's seeds and the parents of every later stage: winner's curse on L1 and on the whole lineage. | applied: B.7 Q2 (screening score, exactly one selection, confirmation seeds, orthogonal array, value normalisation, recall-based calibration), G.5 |
| RD-10 | major | Stage 2 and Stage 4 may each walk anywhere in 1.25 ± 0.10 m/s, and Stage 4 weights speed 1.5 against 0.8. | applied: G.2 L3 (speed-preservation limit, per-metre direction), G.3, B.7 Q3 slope |
| RD-11 | major | G.4 says the bands stay inside the distance between SMAT and its nearest ablation, including 'four-group reduction 10.1 % versus 0 for no assistance'. | applied: G.4, G.2 L3 (device-attributable reduction on the same line), C.12 |
| RD-12 | major | The published 0.83 is read from the bilateral mean profile (O Fig. | applied: G.3 (primary definitions from the mean profiles, P0 = 0.5 W) |
| RD-13 | major | (1) 'Half-width' is undefined for the one-sided and binary criteria that carry the most per-seed risk: symmetry ≥ 0.92, RMSE ≤ 3.6°, negative power ≤ 15 %, falls ≤ 10 %, and 'every group reduced'. | applied: G.4 (operational half-widths, fall rate on at least 100 episodes), G.3 (cycle exclusion and invalid metrics) |
| RD-14 | major | P1 runs a different model (22-muscle, planar), reward and device, with no pass criterion ('walk stably'), so it cannot tell a walk26 bug from a model limit. | applied: B.6 known-answer controls K-exo3, K-exo4, K-effort, K-env, K-metric; G.7 |
| RD-15 | major | B2's filter is the discounted LQ optimum of the exo reward terms alone, derived with ω̂ held constant (smat_spec). | applied: B.6 B2+ and B8, G.7 wording, 02 §6 |
| RD-16 | major | (1) The held-out S4 humans were co-adapted to SMAT devices, so SMAT-like devices meet familiar partners while B2 and B6 meet unfamiliar ones. | applied: G.2 L4c (device-naive partners, linear contrasts, crossed random effects), B.6 cross-play 2 × 2 |
| RD-17 | major | (1) Learning parity covers Stage 1 only, on 3 seeds, with margins equal to the full L1 bands (lenient), while the GPU is meant for S3–S4 work (Q7, Q8), where the headline metric lives. | applied: B.5 gate 4b (S3–S4 learning parity), gate 3 margins and policies, MULTICCD sensitivity |
| RD-18 | major | The only replicate unit is an independent full pipeline (about 0.55 B transitions). | applied: G.4 (blocks × replicates, blinded re-estimation), B.7 Q5 pilot |
| RD-19 | major | The pre-loaded campaign cannot complete any path's G2. | applied: B.7 Q5b, G.8 required-arms test |
| RD-20 | major | (1) Maximum speed is the peak 0.5 s moving average over any run, including failed runs, so a forward lunge or fall can reach 4.0 m/s. | applied: G.2 L5 (flying 20 m speed, naming, architecture test, nominal and pessimistic actuator, seed as the unit), G.3 |
| RD-21 | major | Conjunctions are handled correctly (an intersection-union test needs no adjustment), but disjunctions are not. | applied: G.2 L4 (one primary sub-criterion, Holm), G.4 (one-sided 95 % everywhere, Holm or exploratory labels), G.7 |
| RD-22 | major | Arm matching checks transitions, torque, code identity and backend, but not config identity outside the arm-defining keys. | applied: G.5 arm-defining keys, C.10 |
| RD-23 | major | The value of the design rests on bands and rules fixed before the evidence, but the only proof is a hash chain in a private repository whose commit dates the authors control. | applied: G.8 public preregistration before the first Stage-4 job, C.14 |
| RD-24 | minor | G5 asks a second machine to reproduce 'the central cell on 3 seeds within the claim's band'. | applied: G.6 G5 (bit-equal re-evaluation; prediction interval for a mean of 3) |
| RD-25 | minor | The suspect thresholds ignore the arm. | applied: C.10 arm-specific suspect thresholds |
| RD-26 | minor | The toe-off band's upper limit (61 %) excludes the common overground value of about 60–62 %, so a more physiological reconstruction can fail L1 (this norm was not re-checked here). | applied: G.2 L1 split into published and plausibility parts; toe-off 55–62 % |
| RD-27 | minor | Deterministic evaluation matches MyoAssist's evaluator and is a reasonable primary. | applied: G.3 (stochastic sensitivity, stationarity check) |
| RD-28 | minor | Several quantities check_gate.py must compute are undefined. | applied: G.2 (A1 at 6 Nm, L4a torque bound), G.3 (body weight with device), G.7 (Kendall's W), B.6 (B4 matched on positive work) |

## Implementability and sequencing (IM): 30 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| IM-01 | critical | Every user-dependent M0 step is serial behind the GitHub login: login -> repository -> Pages -> drop page -> bot token -> bridge. | applied: E.8 step 0, N.9 steps 1–3, README step 3 |
| IM-02 | critical | The flags the wrapper uses are defined only 'once the user taps' option 1 or 2. | applied: README first message carries the builder mode; N.8 launch rule (h) |
| IM-03 | critical | Wrapper-launched Codex sessions run inside smatsprint-ctl.slice, which R.2 caps at 2 CPUs and 1 GB in total, shared with the controller, runner, bridge, wrapper and watchdog. | applied: N.8 build slice, R.2, E.4 detach.sh slices, H.4 layer 4 |
| IM-04 | critical | The launch rule checks only blocking needs, the build-pause button and the usage-limit cool-down. | applied: N.8 (end.json and launch conditions), E.4 |
| IM-05 | critical | Before the first registered experiment, M1 must deliver: the environment; the trainer; eval/ for every protocol (walk, sprint, parity, partner transfer, offline replay); gate/ for L0-L5 and all three paper paths, with sy | applied: E.4 M1a/M1b (watcher to M3, card validator to M2), B.7 registration order (Q2 restricted to the options available in M1a), G.8 freeze by milestone, H.4 |
| IM-06 | major | The M1 exit, and so the campaign start, waits on long wall-clock suites: two 10-minute 'stays inactive' holds; 100 real pause/resume cycles, each up to about 50 s to stop plus up to 120 s for the heartbeat; 50 SIGKILL mo | applied: E.4 campaign-start gate, C.8 correctness task, R.2 fault injection |
| IM-07 | major | B.2 says to compose with compose_env_model(..., planar_root=True) but never says in which environment. | applied: B.2 (where composition runs, runtime depends only on mujoco, effective-model hash, free-root caveat) |
| IM-08 | major | The prompt never says whether the PPO update of CPU-physics jobs runs on the GPU or the CPU. | partly: C.8 makes the GPU learner the default, with rows recording learner_device, and B.7 Q1 measures both learners; the finding's "comparable within the tolerance Q1 measures" was not adopted (no such measurement is defined): the learner device is a registry choice that the arms of a claim share, and the CUDA learner runs in deterministic mode so resume stays bit-equal; the CPU-physics hardware class includes the learner GPU's compute capability (G.5) |
| IM-09 | major | C.7 puts the tier calibration in Q1: at least 8 configurations, each at P1 (40 M) and P3 (320 M), on 2 seeds. | applied: B.7 Q1 (throughput only) and Q2 (12 configurations at P3 as calibration and miss check; P1 selection waits for them), C.7 (trust P1 by top-third recall), G.4 noise-floor calibration |
| IM-10 | major | Q2 selects configs by the L1 criteria, which need evaluation episodes. | applied: G.5 and C.3 seed pools with the selection pool |
| IM-11 | major | G.4 has 'the runner' raise the evaluation episode count E automatically when measured noise exceeds a quarter of a band half-width, but the prompt never says where E lives. | applied: G.4 E function (largest over the gated metrics, 20 before any noise-floor row, part of evaluation job identity), C.9 |
| IM-12 | major | The single uv.lock also receives the tooling added during M0-M7: PyNaCl, pytest, hypothesis, playwright, gymnasium for the PPO check, plus mujoco-warp and warp-lang in M4. | applied: C.2 dependency groups and code_id, E.2 |
| IM-13 | major | A candidate's EVAL_HASH and GATE_HASH are pinned at registration, and its jobs refuse to start on any mismatch. | applied: G.8 hash families and epoch re-registration, C.9 |
| IM-14 | major | A process started with systemd-run --scope is moved into its own scope cgroup under smatsprint-exp.slice. | applied: R.2 scopes and pause, D.2 |
| IM-15 | major | This is not implementable in user space. | applied: H.4 layer 4 (write intents, then authenticated by LI-03) |
| IM-16 | major | Execpolicy rules load from the rules/ directories of active config layers (fact codex-36). | applied: N.8 (project rules, enumerated foreign units, prompt-only conditions stated) |
| IM-17 | major | In option 2 the only vetted helpers are a 'git push helper' and launch-detached. | applied: N.8 (own canary file, option-2 helpers, bus-reachability warning, push canary after the repository exists) |
| IM-18 | major | Several rules conflict. | applied: N.5 single fallback module, A.4 |
| IM-19 | major | (a) With 80 GB free on 2026-09-23 and a 65 GB floor, only about 15 GB can be used before new work stops, not the 30 GB cap. | applied: A.5 per-host floors, H.4 layer 5 shared wheel cache, B.6 replay subset, E.4 disk need |
| IM-20 | major | An equivalence claim against SMAT needs at least 10 seeds according to the README, but 5 according to the gate text. | applied: G.2, G.4 and G.7 (10 seeds for equivalence), B.7 Q6b, README, Page one |
| IM-21 | minor | Codex would have to guess items that change results. | applied: B.2, B.3 rows 17–19, G.3 fall and evaluation rules, C.5 checkpoint contents |
| IM-22 | minor | Q5 calls 'A1, B1 and B3' cheap, but B.6 makes B1 co-adapted at 66 M, and B3's 6 variants inherit the 66 M default. | applied: B.6 and B.7 budgets, Q6p partner humans, C.10 |
| IM-23 | minor | The single push function enforces 30 s spacing, yet a pause acknowledgement must publish 'at once'. | applied: C.2 and C.4 (ledger and generated documents on the ledger branch only), D.3 push spacing |
| IM-24 | minor | At step 4 no push credential exists. | applied: N.9 step 4 deploy key, D.3 ruleset fallback |
| IM-25 | minor | copy-in must read experiment configs and checkpoints, but it is listed as a jailed process, in a jail that binds nothing of the experiment tree. | applied: H.4 layer 1 (Python installation bound, device nodes enumerated, cache variables, sbx code sync); copy-in is by a jailed writer (LI-02) |
| IM-26 | minor | The sail-gpu alias exists only in the PC's ~/.ssh/config. | applied: H.10 (PowerShell linter, user-level sshd for tests, throwaway instances under the project cache) |
| IM-27 | minor | Loading MyoAssist's reference file requires np.load(allow_pickle=True). | applied: B.2 reference conversion without pickles |
| IM-28 | minor | Headless Chromium needs system libraries, which `playwright install-deps` installs with sudo. | applied: E.4 Phase 0 prerequisites probe and one bundled root script |
| IM-29 | minor | Wrapper sessions are systemd transient units, so their PATH contains neither ~/.local/bin nor sprintctl, yet the continue prompt says 'create needs with sprintctl need create'. | applied: N.8 (explicit PATH and environment, build_sessions_per_day default 4, continue prompt diffs the handoff folder), E.9 |
| IM-30 | minor | The prompt has wrong or dangling references, undefined terms and colliding names. | applied: H.5, H.2, C.9, H.9, D.7, E.4 (Mode B removed), A.4 (forge handoff path), B.8 (profiles defined inline), B.6 (known-answer controls replace P1–P3) |

## State machine and coexistence with the forge (SM): 29 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| SM-01 | critical | Packed jobs run in transient scopes (systemd-run --user --scope --slice=smatsprint-exp.slice), which are separate units from smatsprint-worker.service. | applied: R.2 (named scopes with BindsTo, PDEATHSIG, flocks, stale-scope stop, slice-level stop and cgroup.kill, verification by cgroup.events and nvidia-smi), D.1, D.2, I6, N.10 pause_not_verified; TimeoutStopSec=40 on scopes was left out because it would cut the 45 s SIGTERM exit |
| SM-02 | critical | 'The mirror, the record copier and the moves ignore anything with an older epoch' contradicts resume. | applied: D.2 epoch fencing by lineage (state/epochs.jsonl), D.1, I1, I11; two deliberate deviations: checkpoints restored from a fenced host's pre-fence backup are accepted, and a rejected DONE also returns the job to the outbox |
| SM-03 | critical | The user asked for the tick-box ('The sandbox lane travels with the experiment lane on a move only if I tick it'), and also wrote 'When I move from Vast back to the GPU server, everything moves back' and 'Nothing is dele | applied: D.1 and D.2 (the sandbox move specified end to end), H.7 (tick box disabled until its rehearsal passes) |
| SM-04 | major | The forge's D.3 exempted pause, emergency_stop, cancel_move, settings and register_device from busy rejection. | applied: D.3 (safety commands never busy-rejected) |
| SM-05 | major | (1) 'vastai stop instance $CONTAINER_ID' passes no key. | applied: D.6 worker self-guard (lower-bound cost, 30-minute sync wait, never destroys; the key goes in the child's environment, not argv, per A.5 rule 8; verify in M5), D.2 lease_cap at 90 % |
| SM-06 | major | The adaptation dropped the forge's definition of a 'full copy'. | applied: D.2 covering copy and park |
| SM-07 | major | min_free_gb gates only 'a new job, download or archive'. | applied: D.2 disk precondition for lab writes, D.7 streamed archives, A.5 |
| SM-08 | major | A.4 and the probe measured 80-82 GB free, a figure that 'moves by tens of GB a day'. | applied: A.5 rule 5 (admission against the forge floor plus a 3 GB margin, reserved writes counted), D.2 PAUSED(by: disk), R.3/R.4, README; the finding's 25 % overrun stop and IM-19's option to lower the floor to 62 GB were not adopted |
| SM-09 | major | The two programmes cannot deadlock on memory, because running jobs finish and free it. | applied: R.2 (OOMScoreAdjust, admission with forge_reserve, ramp waits, start jitter), N.10 memory_starved, H.4 layer 6 |
| SM-10 | major | Each programme treats the other as a same-account process that coexists, so neither yields compute and no priority is defined. | applied: D.2 same_account_gpu options, exp_vram_cap_gb, R.3/R.5 bounded no-strike re-queues, N.10 gpu_contention |
| SM-11 | major | Pause, emergency stop and polite pause act only on the worker and smatsprint-exp.slice. | applied: D.1 and D.2 (pause covers sandbox runs and GPU build jobs), H.7, E.4 |
| SM-12 | major | Every Pause path runs through the controller. | applied: D.3 failsafe pause, R.2 watchdog, N.5 /pause fallback |
| SM-13 | major | (1) The forge's rule 'on confirm the loop runs and polite mode ignores the PIDs present at that moment' was dropped. | applied: D.2 (override ignore list, flap damping, UID classification), A.5 |
| SM-14 | major | 'Hardware class' is never defined, yet gate/ freezes in M1, long before the M5 move semantics exercise it. | applied: C.10 and G.5 hardware class, D.2 move dialog and run_replication, D.6, B.5 certificate |
| SM-15 | major | Inside a Docker container, /proc/meminfo, MemAvailable and os.cpu_count() describe the whole host. | applied: R.2 container budgets, D.6 offer ranking with storage and bandwidth |
| SM-16 | major | The worker materialises each job's code with 'git archive <sha>', but a Vast worker has no git objects, and R.10 forbids pulling code from anywhere but the lab. | applied: D.1 code shipment to Vast, C.2 |
| SM-17 | major | The Vast account 'UGRP Exp' is shared with the forge (also USD 150 a month) and with other people. | applied: A.5 rule 6, D.2 and D.6 credit rules, README |
| SM-18 | major | (1) One full lab disk triggers both programmes' emergency evacuations at once, and both draw on one Google quota: 15 GB on a free account, shared with Gmail and Photos. | applied: D.7 (separate Google project, daily lean backup, prune rule with evacuations logged in state/evacuated.jsonl), N.7 |
| SM-19 | major | The rehearsal label smatsprint-rehearsal-* lies inside the production prefix smatsprint-, and the rehearsal runs 'from its own checkout with its own state/ root'. | applied: D.6 labels smatsprint-prod- and smatsprint-reh-, D.3 destroy-labelled accepts only the rehearsal prefix (and destroys only there, since rehearsal data is disposable), R.7 orphan rule, A.4 and A.5 rule 6 |
| SM-20 | major | At B.7's planning rate of about 20,000 end-to-end transitions per second, one 65,536-transition SMAT update takes roughly 3-5 s per job. | applied: C.5 pin protocol, D.2 mirror rules |
| SM-21 | major | The latency-critical controller shares a 1 GB, 2-CPU slice with the runner, bridge, wrapper and watchdog. | applied: R.2 slice table (ctl 2G and 400 %, build, bulk; Nice, I/O class and OOMScoreAdjust set on the units, since slices cannot carry them), C.13, N.8 |
| SM-22 | major | Both dashboards are Pages sites on mushfique-dgist.github.io and share one localStorage, and this programme's shell is copied from the forge's. | applied: D.3 storage key prefix and no service worker, E.2 two-dashboard test |
| SM-23 | major | The automatic out-of-memory fallback changes a registered choice (the world count, and with it the batch geometry) while the job keeps its identity. | applied: R.3 (no automatic change of the world count) |
| SM-24 | minor | The forge's poll interval ('git ls-remote origin refs/heads/control' every 15 s) was dropped, so the ≤ 90 s button-to-free budget has no stated input. | applied: C.1 poll intervals, D.5 drain signal, I4 |
| SM-25 | minor | state_version increments on every change of phase kind, so every polite pause and resume bumps it. | partly: D.3 and H.5 use based_on_queue and candidate versions; the finding's need-button nonce clause was replaced by the decision-button rule of N.5 (UX-09): based_on is the state version when the need was sent, and a changed state raises a fresh need |
| SM-26 | minor | An instance that the API reports as running but that SSH cannot reach (direct and proxy) for 15 minutes is treated as lost and destroyed. | applied: D.2 I2 and Replace (a lab-side SSH canary plus a TCP connect to the Vast SSH proxy host; verify in M5) |
| SM-27 | minor | After M2 the lab holds only the deploy key, which works only for git. | applied: D.8 dead-man branch, R.8 |
| SM-28 | minor | Gmail is the bridge's fallback, and it is the watchdog's only path when the bridge is silent. | applied: R.8 daily Gmail fallback check |
| SM-29 | minor | gh, rclone, vastai and uv are called from ~/.local/bin, where the forge's build installed them and can upgrade them at any time. | applied: A.4 pinned tool copies, A.5 cache list, N.8 PATH and systemctl rules |

## Fidelity to the request and user experience (UX): 27 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| UX-01 | critical | M0 runs entirely inside the one Codex session the user starts at the PC. | applied: N.9 and N.8 (bootstrap never depends on a live session), E.3, README step 3 |
| UX-02 | major | No milestone builds Phase 2, the lab's actual direction. | applied: E.4 M8, Page one, B.7, B.8, G.8 sprint gate family, C.9, N.8 ARMED(M8), N.10, README |
| UX-03 | major | Anti-pattern check: 'a week of infrastructure before the first experiment'. | applied: E.4 M1a/M1b, B.7 (K-env replaces P1 and moves out of Q1) |
| UX-04 | major | The user's typical tweaks cannot be expressed. | applied: B.3 continuous parameters, H.8, D.4 |
| UX-05 | major | The sandbox, the feature the user says they will use most, cannot be driven from the phone. | applied: D.3 command set and D.4 Sandbox panel, H.7 |
| UX-06 | major | The gate is the part the user called most crucial, and it departs from the request in ways the README never shows. | partly: README correction 7 and question 9 show every departure to the user; G.2 keeps the four-group criterion as the only L3 pass and the 5 % torque allowance until the user answers (the bands must be settled before the first Stage-4 result) |
| UX-07 | major | Sweeps have no legal seeds to be judged on. | applied: G.5 and C.3 selection pool |
| UX-08 | major | Q8, the L4 attempts behind one of the three paper paths, has no owner and uses forbidden wording. | applied: B.7 Q8 pre-registered held blocks, 02 §5 |
| UX-09 | major | N.5 says 'Nothing else can be commanded from Telegram' besides /status, /needs, /pause, /resume and /help, and H.5 lists only /pause and /resume as the Telegram subset. | applied: N.5 decision buttons, H.5, D.3 |
| UX-10 | major | The PC-only list is short only because it leaves out PC steps the prompt creates. | applied: README PC-only list, N.8 Start a build session, E.5 paper upload, D.3 paper_upload |
| UX-11 | major | At review time (2026-09-23, about 19:30 KST) the package is not ready to hand over; if it shipped as is, the first step would fail. | applied: papers and digests rebuilt with no draft or pending fields, verification.json written, prompt reassembled and checked, folder mirrored with checksums |
| UX-12 | major | Section 3 of the request lists topics the paper list must cover, and several are missing. | partly: the clusters were completed and cover MJX, Newton, Isaac Lab, MyoSuite, MASS, Molinaro 2024, Powell 2026, running exosuits (passive and active), DeepMimic and its successors, and the walking datasets (Camargo 2021, van der Zee 2022, Scherpereel 2023), now named in B.2 and B.6; MyoDex (a dexterous-hand paper) was left out as irrelevant to the legs; DASH has no public paper and is listed as an occupied claim |
| UX-13 | minor | The first need goes through the shared DGIST bot with no buttons, because the programme cannot poll that bot. | applied: N.4 and N.9 (DGIST-chat line), README table |
| UX-14 | minor | Other deliberate departures are explained only deep in the prompt, not in the README the user reads. | applied: README corrections 8–11, H.6 download line |
| UX-15 | minor | The request's search space names items the registry leaves out: domain randomisation ('if any'); the body-model version with its muscle and contact parameters; exoskeleton inertia and attachment (only mass is a choice);  | applied: B.3 rows 20–23 |
| UX-16 | minor | The request names the evergreen tasks as '(more seeds, longer budgets, baselines)'. | applied: B.7 evergreen longer-budget arms, C.4, R.6 |
| UX-17 | minor | The request asks for 'a CPU, RAM and GPU budget split' between this programme and the forge, 'visible and adjustable on the dashboard'. | applied: H.5 --exp-vram, D.4 host view, README split row |
| UX-18 | minor | H.5 treats 'Pause, Resume, moves, Drive actions' as steering actions that require a 1-200 character reason, and D.4 gives every experiment-changing control 'a required one-line reason field'. | applied: H.3 and H.5 (prefilled reasons for Pause, Stop and Emergency stop), D.4 |
| UX-19 | minor | N.2 caps a need at 8 phone steps. | applied: N.2 (8-step cap with consecutive parts), N.7 Drive in three parts, N.9 bot in two parts, README |
| UX-20 | minor | The user chooses between 'full access with guardrails' and 'auto-review'. | applied: N.8 (the decision need states the canary results) |
| UX-21 | minor | Nothing says which needs set blocks_build, and two acceptance lines depend on the user acting, one of them at the PC. | applied: N.2 (verification asks never block), E.3, E.4 |
| UX-22 | minor | Phone noise can bury the needs the user must act on. | applied: N.3 quiet hours, D.8 digest routing, E.4 detached-job messages |
| UX-23 | minor | The README asks eight questions and says 'Tell Claude or Codex the answers'. | applied: N.9 step 11, E.8, README |
| UX-24 | minor | The request makes the weekly research note (KB status vocabulary, with the user's steering decisions) a standing output. | applied: E.4 (weekly note from M2) |
| UX-25 | minor | Two dangling references could stall a builder. | applied: E.4 (Mode B removed), H.9 reference, check_prompt.py stale term |
| UX-26 | minor | The request asks for the lane name on every 'filename prefix and artefact'. | applied: H.3 exp_ prefix |
| UX-27 | minor | The request lists 'the DEP-RL MyoLeg walking checkpoint installed in .venv-deprl' among the assets to recreate from. | applied: B.8 (DEP-RL walker replayed before the solver-and-speed probe) |

## Final cross-part consistency read after the edits (FC): 40 findings

| Id | Severity | Problem (first sentence) | What was done |
|---|---|---|---|
| FC-01 | blocker | Every unattended session after M0 is a jailed build session that may not pause or resume: its steering is refused and the launcher offers only drain and release. | applied: N.8 launcher pause_resume_drill; D.2 PAUSED(by: release) and the first-install state; R.9 (a release ends its own drain's pause); E.4 campaign-start gate; E.2 rehearsal |
| FC-02 | blocker | M1b must open a gate epoch to add L4 and the walking paper paths. | applied: G.8 gate/core plus gate/families/{walk,method,sprint} with per-family hashes; first_freeze launcher operation for new families and protocols (C.9, N.8); E.4 M1b and M8 |
| FC-03 | blocker | L1 always judges a fall rate, and a fall rate needs at least 100 episodes. | applied: G.4 (E at least 100 for claims that judge a fall rate; the first noise floor on the Q2-selected P3 checkpoint before its L1 claim), C.9, B.4 |
| FC-04 | blocker | Detached build jobs run in the build-jail profile: no user bus, the record root read-only, no steering. | applied: E.2 test instance for disruptive suites; launcher test_instance and cold_start_drill (N.8, R.2) |
| FC-05 | blocker | The composed model, its `.mjb` and the converted reference must be in `work/refdata/` before L0, and the external reference must be added there in M1b. | applied: C.3 refdata_install job kind; B.2 staging directory; N.8 refdata_install operation |
| FC-06 | major | E.4's waiting recipe passes a free-form command after `--` to the launcher. | applied: E.4 detach.sh takes a registered job file from the service tree; N.8 option 2 uses the same files |
| FC-07 | major | Jobs, moves and restores compare model, reference, device and refdata hashes with the ones recorded at L0. | applied: refdata registry ledger/refdata.jsonl replaces 'recorded at L0' in C.3, C.5, D.2, D.7 and H.4 layer 3 |
| FC-08 | major | The campaign starts in M1a, and Q3–Q8 are added to `catalogue/campaign.yaml` afterwards, in M1b. | applied: H.8 catalogue frozen per registered block set; later entries get Promote's provenance checks, not its confirmation |
| FC-09 | major | G.8 publishes each epoch's stamped manifest on the public Pages site before the first Stage-4 job, and C.4 holds every Stage-4 job until it exists. | applied: G.8 public registration kept in the ledger with its .ots proof, nothing on gh-pages; P0 L0 exempt (C.4); R.4 NO_TIMESTAMP |
| FC-10 | major | Only the runner, the controller and job scopes may write record state, and the watcher flags every other change under the record root. | applied: H.4 layer 4 watches ledger, registered configs, baselines, generated docs, queue, record and work; state/ has its own writers; the worker service may write |
| FC-11 | major | The jail hides `~/.config/smatsprint/` except `gh/`, and no launcher operation writes there. | applied: N.8 launcher create_deploy_key, create_vast_ssh_key, write_limits_defaults; N.9 step 4 |
| FC-12 | major | The README promises the user that every build session is jailed away from the Vast key. | applied: the Vast key is bound only into the rehearsal job's own jail profile (N.8, E.2); no Codex session sees it |
| FC-13 | major | Every build session gets `~/.codex` read-write. | applied: N.8 ~/.codex read-only except what a session must write; canary; R.8 daily hash check of config.toml and rules/ |
| FC-14 | major | E.4 schedules 'the host-resource fence (Part R.2)' for M1b. | applied: E.4 M1a installs the memory and disk admission rules before Q0 |
| FC-15 | major | systemd derives a slice's parent from its dash-separated name, so a slice named `smatsprint-build.slice` is always created inside `smatsprint.slice`. | applied: the build slice renamed smatsprint_build.slice (a dash would nest it), everywhere; R.2 explains why |
| FC-16 | major | H.7 invents a sixth pool (40,000–40,999) and relabels 20,000–20,999 as sandbox evaluation. | applied: H.7 uses the single sandbox pool 20,000–20,999 |
| FC-17 | major | C.2 lists MyoSuite in the science group, which B.2 forbids because MyoSuite pins MuJoCo exactly, clashing with `mujoco==3.14.0`. | applied: C.2 science group without myosuite |
| FC-18 | major | G.4 (and the sheet) require B.5's learning parity, an equivalence test, to use at least 10 blocks with the blinded re-estimate. | applied: B.5 gates 4 and 4b on at least 10 seeds or blocks |
| FC-19 | major | The sheet requires all five known-answer controls before a Stage-4 'not reproduced'. | applied: G.7 and B.6 require all five known-answer controls for a Stage-4 non-reproduction |
| FC-20 | major | K-env runs MyoAssist's own Stable-Baselines3 trainer, which exists only in the old sprint `.venv`. | applied: C.3 known_answer_env job kind; B.7 Q2 schedules K-env |
| FC-21 | major | The README asks the user to check the bands 'before sending' but quotes the old per-seed L3 rule. | applied: README correction 7 quotes the pooled three-way L3 rule; question 9 says when the bands can still change |
| FC-22 | minor | B.7 and N.10 make the evergreen items the `queue_empty` buttons, which the user must tap. | applied: B.7 and N.10 (evergreen runs by itself; queue_empty offers unreleased held blocks) |
| FC-23 | minor | Buttons exist only on needs, and every raised need must use a registered code. | applied: N.10 sandbox_disk, drop_confirm, build_stop_confirm; R.3 prunes sandbox files first |
| FC-24 | minor | On the Telegram path the failsafe starts at 60 s, and N.5 reports 'not verified' at 90 s, only 30 s in, while jobs may take 45 s to exit. | applied: R.2 failsafe applies the 55 s and 75 s timers itself; N.5 wording |
| FC-25 | minor | Two definitions exist of the class frozen in `criteria.yaml`. | applied: C.10 and the sheet match G.5 (learner GPU in the CPU-physics hardware class) |
| FC-26 | minor | M2 builds two rulesets, but D.3 and E.2 need three, and ruleset C is the one that guards the `ledger` branch. | applied: E.4 M2 builds the three rulesets |
| FC-27 | minor | The code shipped to Vast omits `pyproject.toml`, without which `uv sync` fails, and syncs without `--only-group science`. | applied: D.1 and D.6 ship pyproject.toml and sync only the science group |
| FC-28 | minor | M2 requires a build session to run `gh auth logout`, the exact command N.8's forbidden prefix rules block for those sessions. | applied: N.7 and E.4 M2 log out through the launcher's gh_logout_programme |
| FC-29 | minor | N.9 step 4 publishes 'only' five files. | applied: N.9 step 4 publishes drop.js and the vendored crypto files |
| FC-30 | minor | The Phase 2 go can arrive at L3, about a week into the campaign, while M2–M3 are still being built. | applied: B.7 and N.8 (an early Phase 2 go is recorded and M8 runs after the milestone in progress) |
| FC-31 | minor | I2 omits the 'no worker ever started' exception that D.2's rollbacks and R.7/R.10's reconciliation rely on. | applied: D.2 I2 exception for instances whose lease shows no worker start |
| FC-32 | minor | As a generic pattern, 'four groups of four lowercase letters' matches ordinary English (for example 'then open this page'). | applied: N.5 no longer matches four lowercase groups; the app password is matched by value |
| FC-33 | minor | Q0 lists trainer correctness (Gymnasium HalfCheetah) and the massless-device test as campaign content. | applied: B.7 Q0 (trainer correctness and the massless-device test are E.2 test groups, not campaign jobs) |
| FC-34 | minor | H.7 says D.1 explains how the sandbox is separated on a rented host, and D.1 points back to H.4. | applied: D.1 and H.7 (sandbox moves are not built; the tick box says so) |
| FC-35 | minor | N.8 and H.4 put user-opened Codex sessions inside the build jail. | applied: E.9 and H.10 (interactive sessions work inside the build jail through sprintctl build shell) |
| FC-36 | minor | Settings defined elsewhere appear neither in D.4's control list nor as SSH-only keys: `promote_per_day`, `sandbox_keep_days`, `build_sessions_per_day`, `build_hours`, `build_session_cap_h`, `polite_min_mib`, `lab_silence | applied: D.3 declares build, bootstrap and guard keys sprintctl-only; D.4 lists polite_min_mib and sandbox_keep_days |
| FC-37 | minor | The canary expects every write under `state/needs/` to fail, but `sprintctl need create` inside the jail must write `state/needs/requests/`. | applied: N.8 canary allows the need-request spool |
| FC-38 | minor | With 15-minute codes, pausing after three unanswered codes yields three codes by 15:40 (14:40, 14:55, 15:10). | applied: N.11 expects three codes by 15:40 |
| FC-39 | minor | L0's tiny pipeline already creates an S2 checkpoint in M1a. | applied: E.4 M1b, E.3, B.7 and the sheet (register Q3–Q7 before the first Q3 S2 job) |
| FC-40 | minor | The held-out Phase 2 start states must be defined, and immutable, at the M1a freeze, but the sprint model and environment only exist from M8. | applied: G.5 reserves start-state seeds 10,900–10,999 for Phase 2 |

