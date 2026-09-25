# 02_RESEARCH_DIRECTIONS — the reasoning behind the programme

Written 2026-09-23 by Claude, from both SMAT papers read page by page, the MyoAssist code at `b1baf69`, a GPU and CPU
probe run on `sail-gpu` the same day, twelve verified literature clusters (`01_PAPERS.md`) and ten implementation
digests (`03_PAPER_DIGESTS.md`). Part G of the master prompt turns this into frozen criteria and Part B into the
campaign. Status words follow the KB's vocabulary: nothing below is "validated"; everything is "proposed" or
"prepared" until the runner executes it.

## 0. The short version

1. **SMAT can only be reproduced by search.** The papers give the architecture, the reward equations and weights,
   the PPO settings and the stage budgets, and leave about forty implementation choices open. No code or checkpoint is
   public (SMAT-Exo is still a placeholder; checked 2026-09-22 and 2026-09-23). A reconstruction therefore means
   hundreds of registered training attempts judged against bands fixed before any Stage-4 result exists.
2. **The paper's headline simulation numbers are partly built into its rewards.** The Stage-4 exo reward is maximised
   by velocity-proportional torque (u = ω/2 rad/s, saturating at 0.814), and with the torque-rate penalty its optimum
   is a 27 ms low-pass of that law. That alone predicts the reported peak (0.83), the small negative-power fraction
   (10 %), the speed-invariant offline peaks (11.6–12.3 Nm at 15 Nm) and the lag behind the biological hip moment. The
   reported 10.1 % activation reduction compares a Stage-2 human with a Stage-4 human retrained under a 15× effort
   weight and a new penalty on exactly the four reported muscles. So the questions that decide what SMAT shows are the
   **controls the papers did not run**: the reward-matched zero-torque human (B0), the matched rate-limited velocity
   controller (B2), the matched phase profile (B4, SMAT's own average torque replayed open-loop), a published
   delayed-feedback hip controller tuned the same way (B6), and the proper "minus r_exo4" ablation (A4).
3. **Throughput makes the search feasible on this server.** The probe measured, physics only: about 58,000 control
   transitions per second on 32 CPU processes (153 MB each when loaded from `.mjb`) and about 235,000 per second on the
   5090 with MuJoCo Warp at 8,192 worlds, after one flag (MULTICCD off). A full 547 M-transition SMAT pipeline is
   therefore hours, not the authors' ~150 h. With contacts, GPU and CPU trajectories diverge chaotically, so the GPU
   backend is certified by statistical and learning parity, and every reported number is measured on CPU physics.
4. **Three paths to a paper, one of them almost guaranteed.** (i) A rigorous reproduction with mechanism attribution
   and an open implementation (it yields a paper whether SMAT reproduces or not, provided the positive controls pass);
   (ii) an open, parity-certified GPU benchmark of staged human-device co-adaptation with matched baselines; (iii) a
   method result: better than SMAT at equal budget, equal at far lower budget, or robust to held-out human partners, and
   in Phase 2, simulated sprint-time reduction with a realistic cable exosuit.
5. **Phase 2's most promising hypothesis is hip-flexion assistance**, not the hip extension Moon et al. used: a 2026
   simulation study found hip-flexor strength has the largest leverage on top speed, and Lambda-Hold's speed ceiling
   is set by hip-flexor force–velocity. The main risk is the human model: MuJoCo Hill-type muscles are weak at sprint
   speeds, and the one open sprint simulator (Bolt) sprints only with doubled muscle strength.

## 1. What the SMAT papers show, and what they do not

**What was measured in simulation** (O = arXiv 2603.07618, IROS 2026; E = arXiv 2608.00715): a 26-muscle 3D human in
MyoAssist (0.1) learns to walk at 1.25 m/s by imitation (Stage 1, ~320 M steps); it adapts to the device's mass at zero
torque (Stage 2, ~160 M); with the human frozen, an exo actor learns at 6 Nm (Stage 3, ~1.1 M); both train at 25 Nm
(Stage 4, ~66 M). Reported: left–right joint symmetry r > 0.92 and toe-off at 57.8 % (right) and 58.5 % (left) after
Stage 1; Stage-2 trajectories within 3.6° RMSE of Stage 1; a Stage-4 peak normalised command of 0.83 at 75 % of the gait
cycle; negative power in 10 % of the cycle; right-side mean activation lower in Stage 4 than Stage 2 by 13.5 % (rectus
femoris), 10.5 % (iliopsoas), 9.7 % (hamstrings) and 6.6 % (gluteus maximus), mean 10.1 %; E's bilateral six-group
mean 6.1 %; ablations: Stage 4 without Stage 3 collapses to a 0.14 peak with 32 % opposing power (mean of three runs,
the only multi-run curve), Stage 3 alone saturates bang-bang, "no r_exo4" (which also skipped Stage 3) gives a slight
constant extension torque with 40 % negative power. Offline replay on recorded walking (Molinaro et al.'s dataset; 10
people; 0.6/1.2/1.8 m/s; 15 Nm scale): peaks of 11.6–12.3 Nm and a 9–20 % phase lag.

**What the page-by-page extraction corrected** (`research-data/infra/smat_spec.json`):

- The r > 0.92 is **left–right symmetry across all joints**, not hip correlation with the reference (the request
  paraphrased it as "hip-kinematics correlation"). Symmetry ignores amplitude; Part G adds a reference-plausibility
  floor, labelled as ours.
- The 3.6° RMSE compares Stage 2 with Stage 1, not with the reference.
- The activation comparison is confounded by the reward change (muscle effort 0.01 → 0.15, a squared hip-activation
  penalty with weight 5 on exactly the reported muscles, hip imitation off, speed weight 0.8 → 1.5). No
  reward-matched zero-torque control exists in either paper.
- The Stage-4 exo reward's optimum is velocity-proportional, and its torque-rate penalty turns it into a first-order
  filter (u_t = 0.529 u*(ŵ_t) + 0.471 u_{t−1}); the Stage-3 reward's optimum is bang-bang. Several "emergent" behaviours
  are reward optima.
- The papers' explanation of the Stage-4-only collapse ("the second term rewards minimising torque") does not match the
  algebra (the reward's gradient at u = 0 is 0.3 ŵ, so zero torque is not optimal). The collapse is real in their
  figure, but its cause is untested: exploration noise costs, critic bias after the reward switch, or human-side terms.
- The only seed statistic in either paper is "mean of three runs" for one ablation curve. The main pipeline is one
  run.
- MyoAssist's own training code of the SMAT era contains a target-speed randomiser bug that draws targets up to 5 m/s
  when the minimum and maximum are both 1.25 m/s. Whether SMAT trained with it is unknown; the registry keeps a
  diagnostic arm that reproduces it.
- Hardware facts (not simulation targets): device 5.94 kg; human results (−19.7 % net metabolic rate versus the
  passive device, −9.1 % versus no device, +13.1 % device burden, hip ROM 44 → 62°, 18.07 W per hip command-based
  positive power) need people and a calorimeter, and are never tuned toward.

**What this means for the reproduction.** Reaching the published peak and negative-power fraction tests that the
reconstruction is faithful. Reaching the 10.1 % tests that it is faithful *and* that the reward change and the torque
together do what the paper says. Only B0, B2, B4, B6 and A4 say *why*. The programme reports all of them side by
side.

## 2. The adjacent state of the art, and where each leaves room

- **UniExo** (the SMAT authors, 2026-09-17): an 80-muscle MyoLeg on MuJoCo Warp via mjlab at ~37,000 steps/s; walking at
  three speeds, turning, jogging, backward walking; an exo actor initialised from a hip-moment predictor, then
  co-adapted with a shared critic; six participants; no metabolic data; no velocity or phase baseline; code promised.
  It makes "SMAT on the GPU" unpublishable as a headline, raises the bar for "better", and shows the throughput route.
  It keeps SMAT's 0.3/0.15 power terms, so the velocity-law analysis applies to it too.
- **Two-agent human-device training is not new**: a human and a knee prosthesis with two actors and one critic
  (NeurIPS 2022), a human and a hip exoskeleton with a centralised critic in OpenSim (2026), Assistax (RLC 2026: a
  robot-plus-humanoid benchmark evaluated on 625 held-out partners). Novelty must come from isolating the mechanism
  and from partner transfer, not from the two-agent framing.
- **Exo-Plore** (ICLR 2026, arXiv 2601.22550), the nearest work to the reproduction paper: a 164-muscle human driven
  by deep RL wears a hip exoskeleton running Samsung's delayed output feedback law (τ = κ·u(t − Δ),
  u = sin θ_r − sin θ_l; Lim et al., T-RO 2019), with the human reward tuned to match measured assisted-gait trends,
  and a surrogate finds speed-dependent (κ, Δ) optima; code public (non-commercial licence). It never compares a
  learned policy, so B6 puts its controller into the matched comparison. It also warns that Hill-type muscles are
  weak for fast running. MDOFC (IEEE TNSRE 2026) tunes a harmonic two-parameter variant the same way.
- **A simple rule matches SMAT's positive-power headline**: PositiveAssist (IEEE/ASME TMech 2026), a fixed-parameter
  energy-gated controller on two thigh IMUs, keeps more than 97.8 % of delivered power positive in walking. The 0.98
  ratio therefore cannot separate learned from simple control; activation, joint-power offload and the matched arms
  must.
- **Barati et al.** (RA-L 2026): a policy trained against a fixed reflex walker cut metabolic cost 15.2 % on hardware
  (n = 8), a ready-made "no co-adaptation" comparator.
- **The Luo–Collins dispute**: Luo et al. (Nature 2024) learned hip assistance in simulation; Collins et al. (2026
  preprint) replicated the average torque profile on hardware (10 people, no significant saving) and argued the claimed
  savings exceed physiological limits; Luo et al. replied that a fixed profile is not their learned policy and that a
  valid replication must first reproduce a known result on the same setup; Nature added an Editor's Note on data and
  code on 2026-07-27. Three lessons are built into the gate: pass known-answer controls before any "does not
  reproduce" verdict (Part B.6), run Collins' experiment cheaply in simulation (B4 replays SMAT's own average torque
  open-loop at phase shifts of −10 % to +30 %), and release everything. SMAT's last author, Xianlian Zhou, co-authored
  Luo et al. 2024 and its 2026 response, so neither line of work is independent evidence for the other; the paper says
  so.
- **Park, Song and Kang** (2026): SCONE/Hyfydy teacher, TCN student on one thigh gyro, hardware waveform agreement in
  five people; their public repository is a precursor without the exoskeleton, student or deployment package. **Choi,
  Park, Halilaj and Kang** (2026): musculoskeletal motion imitation for personalised exo control on the same Hyfydy
  body (600 M steps in about 48 h, with the physics on 24 CPU cores and the RTX 5090 only for training updates), a
  6.95 % simulated metabolic saving from hip assistance when jogging at 2.0–2.2 m/s (13.8 % at the ankle), and a reward
  change during exo fine-tuning that leaves part of that saving unexplained (the same confound B0 addresses here).
- **MyoAssist 1.0** (bioRxiv, 2026-08-26): the framework SMAT used (0.1), now composing bodies at runtime, with the
  26-muscle leg marked beta and RL configs only for the 22-muscle 2D model. It already offers separate human and exo
  RL agents, spline exo controllers and standardised evaluation, on the CPU and without a staged protocol, and an
  unpublished repository (`Luk7-sb/myoassist-dual-ppo-control`, created 2026-08-26) already stages human and exo PPO
  on MuscleMimic's JAX/MJX stack. The benchmark direction (rank 2) therefore rests on the staged protocol as the unit
  of evaluation, matched simple-controller baselines and certified parity, not on "GPU co-adaptation exists".
- **"Beyond Kinematics"** (2026-09-18): MuJoCo walks resemble Hyfydy walks kinematically, but MuJoCo muscle activations
  match EMG poorly (r 0.11 against 0.40). Simulated activation reductions are weak evidence of physiological benefit on
  their own; every write-up says so.

## 3. The reproduction search space, and why it is searched rather than guessed

`smat_spec.json` lists 39 unspecified choices and 21 inconsistencies between or within the papers. Part B.3 ranks the
ones that matter most, from the on-policy literature and MyoLeg-specific evidence:

1. **How bounded muscle actions are produced, and where entropy is measured.** A 2026 MyoLeg study found a clipped
   Gaussian put 89 % of muscle commands within 5 % of a bound; a tanh mapping with entropy measured on the executed
   actions cut that to about 19 %, and a Beta policy to about 15 %. The initial log-std was among the most sensitive
   choices in the largest on-policy study. MyoAssist's code default is −2.0 and its tutorial config 0.0, and it shares
   one log-std vector across both actors, which also breaks freezing.
2. **Observation normalisation** was crucial on four of five MuJoCo tasks in that study; MyoAssist has none.
3. **The critic and the update form**: what the critic sees, value normalisation, the reward-to-actor assignment, one
   ratio or two, and time-limit bootstrapping.
4. **Step counting**: aggregate (the throughput arithmetic makes it the likely reading: 28 h per 100 M on 8 cores is 992
   steps per second) or per environment (32× more; Stage 3 would get 537 PPO updates instead of 16.8, which matters
   because 16.8 updates barely move a policy).
5. **The reference motion** (MyoAssist's file has undocumented provenance) and phase handling.
6. The human observation, episode rules, the physics step, stage-transition details, the frozen-human action mode, the
   device mass and the Stage-1 model, and the hip-imitation release (O versus E).

The campaign's Stage-1 search (Q2) runs a balanced orthogonal array of 24 configurations over the first, second,
third (value normalisation), fifth and sixth groups at a cheap tier, promotes the best by successive halving, selects
exactly one configuration at the full budget on selection seeds, and then confirms it on three fresh seeds: only the
confirmation seeds count and parent Stage 2, because the best of many screened configurations is biased upward by
construction. Twelve configurations also run at the full budget as a tier calibration, so the dashboard shows whether
the cheap tier discards real winners (the cheap tier is trusted only if it recovers at least 60 % of the full-budget top
third). An era-faithful pipeline (MyoAssist's clipped Gaussian, shared log-std, no normalisation) is carried alongside,
because the published Stage-4-only collapse may come from exactly those defects.

## 4. The throughput lever, measured

The probe (`research-data/probe/results_2026-09-23/`; ~169 s of GPU time with only same-account forge jobs present):

| Backend | Setting | Control transitions per second (physics only) | Memory |
|---|---|---|---|
| CPU, 1 thread | model step 0.002 s, 10 substeps | ~2,040–2,100 | 153 MB per process from `.mjb` (560 MB from XML) |
| CPU, 32 processes | same | ~57,900 (87 % per-process efficiency) | ~5 GB |
| GPU, MuJoCo Warp 3.14, 8,192 worlds | same, MULTICCD off | ~235,000 | 3.6 GB VRAM |

At the MyoAssist default physics step (1/1200 s, 24 substeps) divide by about 2.4. Learner, policy inference and
environment code are not included; M1 and M4 measure end-to-end numbers. Rough consequences: one full four-stage
pipeline takes hours on either backend instead of the authors' ~150 h, and Stage 3 + Stage 4 branches (67 M
transitions) take minutes on the GPU. That is what makes seeds, controls, cross-play and sweeps affordable.

Two facts shape the design. First, stock models do not load in MuJoCo Warp (non-zero geom margins on mesh pairs with
MULTICCD on); disabling MULTICCD fixes it, but it also changes CPU contacts in 30–42 % of steps, so both backends must
run with the same flag and the model declares it. Second, **trajectory parity is impossible** with contacts: identical
Warp worlds start 5e-10 apart and reach 1e-2 within about 75 steps, and CPU MuJoCo itself amplifies a 1e-7 perturbation
into 4e-3 within 100 steps. Contact-free dynamics match to float32. Hence the certificate of Part B.5: feature canary,
contact-free parity, statistical parity of every gated metric, learning parity, and evaluation always on CPU physics.

## 5. The campaign, and what each block answers

Q0–Q1 prove the plumbing and measure throughput with both learners. Q2 selects and confirms one Stage-1
configuration. Q3 adds the passive device and calibrates evaluation noise; Q3t builds tuning blocks that no claim uses.
Q4 first settles the Stage-3 step-count reading by a known answer (the Stage-3 reward's bang-bang optimum), then runs
Stage 4: three independent pipelines and the first L3 verdict, which escalates to five and ten pipelines only while it
is inconclusive. Q5 tunes the simple controllers on the tuning blocks and runs every control on the claim blocks, each
with the same reward, stages, budget and (for B2-w) positive work as SMAT. Q5b adds the schedule contrasts, Q6 the
fourth and fifth pipelines, Q6p the device-naive partner humans and the first cross-play matrix, and Q6b the blocks the
equivalence tests need (10 by default, re-estimated blind after 5). The user decides which held L4 block (Q8) to
release, with the evidence on the dashboard, and whether to start Phase 2. The walking campaign is about 31 B
transitions, roughly 18 days on the CPU alone; the first L3 verdict comes after about a week.

Decision points, each a Telegram need with the evidence attached:

- If no configuration confirms L1: the dashboard shows the closest ones and why they fail; the user chooses between
  extending the search (for example the external reference or a different physics step) and accepting a "Stage 1 does
  not reproduce under these choices" finding. The known-answer control K-env (MyoAssist's own trainer against ours on
  the same model) distinguishes "our trainer cannot learn to walk" from "this model and reward do not walk at this
  budget".
- If L3 is REPRODUCED: the key numbers are not the 10.1 % but the device-attributable reduction (SMAT − B0) and the
  mechanism outcomes against B2, B2+, B4, B6 and B8 on the same blocks. If B2 or B0 explains most of it, the mechanism
  paper is the result, and it is a strong one.
- If L3 is NOT REPRODUCED with the known-answer controls passing: "under reconstruction R with deviations D, we did
  not obtain X" is the result, with the sensitivity to each registry choice as the analysis. INCONCLUSIVE after ten
  pipelines is also reported as such, with the achieved intervals.

## 6. Mechanism hypotheses, stated before the evidence

- **H-reward** (Part G.7 M-reward): most of the Stage-4 activation reduction comes from the Stage-4 human reward
  (effort weight 0.15 and the hip-activation penalty) rather than from the torque. Test: 2 · R(B0) − R(SMAT) > 0 on
  paired blocks.
- **H-velocity** (M-velocity): a matched closed-form velocity controller, with the human co-adapted at the same budget,
  reward and stages, reaches SMAT's reduction within ±2 percentage points. Test: SMAT versus B2 by two one-sided tests
  on at least 10 blocks (B1, B2+ and B3 secondary, never "best of"). The same test against B6 (M-simple) answers the
  reviewer's version: does the learned policy beat a published two-parameter controller tuned the same way? M-learned
  requires SMAT to beat B2, B2+ (a lead-compensated filter), B6 and B8 (the best linear policy on the same inputs).
- **H-stage**: the benefit of staging comes from the initialisation Stage 3 provides, not from freezing per se. Tests:
  B5 with and without a behaviour-cloned velocity-law warm start; K1 (frozen-then-joint versus joint-throughout with
  identical reward and torque schedules).
- **H-partner**: a device actor co-adapted with one simulated human loses part of its benefit with independently
  trained humans. Test: the cross-play matrix on device-naive partners, and the device × partner-origin interaction in
  a 2 × 2 of (SMAT, B2) devices by (SMAT-adapted, B2-adapted) humans (a fixed law's humans still co-adapted to it).

These are hypotheses to test, not results to aim for; the bands and tests are frozen in Part G whatever they predict.

## 7. The sprint thesis (Phase 2)

- **The endpoint** is simulated 200 m time from a standing start, with the 100 m split and top speed secondary, and
  incomplete runs as failures. Moon et al. (Science Robotics 2023) is the only human evidence, and it is weaker than it
  looks: 0.97 ± 0.41 s (SEM) faster over 200 m with hip-extension assistance, nine non-elite men, P = 0.047 uncorrected
  and about 0.09 after correction across the three distances, two of the nine slower, the second 100 m not significant,
  and no "suit worn, assistance off" arm. The simulated comparator is therefore C1-matched: the same human wearing the
  device at zero torque and trained for exactly the assisted condition's budget. Unless the simulated human sustains
  6 m/s (Moon's runners averaged about 6.1 m/s), the endpoint is named "fast-running 200 m time".
- **The human is the hard part.** Lambda-Hold reaches about 4.7 m/s in SCONE/Hyfydy with a minimal reward, threshold
  control and event-synchronised holds; its code is unreleased, it has not been run in MuJoCo, and its muscle strength
  is uncertain (its baseline settings match a public config with doubled strength). MyoLeg reached 5.44 m/s
  only as the best of 20 rollouts with DEP-RL. Bolt sprints at 12.5 m/s but with doubled muscle strength, and its
  authors lost realistic sprinting when they swapped in MuJoCo's constraint solver. So the first Phase-2 job is a cheap
  solver-and-speed probe on MyoLeg at normal strength for each human route; the replication gate (median ≥ 4.0 m/s over
  five seeds, published reward unchanged, strength unchanged) decides whether any device work happens.
- **Where to assist.** Hip-flexor strength has the largest leverage on top speed in a 2026 simulation study, and
  Lambda-Hold's speed ceiling is hip-flexor force–velocity. Hip-flexion assistance in late stance and swing is
  therefore the lead hypothesis; Moon-style extension and bidirectional assistance are the comparators.
- **The same fact is the main threat to that hypothesis.** If the model's top speed is capped by its hip-flexor
  force–velocity curve (Lambda-Hold reached 6.5 m/s only with maximum shortening velocity doubled), a hip-flexion gain
  may be patching a model weakness rather than helping a sprinter. Every assisted result is therefore reported beside
  the same human with shortening velocity doubled, as a labelled diagnostic, and the paper states how much of the model's own deficit the device
  recovers.
- **Device realism decides whether a gain is real**: tension-only cable, attachment-dependent moment arm, compliance,
  delay, a torque-speed-power envelope, motor electrical dynamics (which change assisted-movement simulations far more
  than device mass and inertia do; Nguyen et al. 2020) and mass, from measured parameters or swept when unknown. An
  ideal-actuator gain that vanishes with the cable model is reported as such. No simulation of any device reducing
  sprint time was found (checked 2026-09-23), so a positive result here would be the first.
- **What would kill it**: the replication gate fails on every route; or even the ideal actuator at matched budgets
  cannot reach the assistance gate (0.5 s or 2 % versus C1-matched) in the fixed-profile and staged conditions;
  then the finding is about the limits of the model or the device class, and it is written as such.

## 8. The ranked portfolio, with kill rules

| Rank | Direction | Why it ranks here | Kill rule |
|---|---|---|---|
| 1 | **Reproduction and mechanism paper** (Phase 1) | Always yields a result once the known-answer controls pass (REPRODUCED, NOT REPRODUCED or INCONCLUSIVE, each with the mechanism outcomes); answers the professor's question; B0 and B2 are cheap on the GPU | None; if L0–L2 fail repeatedly after the Q2 extension, publish the "does not reproduce under documented choices" result with the sensitivity analysis |
| 2 | **Open GPU benchmark of staged co-adaptation** | Nobody has released one with matched baselines and certified parity; UniExo's code is not out | If learning parity fails on every geometry, the benchmark is CPU-only and ranks below 3 |
| 3 | **Partner transfer / better (L4)** | Cross-play is untested for any human-device pair in simulation; fewer transitions is plausible with GPU batch geometry | If SMAT keeps at least 90 % of its benefit on device-naive partners and M-velocity holds, there is nothing to improve on: stop |
| 4 | **Sprint-time reduction (L5)** | The lab's goal; the hip-flexion hypothesis is new and testable | The replication gate fails on all routes, or the ideal-actuator gain misses the assistance gate |
| 5 | **Ambitious extras** (clutch or energy-recycling actions, personalisation latents, device co-design) | High upside, only after 4 has a passing human | Each is a registered candidate that must survive matched budgets and the realistic actuator |

## 9. Venue and timeline (checked 2026-09-23)

The internal manuscript is due 2026-12-07; the reproduction and mechanism paper (rank 1) is realistic by then if Q2
finds a walking configuration within about two weeks. IROS 2027 (Florence, 26 September–1 October 2027) has its paper
deadline on 2027-03-01 per the IEEE RAS calendar; RA-L papers accepted between 2026-08-01 and 2027-04-30 can be
presented at IROS 2027 (there is no longer an RA-L-with-IROS-option track). Default route: RA-L for the rank-1 paper,
then IROS presentation by transfer; T-MRB for a longer version; Science Robotics only for a passing L5.

## 10. Risks and open questions

- The exact SMAT body model cannot be recovered (MyoAssist 0.1 era; the 26-muscle leg is beta in 1.0); the
  reconstruction is on a documented, hashed model, and the paper says so.
- The reference motion's provenance is undocumented; an external dataset is a registered alternative.
- Simulated activation is weak evidence of physiological benefit in MuJoCo; claims stay in simulation terms.
- The GPU backend may pass statistical parity yet fail learning parity (Stage 1, or Stages 3–4); then it serves
  screening or Stages 1–2 only.
- L3 is judged on pooled means with a three-way verdict; with a large seed spread even a faithful reconstruction can end
  INCONCLUSIVE at ten pipelines, and that is reported, not hidden.
- Before the first Stage-4 job, the hashes of the gate and the campaign are stamped publicly (OpenTimestamps and the
  public Pages site; an OSF or Zenodo record is optional), so a reviewer can check that the bands came first.
- Disk on the shared server is tight (80 GB free of 915 GB on 2026-09-23, with the forge's floor at 60 GB); the programme
  runs lean and stops before it could push the forge below its floor.
- If the SMAT authors send materials, the exact-replay mode keeps them separate from the reconstruction.
