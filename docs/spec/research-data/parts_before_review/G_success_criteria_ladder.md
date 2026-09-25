## PART G — Success criteria: the ladder, the frozen bands, the paper gate (the part that governs all the others)

### G.0 Why this part comes first in importance

A programme converges to whatever its criteria reward. If they are loose, the user's steering converges to a
plausible pile of runs: a lucky seed, an unmatched comparison, a band widened after the fact. If they are vague, it
never converges. So the criteria here are:

1. **machine-checked**: `gate/check_gate.py`, a pure function of the ledger, decides every level and every gate;
2. **frozen against everyone who queues, steers or runs experiments, the user included**: no steering action, no
   sweep, no Promote, no dashboard control and no runner code path can edit `gate/` or a band (Part G.8);
3. **fixed before the evidence**: every band below is fixed now, in this handoff, before any Stage-4 result exists,
   from what the papers report, the discriminability between SMAT and its own ablations, and measurement precision;
   **never** from what comes out;
4. **laddered**: there is always a next rung, so every candidate on the Watch panel shows what it still needs;
5. **honest in both directions**: the programme must be able to come back with "it reproduces", "it does not
   reproduce", or "it reproduces but a simpler controller or the reward change alone does the same", each with
   evidence. The professor's scepticism is the reason this reproduction exists; a clean negative is a result.

Build `gate/` in M1 (Part E.4), before the first registered result, and test it harder than anything except the
state machine and the lanes.

### G.1 What the papers actually claim in simulation (read this before building `eval/`)

The handoff's page-by-page extraction of both SMAT papers (`research-data/infra/smat_spec.json`, digest in
`03_PAPER_DIGESTS.md`) corrects three readings that were in the user's request and in earlier notes. The gate uses
the corrected ones:

- **"Pearson r > 0.92" is left–right symmetry across all joints** (O p5: "strong bilateral symmetry across all
  joints (Pearson r > 0.92)"; E p6). It is **not** a correlation of the hip with the reference motion. Symmetry is
  insensitive to amplitude and would pass an abnormal but symmetric gait, so the gate adds a reference-plausibility
  floor that is labelled as **ours** (G.3, L1).
- **"RMSE < 3.6°" compares Stage 2 with Stage 1** of the same pipeline ("preserving the learned trajectories"), not
  with the reference.
- **The 10.1 % activation reduction is confounded.** Stage 2 and Stage 4 both wear the device, but the Stage-4 human
  was retrained for 66 M more steps under a different reward: muscle-effort weight 0.01 → 0.15, a new squared
  hip-activation penalty (weight 5.0) on **exactly** the four reported muscle groups, hip imitation switched off,
  forward-speed weight 0.8 → 1.5. No reward-matched zero-torque control was reported. This programme runs it (B0,
  Part B.6) and reports every activation effect beside it.
- **The Stage-4 exo reward pre-determines several headline numbers.** Alone, it is maximised by u = ŵ (normalised
  hip velocity) for |ŵ| ≤ 0.8 and u = 0.814 at |ŵ| = 1; with the torque-rate penalty the discounted optimum is the
  first-order filter u_t = 0.529·u*(ŵ_t) + 0.471·u_{t−1} (about a 27 ms lag). That predicts a peak near 0.81–0.83, a
  small negative-power time fraction, speed-invariant offline peaks of about 12 Nm at the 15 Nm scale, and a lag
  behind the biological hip moment. The Stage-3 reward is maximised by bang-bang u = sign(ω), which is exactly the
  published "Stage 3 only" behaviour. **Gates on these numbers test that the reconstruction is implemented
  faithfully; only the matched baselines and B0 test the SMAT mechanism.** The gate is built to say which is which.
- **The "no r_exo4" ablation also skipped Stage 3** (O Fig. 5 caption); only the "Stage 4 only" curve reports runs
  (mean of three); the main pipeline reports no seeds at all. The papers' explanation of the Stage-4-only collapse
  ("the second term rewards minimising torque") contradicts the reward's algebra (its gradient at u = 0 is 0.3·ŵ).
  The programme treats the collapse as an observation to reproduce, not as an explained mechanism.

### G.2 The ladder L0–L5 (every candidate and every claim has a level; the Watch panel shows it)

Each level lists its **gating criteria** (all must hold, decided by `check_gate.py`) and what it must **report**
(published beside it, never gating). "Independent seed" means a pipeline whose every stage used its own training
seed (Part C.3). "Per seed" means every seed must pass; "pooled" means the mean over seeds with its 95 % t-interval.

- **L0 Plumbing.** The four-stage trainer runs end to end on a tiny budget (the M1 integration test); actor freezing
  verified by identical weight hashes at the start and end of every frozen stage; the unit, sign and history tests
  of Part E.2 pass (the exo actor's 18 inputs, the stage torque scales, the reward terms on hand-computed states);
  the reference motion, the composed body model and the device model recorded by hash in the ledger.
- **L1 Human walking (Stage 1), on at least 3 independent seeds, per seed:**
  - the published criteria: **left–right Pearson r ≥ 0.92** for hip flexion, knee and ankle angles (gait-cycle-
    normalised mean curves, each limb normalised to its own cycle); **toe-off at 55–61 % of the gait cycle on both
    sides** with |right − left| ≤ 2 percentage points (published 57.8 ± 1.1 % right, 58.5 ± 0.9 % left; the ± are
    cycle-to-cycle spreads, so the band is wider than them to absorb the model and reference differences, and still
    rules out running, 35–40 %, and shuffling, above 64 %);
  - stable walking (ours, declared): mean forward speed 1.25 ± 0.10 m/s over the evaluation window; falls in at most
    10 % of evaluation episodes;
  - **reference plausibility (ours, labelled "ours" everywhere)**: hip and knee angle curves correlate with the
    reference motion at r ≥ 0.80, and hip and knee range of motion are within ±30 % of the reference's;
  - report: every joint's symmetry r and reference RMSE, the fall rate, the ROM ratios, the transitions used.
- **L2 Passive device (Stage 2), on the same seeds, per seed:**
  - **RMSE ≤ 3.6°** between the Stage-2 and Stage-1 gait-cycle mean curves of hip flexion, knee and ankle, both sides
    (the published bound, same comparator);
  - symmetry, speed and fall-rate criteria of L1 still hold;
  - the device's mass, inertia and attachment are recorded and compared with the paper's hardware (5.94 kg; the
    simulated mass is not reported in either paper) in the claim file; the mass used is a registered choice.
  - report: the per-joint RMSE, the activation change Stage 1 → Stage 2 (the papers report that simulated hip
    muscles were *less* active in Stage 2 while humans paid +13.1 %: this is a known model limitation to report,
    not a target).
- **L3 Reproduction (Stage 4 and ablations), on at least 3 independent full pipelines:**
  - **normalised peak torque 0.83 ± 0.08** per seed (the mean over evaluated cycles of each cycle's peak |u|, averaged
    over the two sides);
  - **negative-power time fraction ≤ 15 %** per seed (the fraction of evaluated control steps with τ·q̇_hip < 0,
    pooled over both sides; published 10 %, ablations 32 % and 40 %);
  - **four-group right-side activation reduction versus Stage 2**: every one of the four groups (rectus femoris,
    iliopsoas, hamstrings, gluteus maximus; mapped to `rectfem_r`, `iliopsoas_r`, `hamstrings_r`, `glutmax_r` of
    `myolegs26`) is reduced on every seed; the pooled mean relative reduction is within **10.1 ± 5 percentage
    points** (5.1–15.1 %) and its 95 % t-interval excludes zero;
  - gait preserved in Stage 4: symmetry r ≥ 0.92, speed and fall-rate criteria of L1; knee and ankle RMSE versus the
    same seed's Stage 2 ≤ 5° (ours; hip is expected to change because hip imitation is released);
  - **the published ablation directions**, each on at least 3 seeds branching from the same S2 checkpoints as the
    full pipeline: *Stage 4 only* (from S2, exo actor random): peak ≤ 0.30 and opposing-power time ≥ 20 %;
    *Stage 4 only without r_exo4* (from S2, as published): mean swing-phase torque in extension and negative-power
    time ≥ 25 %; *Stage 3 only*: |u| ≥ 0.95 for at least 50 % of the gait cycle;
  - report beside every L3 number: the six-group bilateral reduction against its band (**6.1 ± 4 percentage points**,
    averaged per group over both legs, then over the six groups: gluteus maximus, hamstrings, iliopsoas, rectus
    femoris, gastrocnemius, soleus); **B0** (reward-matched zero torque) and **B1–B4** (the matched velocity and phase
    controllers) on the same seeds; the offline-replay numbers (Part B.6); the fraction of SMAT's command variance
    explained by the filtered velocity law.
  - Before the full pipelines exist, a candidate whose Stages 3–4 branch from a shared S2 checkpoint may show
    **"L3-provisional (shared trunk)"**; it never counts as L3.
- **L4 Better** (a method claim), on at least 5 independent seeds, at least one of:
  - (a) a four-group reduction at least **2 percentage points larger** than the programme's own reproduced SMAT, with
    the 95 % interval of the paired difference above zero, at equal or lower torque (peak command limit equal; RMS
    torque and positive work no more than 5 % higher) and equal or lower total transitions, with gait preserved;
  - (b) the same reduction as the reproduced SMAT (two one-sided tests at ±2 percentage points, 90 % interval inside
    the margin) using **at most half** of SMAT's total transitions including human pretraining, with gait preserved;
  - (c) **partner transfer**: in the cross-play matrix (every device actor evaluated with every held-out human policy
    from other independent pipelines, no adaptation allowed), the method keeps at least 70 % of its self-play
    reduction with an interval above zero, and its retention exceeds the reproduced SMAT's by at least 0.10;
  - and in every case the learned controller **beats B2 (the matched rate-limited velocity controller) and B4 (the
    matched phase profile)**, each with the human co-adapted at the same budget and the same torque limit, and beats
    the B0-adjusted effect, each by at least 2 percentage points with the 95 % interval of the paired difference above
    zero. If it does not, the result goes to the mechanism path (G.7).
- **L5 Sprint** (Phase 2), on at least 5 independent seeds, complete 200 m episodes only, all failures reported, the
  realistic actuator model applied (Part B.8):
  - **replication gate**: the unassisted sprinting human reaches a median maximum speed of at least **4.0 m/s**
    across 5 seeds, without changing the published reward of the human model it reconstructs and without any
    increase in muscle strength or shortening velocity; its 200 m completion rate and fall rate are reported;
  - **assistance gate**: median 200 m time improves by at least **0.5 s or 2 %** (whichever is smaller) versus the
    same human wearing the passive device, with a bootstrap 95 % interval (over seeds and paired starts) excluding
    zero; incomplete episodes count as failures with no time and are never dropped;
  - **architecture gate**: staged co-adaptation beats, or explains the failure of, the fixed-profile and unstaged
    conditions at matched budgets (Part B.8 conditions C3, C5, C6);
  - the gain survives the realistic cable actuator (tension only, attachment-dependent moment arm, delay,
    torque-speed-power limits, device mass); a gain that exists only with the ideal actuator is reported as an
    ideal-actuator result, not L5;
  - **transfer gate**: bench and human work are the lab's, separate, never automated; L5 claims simulation only.

**Ladder words** (the card validator of Part C.12 enforces them): below L1 every number is "screening"; L1–L2 numbers
are "findings"; a number is a "result" only from L3; "reproduced" appears only with L3; "better" only with L4; "sprint
gain" only with L5. The Watch panel's "How sure we are" wording comes from this table:

| Evidence | What happened | How sure we are |
|---|---|---|
| fewer than 3 independent seeds, or a sweep member not yet re-run on fresh seeds | "screening: too early to say" | low |
| a level's criteria met on its seeds | "(the level's word): met", with the numbers | medium at L1–L2; high from L3 |
| criteria failed on registered seeds | "not reproduced" / "not better", with the numbers and the band | high that it is not enough |
| a comparison not matched in budget, backend or hardware class | "not comparable" | none |
| a row flagged `suspect` (Part C.10) | "looks too good; being re-checked" | low until a fresh seed reproduces it |

### G.3 Metric definitions (implemented once, in `eval/core`, frozen with `EVAL_HASH`)

All metrics are computed from saved evaluation rollouts on the reference physics (native MuJoCo, float64; Part C.9),
with deterministic actions, `E` episodes (default 20) of 12 s at 1.25 m/s, the first 2 s discarded, evaluation seeds
from the evaluation pool.

- **Gait events.** Heel strike: the vertical ground-reaction force of a foot (sum over its heel and toe geoms) rises
  through 5 % of body weight after at least 100 ms below it; toe-off: it falls through 5 % of body weight. A cycle runs
  from one heel strike to the next of the same foot and is resampled to 101 points. Cycles shorter than 0.6 s or
  longer than 2.0 s are rejected and counted.
- **Symmetry r** (per joint): Pearson r between the right and left mean curves (each over its own cycles).
- **Toe-off %**: the mean over cycles of 100 × (toe-off time − heel strike) / cycle duration, per side.
- **Stage-2 RMSE** (per joint, per side): RMS difference between the Stage-2 and Stage-1 mean curves, in degrees.
- **Reference plausibility**: Pearson r and RMSE between the mean curve and the reference motion's cycle-normalised
  curve (the reference's own gait events); ROM = max − min of the mean curve.
- **Normalised peak torque**: per cycle and side, max |u| over the cycle; averaged over cycles, then over sides.
- **Negative-power time fraction**: over all evaluated control steps and both sides, the fraction with
  τ_applied · q̇_hip_flexion < 0, where τ_applied is the actuator force the simulator applied.
- **Activation reductions**: for each muscle group g and side, ā_g = the mean over evaluated cycles of the
  time-averaged activation (`data.act`, never the excitation) of g's actuators; the reduction of condition X versus
  Stage 2 is 100 × (ā_g,S2 − ā_g,X) / ā_g,S2 on the same seed and evaluation seeds. Four-group = the simple mean of
  the four right-side group reductions. Six-group = per group, the mean of the left and right reductions, then the
  simple mean over six groups. Group membership: `rectfem`, `iliopsoas`, `hamstrings`, `glutmax`, `gastroc`,
  `soleus` (`bifemsh` is not in "hamstrings": it does not cross the hip; a sensitivity analysis including it is
  reported).
- **Offline replay**: the device actor run open-loop on recorded no-exoskeleton walking (Part B.6) at the 15 Nm
  scale: peak torque per speed and the lag of the torque curve behind the biological hip moment by
  cross-correlation of gait-cycle-normalised group means.
- **Sprint metrics** (Phase 2): 200 m time from the common standing start with the finish interpolated between
  control steps; 100 m split; maximum speed (the maximum over the run of the 0.5 s moving average of pelvis forward
  speed); completion and fall rates; delivered torque, positive and negative device work, saturation time.

### G.4 How the bands were fixed, and the precision rule

The papers report no seed-level uncertainty for any simulated number; the only ± values are cycle-to-cycle spreads.
So each band above is the published value, widened to cover the definitional ambiguity the extraction found and
narrowed to stay well inside the distance between SMAT and its nearest ablation (peak 0.83 versus 0.14; negative-power
time 10 % versus 32–40 %; four-group reduction 10.1 % versus 0 for no assistance), so that a reconstruction behaving
like an ablation can never fall inside the SMAT band. The bands are written into `gate/criteria.yaml` in M1 exactly as
above.

**Precision rule.** Before any Stage-4 result exists, the runner measures each gated metric's evaluation noise (the
same checkpoint evaluated on five disjoint evaluation-seed sets). If that noise's standard deviation exceeds a quarter
of the band's half-width, the evaluation episode count `E` is raised until it does not. **The band is never widened**;
measurement is made precise enough for the band.

**Statistics.** Per-seed criteria must hold on every registered seed; failed or fallen seeds stay in (a seed that
cannot walk fails L1, it is not dropped). Pooled criteria use the 95 % t-interval over independent seeds; a
stratified bootstrap is reported and never gates. Equivalence claims use two one-sided tests at the stated margin.
Superiority claims use the one-sided 95 % bound of the paired difference. Claims are judged on the seeds registered
with the claim; seeds added later by steering are reported beside them (Part H.5).

### G.5 Claims, seeds and held-out assets

- A **claim** (`ledger/claims/<claim_id>.yaml`) is created when a candidate first meets L1 or when the user registers
  a comparison (a paired block of Part C.6). It records: `claim_type` (reproduction, better, mechanism, sprint,
  benchmark), the statement, the level targeted, the arms (candidate versions), the registered seeds (3 or 5 plus 5
  reserved top-up seeds drawn by `sha256(claim_id)`), the metrics and bands it is judged on, the gate epoch, and its
  steering and Promote provenance. Statement, arms, metrics and seeds freeze at creation; a changed statement is a new
  claim, and the old one keeps its evidence and verdict.
- **Held-out assets, reserved in M1 and listed in `gate/criteria.yaml`:** the evaluation seed pool; the human-partner
  seeds (900–949) whose Stage-2 and Stage-4 human policies serve only as held-out partners in cross-play; the recorded
  walking data used for offline replay; for Phase 2, a held-out set of start states. No search, sweep, sandbox run or
  tuning job may touch them (the job schema rejects it, and the sandbox cannot copy them, Part H.7).

### G.6 The paper gate (five gates, adapted to this domain)

- **G1 Effect at matched budget.** The claim's primary contrast holds on its registered seeds at matched transitions,
  torque budget, code identity, backend class and hardware class (Part C.10), with the statistics of G.4.
- **G2 Mechanism isolated.** The actor-update schedule is separated from the reward and torque curricula (the
  contrasts of Part B.6: frozen-then-joint versus joint-throughout with the same reward and torque schedules; progressive
  versus final reward; progressive versus final torque), B0 separates the reward change from the torque, and B1–B4
  separate learned timing from reward-shaped velocity feedback. Each named rival has its control, and the control does
  not explain the effect (a control reaching at least half the effect *is* the explanation and moves the claim to the
  mechanism path).
- **G3 Novelty.** A prior-art memo naming the five nearest works, UniExo (arXiv 2609.19690) and its successors
  included, each opened and quoted in a line, with the one-sentence falsifiable difference; the arXiv query is re-run
  monthly by the runner (Part E.4 M7) and the memo updated. Occupied territory is a comparator, not a kill.
- **G4 Transfer.** The effect survives the realistic actuator model (delay, rate and torque-speed limits; for Phase 2
  the cable model) and held-out partners (the cross-play matrix), each at least 50 % of the original effect with an
  interval above zero.
- **G5 Reproducibility.** A fresh clone reproduces every headline number within its interval, and a second machine
  (the Vast worker through `run_replication`, Part D.2) reproduces the central cell on 3 seeds within the claim's band.

### G.7 Three paths to a paper (so there is more than one way to converge)

- **Method path**: an L4 claim (walking) or an L5 claim (sprint) passing G1–G5.
- **Reproduction, negative or mechanism path**: a rigorous reproduction with an open implementation. It passes when:
  L3 is reached **or** decisively not reached (the registered seeds' intervals exclude the band, with the fidelity
  checks of L0–L2 passed, so the failure is not a broken implementation); B0 and B1–B4 are run on the same seeds; and
  the attribution is stated with evidence, for example "**SMAT's simulated gain is largely reward-shaped velocity
  control**" (the best matched velocity controller reaches SMAT's reduction within ±2 percentage points by two
  one-sided tests on 5 seeds) or "**the reward change alone accounts for most of it**" (B0 reaches at least half of
  it). G2, G3 and G5 apply as written; G1 is the equivalence or non-inferiority test at the stated margin.
- **Benchmark and tooling path**: an open, GPU-batched staged human-device co-adaptation benchmark with the matched
  baselines of Part B.6, certified physics parity against native MuJoCo (Part B.5), and the measured throughput, used
  to produce the reproduction numbers above. G1 becomes: the benchmark's rankings of the baselines and SMAT are stable
  across seeds and across the CPU and GPU backends.

A pass on any path drafts that package and raises `paper_gate_decision`. **After the gate:** park the GPU and alert the
user (`<<AFTER-GATE: park the GPU and alert me>>`, the user's choice); `after_gate: continue` is a setting.

### G.8 The gate is frozen against everyone

- `gate/criteria.yaml` (every band and threshold of G.2–G.7, the held-out assets of G.5, the metric names, which may
  only be quantities `eval/core` produces), `gate/check_gate.py` (a pure function from the ledger to
  `ledger/ladder.json` and `ledger/paper_gate.json`) and `gate/GATE_HASH`. The runner verifies `GATE_HASH` at start and
  before every harvest; `check_gate.py` refuses to run on a mismatch; the daily doctor checks it; each epoch's hash is
  in `ledger/epochs.jsonl`.
- **No steering action, sweep, Promote, dashboard control or Telegram command can change it** (the command schema has
  no such command; Part H.5). The only change path is `sprintctl gate-change <key> <value> --reason "…"` over SSH,
  which opens a visible gate epoch (alerted, shown permanently), and which **refuses any change to a band or threshold
  that a claim with an existing result is judged on**: a band can be corrected for claims not yet evaluated, never
  relaxed for one that has seen its numbers. A claim is always judged under the epoch in force when it was created.
- `check_gate.py` has its own synthetic-ledger tests (Part E.2 Gate group): every clean level and path passes, and every
  single violation fails alone.

### G.9 Deadlines and venue

Verify on the official sites in Phase 0 and keep `docs/calendar.md` current. Checked 2026-09-23: the internal
manuscript target is **2026-12-07**; **IROS 2027** is confirmed on its official site (2027.ieee-iros.org) for
Florence, 26 September–1 October 2027; its paper deadline, 2027-03-01, appears so far only on the IEEE RAS calendar,
without a time zone (re-check the call when it opens); IROS 2026 used 8 pages including references with no paid extra
pages and the `ieeeconf.cls` class. There is **no RA-L-with-IROS-option track any more**: RA-L papers accepted in the
transfer window 2026-08-01 to 2027-04-30 can be presented at IROS 2027 (re-check the window). RA-L is 6 pages plus up
to 2 paid pages; IEEE T-RO allows 20 pages (charges beyond 12); IEEE T-MRB allows 12 pages; Science Robotics research
articles run to about 8,000 words. The dashboard shows days to each date. Eight weeks before a deadline, if no claim
has passed the gate, the runner drafts a package from the best claim at its current level, labelled with its level,
while the queue continues. The gate is never lowered to meet a date.

Default venue (`<<VENUE>>` in the request; README): **IEEE RA-L, transferred to IROS 2027** for a reproduction,
mechanism or benchmark paper (a short, rigorous paper with open code fits RA-L, and the transfer gives the conference
presentation), or a **direct IROS 2027 submission** if the RA-L review would not finish inside the transfer window;
**IEEE T-MRB** for a longer journal version; Science Robotics only if an L5 sprint claim passes with the realistic
actuator. The template is the venue's official IEEE class, fetched when the package is drafted.
