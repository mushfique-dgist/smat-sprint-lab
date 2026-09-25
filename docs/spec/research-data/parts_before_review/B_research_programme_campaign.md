## PART B — The research programme: the reconstruction, the search space, the GPU track, the controls, the pre-loaded campaign, and Phase 2

`02_RESEARCH_DIRECTIONS.md` holds the reasoning behind this part; `research-data/infra/smat_spec.json` holds the
paper-level specification (every equation, weight, stage rule and published number with its page);
`research-data/infra/myoassist_facts.json` holds the code-level facts about MyoAssist at `b1baf69`;
`research-data/probe/results_2026-09-23/` holds the measured throughput, memory and backend facts. Use them; do not
re-derive them.

### B.1 The questions, in the order they are answered

1. **Can SMAT's simulated results be reconstructed without the authors' code?** Stage 1 walking (L1), Stage 2 with the
   passive device (L2), Stage 4 torque shape, negative-power fraction and activation reduction, and the published
   ablation directions (L3), under the frozen bands of Part G.
2. **What produces the effect?** The papers change the reward and the torque at the same time and the Stage-4 exo
   reward already encodes a velocity-proportional law (Part G.1). So: how much of the activation reduction is the
   reward change alone (B0), how much is reward-shaped velocity feedback (B1–B3), how much needs a learned,
   co-adapted controller (SMAT versus the matched controllers), and how much is the staging itself (the schedule
   contrasts K1–K3)?
3. **Does the co-adapted device generalise to humans it was not trained with?** The cross-play matrix (Part G.2 L4c).
4. **Can it be better** at equal budget, or equal at far lower budget (L4)?
5. **Phase 2:** does staged co-adaptation of a physiology-grounded sprinting human and a realistic cable exosuit reduce
   simulated 200 m time, and does the gain survive the realistic actuator and matched baselines (L5)?

Every answer, positive or negative, is a result (Part G.7).

### B.2 The reconstruction (Phase 1)

**Body and device.** Compose `myo_sim` `myolegs26` with `assist_sim` `Hippo_L1` through MyoAssist's composer at
`b1baf69` (`myoassist_utils.compose.compose_env_model(msk_key="myolegs26", device_key="Hippo_L1",
planar_root=True, export_path=…)`, which calls `assist_sim.load_combined`). `planar_root=True` replaces the free root
joint with six named root DOFs (`pelvis_tx`, `pelvis_ty` up, `pelvis_tz`, `pelvis_tilt`, `pelvis_list`,
`pelvis_rotation`; nq = nv = 46), which is what the SMAT imitation weights (E Table S3) and the reference file name.
Export the composed MJCF and its assets into `work/refdata/models/`, record every file's sha256, and **load the
compiled binary (`.mjb`) in every environment process**: the probe measured 560 MB resident per process when loading
the XML (the eight Hippo meshes have 251k vertices) and 153 MB from the `.mjb`. Facts of the composed model (probe,
2026-09-23): 26 muscle actuators (`dyntype`/`gaintype`/`biastype` muscle, `dynprm` 0.01/0.04), 26 spatial tendons with
96 site wraps and no wrapping geoms, 28 joint equality couplings with quartic coefficients (knee translations and
moving muscle path points), 12 sensors (4 touch, 8 joint-limit force), Euler integrator, Newton solver, pyramidal cone,
no `<option>` element (timestep 0.002 s from the default), mass 82.99 kg with the device and 78.09 kg without; the
device weighs 4.90 kg (actuator block 1.92 kg). Add an `<option>` element explicitly in our exported model so the
integrator, solver, iterations, cone and **`multiccd="disable"`** are declared rather than inherited (Part B.5 says why
the flag must be the same on both backends).

- **Stage 1 without the device, same layout.** Default: the same composed model with every device body's mass and
  inertia set to zero and its geoms non-colliding (`contype=conaffinity=0`), so observation, action and critic layouts
  are identical across stages; a unit test proves the total mass equals the bare human's 78.09 kg and that the bare
  `myolegs26` and the massless-device model produce identical trajectories for 300 steps from the same state and
  actions. Registered alternative: the bare human model with its own layout.
- **Stage torque scales** by setting the device actuators' gain (`gainprm[0]`) to 0, 6 and 25 Nm with control range
  [−1, 1], never by clipping forces; a physics audit asserts `|actuator_force| ≤ scale` every step and exactly zero in
  Stage 2. (On `Hippo_L1` a pinned command of 1.0 means +100 Nm; MyoAssist's "exo off" idiom does not apply.)
- **Device mass** is a registered choice: 4.90 kg as shipped (default), scaled to 5.94 kg (the papers' hardware), and 0
  (diagnostic only). The mass used is recorded in the claim.

**Why the environment is ours, not MyoAssist's.** The MyoAssist RL path at `b1baf69` has defects that change the
experiment (verified in the code, `research-data/infra/myoassist_facts.json`): the target-velocity randomiser passes its
arguments in the wrong order (`rl_train/envs/myoassist_leg_base.py:407–414`), so with minimum = maximum = 1.25 m/s six
resets produced targets from 0.94 to 5.0 m/s (fixed only on the unmerged branch `feat/prosthesis-rl`); resets restore
only the tracked joints, so the 3D hip and pelvis DOFs carry over from the previous episode; both actors share one
log-std vector, so freezing an actor does not freeze its exploration; "reset network after load" rebuilds modules the
optimiser no longer holds, so they never train; loading a previous policy cannot cross a change of observation or
action size; there is no staged freezing, no 26-muscle config and no batched backend. So `smatsprint/envs/walk26.py`
implements the environment on the composed model directly (Part C.8), reusing MyoAssist for composition, reference data
and cross-checks. Its tests include: the target speed is exactly 1.25 m/s on every reset; every DOF is set on reset; the
exo observation holds exactly its 18 inputs.

**Reference motion.** Default: MyoAssist's `short_reference_gait.npz` (one continuous 89.8 s trial at 500 Hz, mean
1.2815 m/s, about 81 strides of 1.109 s, 36 OpenSim coordinates including the 3D pelvis and hip DOFs; its subject and
provenance are undocumented, which the paper must say). Resample to 50 Hz (4,490 samples); the reference index advances
one sample per control step (its recorded cadence), episodes start at a random index in the first 80 %, positions are
not speed-scaled, and velocity targets are scaled by ρ(t) = 1.25 / ṗ_ref,pelvis_tx(t), as E writes it. Correct the
reference pelvis height to the composed model's standing height in both directions (MyoAssist corrects only positive
offsets). Registered alternatives: an external 1.25 m/s dataset from `01_PAPERS.md` (the motion-imitation cluster), and
a phase-matched lookup instead of time-indexing.

**Observations.** Human (registered variants; SMAT reports none): `h3d_default` = the tracked joint positions (without
`pelvis_tx`) and velocities of the 3D model, the 26 muscle activations, the 4 foot touch values and the target speed;
`h3d_phase` = the same plus sin/cos of the reference phase; `h3d_full` = plus muscle lengths, velocities and forces; in
Stage 4 each variant gains the two current normalised exo commands (the input layer grows by 2: existing weights copied,
the new ones initialised small, the scale a registered choice). Exo (all 18, fixed by the papers):
`[q_hip_r, q_hip_l, q̇_hip_r, q̇_hip_l]` at t, t−1, t−2 and the applied (post-clip) commands `[u_r, u_l]` at t−1, t−2,
t−3, raw radians and radians per second by default (dividing velocities by 2 rad/s is registered), history initialised
by repeating the first sample (zeros registered). Critic: the concatenation of both actors' observations plus the
full joint state by default (registered alternatives in B.3).

**Rewards.** Exactly E Eqs. 1–7 with E Tables S2–S3 weights (O's "hip flexion only" release is the registered
alternative), each term multiplied by dt = 0.02 s: speed `exp(−5 (v − 1.25)²)`; imitation `Σ w_i exp(−8 e_i²)` on
positions and on ρ-scaled velocities; mean activation penalty; activation-change bonus `mean exp(−4 Δa²)`; squared
hip-activation penalty over the eight actuators `iliopsoas_*`, `glutmax_*`, `rectfem_*`, `hamstrings_*` (Stages 3–4);
the Stage-3 exo term `0.5 u² sign(u ω)`; the Stage-4 exo term `0.3 u ω̂ − 0.15 u² − 2 max(0, |u| − 0.8)²` with
ω̂ = clip(ω / 2 rad/s, −1, 1); the torque-rate penalty; the joint-constraint penalty `max_k |f_k| / (m g)` from the
joint-limit constraint forces; the foot-force penalty above 1.2 body weights from the touch sensors. Activations are
`data.act`, excitations are the actions. Each term is logged separately. Unit tests check every term on hand-computed
states and the Stage-4 optimum (u = ω̂ for |ω̂| ≤ 0.8; 0.814 at |ω̂| = 1).

**Episodes.** Registered defaults: 1,000 control steps (20 s), terminate when `pelvis_ty` < 0.70 m or when a tracked
joint departs its reference by more than 0.2 rad (MyoAssist's shipped values), truncate at the step limit or the end of
the reference with value bootstrapping on truncation; reset from the reference state at the random index with every DOF
set and activations zeroed.

**Rates.** Control 50 Hz. Physics timestep is a registered choice: 1/1200 s (MyoAssist's environment default, 24
substeps; the default here because SMAT used MyoAssist), 1/1000 s (20 substeps), 0.002 s (the model's own default and
MyoSuite's, 10 substeps; half the cost). The physics sanity checks of Part C.10 must stay clean at the chosen step.

**Trainer and stages** as in Part C.8, with SMAT's per-stage hyper-parameters, per-actor log-std parameters (never a
shared vector), freezing verified by hashes, and stage transitions: S1 random init → S2 loads S1 (human and critic) → S3
freezes the human, re-initialises the exo actor, sets 6 Nm, swaps in the Stage-3 rewards → S4 unfreezes the human,
loads the S3 exo actor, grows the human input by 2, sets 25 Nm, swaps in the Stage-4 rewards.

### B.3 The registry of unspecified choices (the search space the user sweeps)

`smatsprint/choices/registry.yaml` lists every choice below with its options, its default (first) and a one-line note.
The papers are silent or ambiguous on all of them (`smat_spec.json` lists 39 items and 21 inconsistencies). Ranked by
the likely size of their effect (from the on-policy literature and the MyoLeg-specific evidence in `01_PAPERS.md`):

| Rank | Choice | Options (default first) |
|---|---|---|
| 1 | Human action mapping, log-std and where entropy is measured | Gaussian with tanh then affine to [0,1] (entropy on executed actions) · clipped Gaussian · Beta; log-std init −0.5 · −1.0 · 0.0 (a 2026 MyoLeg study found a clipped Gaussian put 89 % of muscle commands within 5 % of a bound) |
| 2 | Observation normalisation | running mean/std (clip 10), frozen at each stage end and carried over · none (MyoAssist has none) |
| 3 | Critic input, value target, reward-to-actor assignment, update form | full state, one advantage on the summed reward, one clipped ratio per actor with a shared advantage · two-head critic with per-agent rewards · product-policy single ratio; value normalisation on · off |
| 4 | Step counting | aggregate across environments (320 M total; 4,883 updates in S1) · per environment (32×; Stage 3 would get 537 updates instead of 16.8) |
| 5 | Reference and phase | MyoAssist reference, time-indexed · external dataset · phase-matched |
| 6 | Human observation | `h3d_default` · `h3d_phase` · `h3d_full` |
| 7 | Episode rules | height 0.70 m + 0.2 rad tracking · height only · height 0.65 m; 1,000 or 500 steps |
| 8 | Physics timestep | 1/1200 · 1/1000 · 1/500 s |
| 9 | Stage transitions | new optimiser per stage, critic carried · optimiser carried · critic reset at S3 with a value-only warm-up |
| 10 | Frozen-human action mode (S3) | stochastic · mean |
| 11 | Stage-4 input growth init | small random (std 0.01) · zero · default init |
| 12 | Device mass and Stage-1 model | 4.90 kg, massless device in S1 · 5.94 kg · bare human in S1 |
| 13 | Hip imitation release | E (all hip DOFs) · O (hip flexion only) |
| 14 | Checkpoint rule | final checkpoint · best training-return moving average (never an evaluation metric) |
| 15 | Network details | tanh hidden units with orthogonal init · ReLU/ELU |
| 16 | Diagnostic only | the MyoAssist target-speed randomiser bug reproduced (SMAT was built on MyoAssist 0.1 from code of that era; if a reconstruction fails with a fixed 1.25 m/s but succeeds with the bug, that is a finding) |

A config fixes one option for every choice; nothing is left implicit. A sweep names a subset (Part C.7).

### B.4 Evaluation

Part G.3 defines every metric and Part C.9 the protocol (reference physics, deterministic actions, 20 episodes of
12 s, first 2 s discarded, evaluation seeds from their own pool). Before any Stage-4 result, run the precision rule of
Part G.4. The offline replay (B.6) uses recorded walking.

### B.5 The GPU physics track (the throughput lever), with statistical parity gates

**What the probe established on 2026-09-23** (`research-data/probe/results_2026-09-23/`, GPU otherwise idle except
same-account forge jobs): `mujoco` 3.14.0, `mujoco-warp` 3.14.0 and `warp-lang` 1.17.0 install in user space and run on
the 5090. The stock composed model **fails** `mjw.put_model` ("geom pair (pelvis_geom_1, tibia_r_geom_1) has non-zero
margin … with MULTICCD enabled"); disabling MULTICCD makes both models load, with every feature accepted (26 muscles,
26 spatial tendons with site wraps, 28 quartic joint couplings, 156 mesh–mesh candidate pairs, sensors). Throughput,
physics only, at the model's 0.002 s step (10 substeps per control step): **about 235,000 control transitions per
second at 8,192 worlds** (2.35 M physics steps per second, 3.6 GB of GPU memory); the cold first compile took about
62 s. Native CPU: about 2,000–2,100 transitions per second per thread, **about 58,000 per second on 32 processes** (87 %
per-process efficiency), 153 MB per process from the `.mjb`. Parity: contact-free dynamics (activations, tendon
lengths, muscle forces) match CPU MuJoCo to float32 precision; **with contacts, trajectories diverge chaotically within
about 75 steps**, the contact sets differ from the first step, and MuJoCo Warp is not bitwise deterministic run to run
(two identical worlds start 5e−10 apart). Disabling MULTICCD also changes the CPU contact sets in 30–42 % of steps, so
**both backends use `multiccd="disable"` in every run**, and the model declares it.

**Consequences.** Trajectory-level parity is impossible and is not the gate. The gates are:

1. **Feature canary** for the exact model and versions: `put_model` succeeds with the declared flags; versions pinned
   in the lock (`mujoco`, `mujoco-warp`, `warp-lang`).
2. **Contact-free parity:** from 20 identical states with contacts disabled, 400 steps under identical excitation
   traces: activations, tendon lengths and muscle forces within float32 tolerance (relative 1e-3 on muscle force; 1e-3
   rad on joint angles after 400 steps).
3. **Statistical parity with contacts:** a fixed trained Stage-1 or Stage-4 policy with deterministic actions, 256
   episodes on each backend from the same initial-state distribution; for every metric the gate reads (symmetry r,
   toe-off, speed, fall rate, hip ROM, per-group mean activation, normalised peak torque, negative-power fraction,
   contact counts, peak ground-reaction force), the difference of means lies within one quarter of that metric's band
   half-width by two one-sided tests; distributions are compared by Kolmogorov–Smirnov and reported.
4. **Learning parity:** Stage 1 trained on the GPU backend with the registered batch geometry (for example 4,096 worlds
   × 16 steps = 65,536 transitions per update, the same batch, epochs and minibatches as SMAT), evaluated on the CPU
   reference, reaches L1 on 3 seeds and its L1 metrics are equivalent to CPU-trained Stage 1 at the same transitions
   within the L1 bands (two one-sided tests). A different rollout geometry is a registered choice, never silently
   swapped.
5. **Evaluation stays on the reference physics** (Part C.9), whatever backend trained the policy.

A **certificate** (`backend id, model hash, versions, code_id, parity report`) is issued when 1–4 pass, and is revoked by
any change to them. Until it exists, every job runs on CPU. If learning parity fails, the GPU backend serves the
screening tiers only (P0–P2) and every claim comes from CPU runs; the dashboard says so. **Throughput table** (on the
dashboard): transitions per second per world count (1,024, 4,096, 8,192), end-to-end training transitions per second
with the policy and PPO update included, GPU memory, compile time, and the equivalent hours per four-stage pipeline.
Estimates from the probe, physics only, for one 547 M pipeline: about 0.65 h on the GPU at 8,192 worlds and about 1.75 h
on 48 CPU threads at the 0.002 s step; roughly double at 1/1000 s and 2.4× at 1/1200 s; the real numbers, with the
learner and the environment code included, are measured in M1 and M4 and replace these on the dashboard.

Implementation route: a direct port of `walk26` onto `mujoco_warp` (observations, rewards, resets and terminations in
Warp or torch on the GPU) behind the same environment interface, or mjlab if it saves time (the SMAT authors' UniExo runs
on mjlab; MyoHub publishes `mjlab_myosuite`; see `01_PAPERS.md`, GPU cluster). Choose in M4 after reading both, and
record why.

### B.6 Controls, baselines, ablations and positive controls (walking)

Every arm below branches from the **same Stage-2 checkpoint and seed** as the SMAT arm it is compared with, runs the
same number of transitions as the stage it replaces, uses the same code, backend class and torque scale, and lets the
human co-adapt under the Stage-4 human reward for the same 66 M transitions unless it says otherwise. Paired blocks
(Part C.6) keep them together.

- **B0, reward-matched zero torque** (the missing control): continue the S2 human under the full Stage-4 human reward
  (muscle effort 0.15, hip-activation penalty 5.0, hip imitation off, speed 1.5, constraint and foot terms) for 66 M
  transitions with the device worn and torque scale 0. Its activation change versus S2 is the part of the "10.1 %" that
  the reward alone produces.
- **B1, instantaneous reward-optimal velocity law**: u = u*(ω̂) (u = ω̂ for |ω̂| ≤ 0.8, sign(ω̂)(0.3|ω̂| + 3.2)/4.3 above),
  25 Nm, human co-adapted.
- **B2, the matched rate-limited velocity controller** (the primary baseline): B1 passed through the discounted optimum
  of the torque-rate penalty, u_t = 0.529 u*(ω̂_t) + 0.471 u_{t−1}, 25 Nm, human co-adapted.
- **B3, velocity-gain family**: u = clip(k ω̂, −0.8, 0.8), k ∈ {0.5, 1, 2}, with and without a one-step (20 ms) delay;
  tuned on training seeds by a declared grid and rule.
- **B4, the matched phase profile**: a fixed hip flexion–extension torque profile over the gait cycle (phase from the
  hip-angle zero crossings or heel strike), shaped from the published SMAT mean profile or a standard hip profile,
  scaled to SMAT's peak and RMS torque; tuned by a declared grid.
- **B5, unstaged simultaneous training**: both actors learn from the S2 human at 25 Nm with the Stage-4 rewards from the
  first step, at the combined S3+S4 budget, with and without a warm start of the exo actor by behaviour cloning of u = ω̂
  (tests whether Stage 3 matters beyond initialisation).
- **Ablations as published**: A1 Stage 3 only (evaluated at 6 and at 25 Nm); A2 Stage 4 only from S2 with a random exo
  actor; A3 Stage 4 only from S2 without r_exo4 (as published, which also skips Stage 3). **A4, the proper ablation the
  papers lack**: full SMAT (with Stage 3) minus r_exo4 in Stage 4.
- **Schedule contrasts** (actor-update schedule separated from curricula, from the KB's program document): K1 frozen-
  then-joint versus joint-throughout with the same reward and torque schedules; K2 progressive versus final reward from
  the first active transition; K3 progressive versus final torque. Report environment transitions and per-actor updates
  both ways.
- **Critic variants** (MAPPO-style): full state versus actor observations only.
- **Cross-play** (partner transfer, Part G.2 L4c): every device actor with every held-out human (S2 and S4 humans of
  other independent pipelines, including the reserved partner seeds 900–949), no adaptation.
- **Offline replay**: the S4 exo actor fed recorded, unassisted walking at 0.6, 1.2 and 1.8 m/s (the dataset SMAT used
  is from Molinaro et al. 2024; locate the public Georgia Tech dataset, record its DOI and licence) at the 15 Nm scale;
  report peaks and the lag behind the biological hip moment, and the same numbers for B1–B3.
- **Positive controls before any "does not reproduce" verdict** (the lesson of the Luo–Collins dispute: a failed
  replication must first reproduce something known on the same setup): (P1) the programme's trainer and environment
  code, run on MyoAssist's shipped 22-muscle imitation tutorial config, walk stably within that config's budget;
  (P2) B2 lowers hip activation relative to zero torque on the frozen S2 human (a direction that follows from physics);
  (P3) L0–L2 pass. Without P1–P3 a failure is "not yet tested", never "does not reproduce".

### B.7 The pre-loaded campaign (what runs before the user touches anything)

At the end of M1 the runner registers these blocks, in this order, in `catalogue/campaign.yaml`; each block's candidates
and sweeps are fully pre-registered (configs, seeds, budgets, selection rules). The user can reorder, pause or remove any
of them (Part H.5). Times are rough, from the probe, for the CPU backend at 48 threads and about 20,000 end-to-end
transitions per second (to be replaced by the M1 measurement); the GPU backend divides them by roughly three to five.

| Block | Content | Budget | Rough time |
|---|---|---|---|
| Q0 Plumbing | L0 tiny pipeline; trainer correctness; composed-model hashes; the Stage-1 massless-device equivalence test | tiny | minutes |
| Q1 Calibration | CPU throughput table (8, 16, 32, 48 environment processes; RSS; transitions/s); evaluation noise floor; positive control P1 (2 seeds) | ~100 M | ~2 h |
| Q2 Stage-1 search | random design over registry choices 1, 2, 5, 6, 7, 8 (24 configs × 2 seeds at P1 = 40 M), successive halving to 8 at P2 (120 M) and 3 at P3 (320 M) on **3 fresh seeds** each, plus 3 random non-promoted configs at P3 × 1 seed (the miss check). Selection rule: the L1 criteria first (pass count), then the smallest symmetry deficit, then speed error | ~6 B | ~4 days |
| Q3 Stage 2 | on the selected config's 3 fresh S1 seeds: S2 at 160 M (device 4.90 kg); one seed at 5.94 kg | ~0.6 B | ~9 h |
| Q4 SMAT S3–S4 | on each S2 seed: S3 1.1 M + S4 66 M, with evaluations → **3 independent full pipelines** (L3 candidates) | ~0.2 B | ~3 h |
| Q5 Controls | on the same S2 seeds, paired: B0, B2, B4, A2, A3, A4 (66 M each), A1, B1 and B3 (cheap), offline replay, K1 | ~1.4 B | ~20 h |
| Q6 Seeds to 5 | two more independent pipelines of the selected config (S1–S4) plus their controls; the first cross-play matrix | ~1.4 B | ~20 h |
| Q7 Step counting | the per-environment reading for S3 (35 M), and for S4 only on the certified GPU backend | varies | GPU |
| Q8 Held: L4 attempts | declared at M4 from what Q2–Q6 show (e.g., fewer transitions with large-batch GPU geometry; partner-robust training); a phone need proposes them for the user's go | — | — |
| Q9 Held: Phase 2 human | the sprinting-human reconstruction and its replication gate (B.8) | — | — |
| Q10 Held: Phase 2 matrix | C0–C9 (B.8) | — | — |

Evergreen options for `queue_empty` (Part C.4): pre-registered top-up seeds of registered claims; refreshed baselines
after a code change; the noise and throughput refresh; clip renders; and each held block by name.

**Phase 2 start** (`<<PHASE-2-START>>` in the request): default **wait for the user's go**. When a claim reaches L3, or the
mechanism path passes, or Q6 finishes, the runner sends `ladder_crossed` with the buttons "Start Phase 2 (release Q9)",
"Strengthen Phase 1 first", "Later". Q9 can be released at any time from the Steer panel, including in parallel with
Phase 1 on spare capacity.

### B.8 Phase 2: sprint-time reduction

- **The human.** Three candidate reconstructions, each crossed with the same device and each labelled as an
  independent reimplementation where it is one:
  (a) **Lambda-Hold-style** control on the 80-muscle MyoLeg in MuJoCo: per-muscle threshold lengths λ, recruitment
  `e = clip[0,1](50 (l − λ) + 0.1 max(v, 0))` (only the velocity term rectified; no reflex delays in the paper),
  event-synchronised holds of 0.05–0.15 s triggered by ground-reaction events, the minimal forward-velocity and
  lateral-stability reward, SAC with gSDE as published (the programme's PPO as a registered alternative). The paper ran
  only in SCONE/Hyfydy with two seeds per curve, and its code is still "TBA" (checked 2026-09-23).
  (b) a **direct-excitation** human: imitation of open sprint data, or the Kinesis or MuscleMimic route (digests).
  (c) **Bolt** (Wang, Delp et al., arXiv 2609.11083, 2026-09-10; code public: `willwng/bolt`, `willwng/msk_envs`): a
  136-muscle model that sprints at 12.5 m/s from direct excitation, **but with doubled lower-body muscle strength**, which
  the gate forbids; it loads OpenSim models and has its own solver, and its authors report that realistic sprinting
  stopped emerging when they swapped in MuJoCo's constraint solver. Use it as (i) a strength-honest human (at normal
  strength, if it passes the gate) and (ii) evidence for a solver risk to test early on MyoLeg. A SCONE/Hyfydy human
  stays out unless the user confirms a lab licence (`<<SCONE-LICENCE>>`).
- **Replication gate first** (Part G.2 L5): median unassisted maximum speed ≥ 4.0 m/s over 5 seeds, published reward
  unchanged, no strength or shortening-velocity increase; complete 200 m episodes and fall rates reported. Known risks,
  stated up front: MuJoCo Hill-type muscles are weak at high speed (Exo-Plore, ICLR 2026) and MuJoCo activations match EMG
  poorly (a 2026 comparison); MyoLeg reached 5.44 m/s with DEP-RL only as the best of 20 rollouts, with strong torso
  wobble (Schumacher et al., appendix); a 2026 study on this GPU class found only about 7 % simulated benefit from hip
  assistance in running. So run a **cheap solver-and-speed probe before any device work**: can MyoLeg reach 4 m/s at
  normal strength with each human route and each MuJoCo solver setting? If the gate fails on every route, that is a
  finding about the models, reported as such, and device work proceeds only on a human that passes.
- **Where to assist.** Hip-flexor strength has the largest leverage on top speed in a 2026 simulation study (Yang, Lin
  and Pandy, Ann. Biomed. Eng.), and Lambda-Hold's speed ceiling is set by hip-flexor force–velocity. Moon et al.
  assisted hip **extension**. So register hip-flexion assistance during late stance and swing as a first-class condition
  beside the Moon-style extension profile, with bidirectional assistance as a third; this is the most promising sprint
  hypothesis the literature supports, and it is testable here first.
- **The device.** An ideal hip torque actuator first (to test the controller hypothesis), then the **realistic cable
  exosuit** (starting from MyoAssist's tendon-driven hip device `HMEDI_L1` and a custom model): tension only,
  attachment-dependent moment arm, cable compliance, a command-to-force delay, a torque-speed-power envelope, device
  mass on the pelvis and thighs; parameters from the Moon digest and the lab's bench measurements when they exist
  (never invented; unknown parameters are swept and labelled). A gain that exists only with the ideal actuator is an
  ideal-actuator result.
- **The task.** 200 m from a common standing start state; the finish interpolated between control steps; forward
  displacement, not path length; falls, timeouts, invalid contacts and numerical failures are failures with no time;
  fatigue is either modelled with a declared muscle-fatigue model or explicitly absent (then the 200 m is a
  steady-speed-plus-acceleration test and the paper says so).
- **The matched matrix** C0–C9 (KB `METHODS-AND-BACKENDS.md`): C0 no device; C1 worn at zero torque; C2 passive
  mechanics; C3 Moon-style fixed hip-extension profile; C4 frozen-human exo learning; C5 simultaneous two-actor PPO;
  C6 full staged SMAT; C7 stage and reset ablations; C8 centralised-critic MAPPO; C9 DiscoRL on a categorical codebook
  (after a conventional baseline works). Plus the phase-adaptive delay-compensated profile and the optimised
  biological-moment mapping of the KB's program document.
- **Ambition.** Curricula, factorisations, action representations, energy-recycling or clutch actions, personalisation
  latents, device-parameter co-design: each enters as a registered candidate and must survive matched budgets, matched
  physiology and the realistic actuator (Part G.2 L5). Nothing may change the human's strength, shortening velocity or
  contacts for the assisted condition only.

### B.9 Occupied territory, and what the programme can still claim

Name these when writing any claim; they are comparators, not reasons to stop (`01_PAPERS.md`, `02_RESEARCH_DIRECTIONS.md`
§6): SMAT itself (both papers); **UniExo** (the SMAT authors, 2026-09-17: GPU co-adaptation with the 80-muscle MyoLeg on
MuJoCo Warp via mjlab, walking to jogging, no velocity or phase baseline, no metabolic data, code not yet released), so
"SMAT on the GPU" is not a claim; two-actor human-device training with a shared or centralised critic already exists
(a human and a knee prosthesis at NeurIPS 2022; a human and a hip exoskeleton in 2026); Exo-Plore (ICLR 2026) models the
adapted end state; Barati et al. (RA-L 2026) trained against a fixed reflex walker; Luo et al. and the Collins
critique. Open, and the programme's to take: the reward-matched control and the mechanism attribution; the schedule
separated from the curricula; the cross-play partner-transfer test; an open, parity-certified GPU benchmark of staged
co-adaptation with matched baselines; and simulated sprint-time reduction under a realistic cable actuator.

### B.10 Model limitations to state in every write-up

The `myolegs26` leg is marked beta in MyoAssist 1.0, SMAT was built on MyoAssist 0.1, and the exact SMAT model cannot be
recovered, so the reconstruction is on a documented, hashed model, not "their" model; the reference motion's provenance
is undocumented; simulated activation is not EMG or metabolism, and MuJoCo muscle activations match EMG poorly (a 2026
comparison); the simulated device showed no hip-muscle burden in the papers while humans paid 13.1 %; offline replay has
no closed loop. The weekly note and the paper carry these lines.
