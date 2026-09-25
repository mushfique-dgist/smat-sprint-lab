# 01_PAPERS — verified reading list for the SMAT reproduction and sprint programme (2026-09-23)

**How to use it.** *Must-read*: read the work in full before building or claiming anything in its area.
*Should-read*: its method or protocol matters; it is a comparator, a baseline or a design source. *Reference*: know it,
cite it. 🆕 marks work that appeared after April 2026. 📚 marks work already digested in the user's knowledge base
(`sail-lab-application-kb/…`, path given): read that note first. Each entry says what to take from the work, what it
left untested **for this programme**, what it takes to run on our server (one RTX 5090, 64 CPU cores, 30 GB RAM), and
the status of its code and assets on the date it was checked. Implementation-grade notes on the cornerstone papers and
on MyoAssist's code are in `03_PAPER_DIGESTS.md`; the reasoning that ties them together is in
`02_RESEARCH_DIRECTIONS.md`; Part B of the master prompt turns it into the campaign.

**How it was verified.** Each of the twelve clusters was researched by an agent that confirmed every entry against
the arXiv record, Crossref, the publisher or the repository page and recorded the title it saw; items it could not
confirm are listed in the appendix and never in the list. Afterwards `tools/verify_arxiv_ids.py` re-checked every arXiv
id against arXiv and every DOI of an entry without an arXiv id against Crossref (or the doi.org landing page); the
result is in `research-data/verification.json`. Code and asset status is a snapshot of the check date; re-check before
relying on it. bioRxiv DOIs from 2026 use the new prefix `10.64898`.

**Counts.** 152 distinct verified works: 54 must-read, 61 should-read, 27 reference. 40 appeared after April 2026 (🆕). 18 are already digested in the user's knowledge base (📚, path given).


---

## 1. SMAT, UniExo and the learning-in-simulation dispute

**What this literature tells the programme**

- SMAT's Stage-4 exo reward Δt·Σ(0.3·û·ω̂ − 0.15·û² − 2·max(0,|û|−0.8)²) with ω̂ = clip(ω/2 rad/s, ±1) is maximised pointwise by û ≈ clip(ω̂, ±0.81): a saturating velocity-proportional (negative-damping) law. The Stage-3 reward 0.5·û²·sign(û·ω) is maximised by bang-bang û = sign(ω), which explains the saturated 'Stage 3 only' ablation. UniExo keeps the same 0.3/0.15 power term (2608.00715 Eqs. 5-6; 2609.19690 Eq. 9). The learned policy has to beat this closed form before 'co-adaptation learns timing' can be claimed.
- The headline simulated number (10.1% hip-activation drop, 2603.07618) compares the Stage-2 human with the Stage-4 human, but Table S2 of 2608.00715 changes the human reward between them (muscle-effort weight 0.01→0.15, activation-rate 0.005→0.05, hip-activation 0→5.0, hip imitation weights→0). Reproduce it as published, then add a same-policy exo-OFF evaluation and a τ_max=0 Stage-4 control; otherwise part of the 'assistance' effect is a reward change.
- The shared-critic two-actor structure is stock MyoAssist (Yuan et al. BioRob 2026 'adapted from' MyoAssist; network_index_handler in neumovelab/myoassist). SMAT's contribution is the stage schedule and exo rewards, specified in 2608.00715 Algorithm S1 and Tables S2-S4 (PPO lr 5e-5/3e-5, clip 0.15, 2048 steps/env, 32 envs, minibatch 16384, 20 epochs, entropy 0.001/0.003; ~320M/160M/1.1M/66M steps per stage). Still missing: exo MJCF (5.94 kg device), reference motion file, full human observation spec, code, checkpoints.
- Compute: the authors report ~28 h per 100M steps on an 8-core Xeon (about 150 h for the whole curriculum). Their own follow-up (UniExo) already runs MuJoCo Warp + mjlab + rsl_rl at 3.7e4 steps/s with 2048-8192 envs on one Blackwell GPU, so 'SMAT on GPU' is infrastructure, not a publishable claim. Fitz-Yuan/mjlab_myosuite is an unmodified fork of MyoHub's early-prototype bridge (last upstream push 2026-03-06); MyoAssist 1.0 itself is CPU MuJoCo 3.4 + Stable-Baselines3.
- Disclosure bar after the Luo dispute: Nature added an Editor's Note on data/code availability (27 Jul 2026); the Nature code link is still non-runnable pseudocode; the Luo reply says code was released but gives no location; a Collins co-author (Slade) asked for code in Sept 2024 (issue #5, unanswered). SMAT shares its senior author (X. Zhou) with Luo 2024 and the reply, promised code 'upon acceptance', and SMAT-Exo is still a placeholder. Publish code, configs, seeds, learning curves and checkpoints from day one.
- Plausibility check to run in simulation: Collins et al. bound metabolic saving per unit exo positive work at about 4 (prior devices ≤2.3; Luo 2024 walking implies 5.5); SMAT-ext reports about 1.3 (47.9 W saving vs 36.1 W positive power). Report simulated muscle-metabolic saving per joule of exo positive work for every controller arm, and fix the gait-event convention first (the two dispute papers disagree mainly on timing).
- Kinematic side effects: on hardware SMAT raised hip ROM from 44° to 62° (+41%) and peak flexion velocity to about 251°/s without changing cadence or stride length, which is what a negative-damping velocity law would do. A reconstruction should check whether the simulated human shows the same amplification; SMAT zeroes hip imitation in Stages 3-4, which permits it.
- Public comparator code exists: Exo-Plore (DaebangStn/exo-plore; delayed-output-feedback τ=κ·u(t−Δt), CC BY-NC-SA, CPU Ray/DART) and a third-party MJX/MuscleMimic dual-PPO overlay with separate critics and matched-initial-state exo ON/OFF evaluation (Luk7-sb/myoassist-dual-ppo-control; one snapshot commit 2026-08-26, no data or checkpoints, simulation-only ±10 Nm). MyoAssist's ctrl_optim spline controllers are stance-phase (vGRF state machine, ankle-oriented), so a full-cycle bidirectional hip phase profile must be written.

### Must-read

- **End-to-End Policy Learning for Hip Exoskeleton via Reinforcement Learning and Reflex-Based Musculoskeletal Simulation** 🆕 — Barati, Kim, Nguyen, Lee, Park. IEEE Robotics and Automation Letters 11(7):8672–8679, 2026. doi:10.1109/LRA.2026.3699246 · [link](https://doi.org/10.1109/LRA.2026.3699246)
  - *Idea.* Exo-only RL: a hip-torque policy (LSTM-PPO vs MLP-PPO) learns against a reflex-driven planar musculoskeletal walker with domain randomisation and sensor noise, then transfers directly; net metabolic cost −15.2% (LSTM) and −11.0% (MLP) vs unassisted, n=8.
  - *Take from it.* Independent evidence that an exo-only policy against a non-learning reflex human yields metabolic savings; SMAT's only no-co-adaptation ablation (Stage 3 only) used a different, saturating reward.
  - *Left untested for this programme.* Full text not read (paywalled); abstract shows no co-adapting human and no velocity- or phase-law baseline; planar reflex model; '22.5% maximum' cited by Luo et al. unconfirmed.
  - *On our server.* Reflex controllers exist in MyoAssist ctrl_optim, so a reflex-human exo-only arm is buildable without new human training.
  - *Code and assets.* no code link in abstract; none found by GitHub search (checked 2026-09-23)
  - *Also relevant to:* musculoskeletal_sims_rl, sim_to_real_exo_control
- **Exo-Plore: Exploring Exoskeleton Control Space through Human-aligned Simulation** — Leem, Lee, Lee, Song, Won. ICLR 2026. arXiv:2601.22550 · doi:10.48550/arXiv.2601.22550 · [link](https://arxiv.org/abs/2601.22550) · [code](https://github.com/DaebangStn/exo-plore)
  - *Idea.* Trains a musculoskeletal gait generator conditioned on hip-exo parameters with a human–exo interaction reward (metabolic plus resistance-minimisation), rolls out a delayed-output-feedback controller τ=κ·[sin q_r − sin q_l](t−Δt) over sampled (κ, Δt), fits a surrogate, and optimises per speed.
  - *Take from it.* A ready, coded simple-controller family (κ, Δt delayed output feedback) plus a human-adaptation reward (energy + interaction/resistance term) to build the programme's matched non-learned comparator arm in simulation.
  - *Left untested for this programme.* No learned exo policy or co-adaptive (two-agent) comparison; no new hardware test of optimised parameters; DART human, not MyoAssist, so transfer of the optimal (κ, Δt) to SMAT's model is unknown.
  - *On our server.* Ray/DART CPU training (10k–24k epochs; 'medium_pc' preset = 32 workers) fits the 64-core EPYC but watch 30 GB RAM; non-commercial licence.
  - *Code and assets.* full pipeline released: DART C++ sim, Ray RLlib PPO gait generator, parameter sampling, NN/GP surrogate, figure scripts; dataset via external SharePoint link, no checkpoints in repo; CC BY-NC-SA 4.0; last push 2026-08-04 (checked 2026-09-23)
  - *Also relevant to:* hilo_coadaptation_theory, sim_to_real_exo_control
- **Experiment-free learning of exoskeleton assistance is not an unsolved problem** 🆕 — Luo, Jiang, Zhang, Zhu, Yu, Dominguez Silva, B. Zhou, Yuk, X. Zhou, Su. bioRxiv (openRxiv) preprint, posted 2026-06-17. doi:10.64898/2026.06.16.731058 · [link](https://www.biorxiv.org/content/10.64898/2026.06.16.731058v1)
  - *Idea.* Rebuttal: the ratio 4 is an average muscle efficiency, not a ceiling; recomputes walking energy ratio as 2.4 (or 3.4 with 18% timing correction); says replication used a fixed averaged profile, heel-strike timing offsets up to 30%, and a 50% heavier device.
  - *Take from it.* Gait-event convention (heel strike vs torque-peak timing) changes estimated exo power and energy ratio (2.4–5.5 across the two papers); fix event definitions and power computation before comparing controllers.
  - *Left untested for this programme.* No new hardware replication with the learned network, no released code at a checkable location, no seed-level simulation results; independent-results argument cites Barati (single-agent) and Zhou (3 participants).
  - *On our server.* Reading only; note X. Zhou (SMAT senior author) co-signs this response, so SMAT is not independent of the dispute.
  - *Code and assets.* claims 'executable code, raw experimental data, and simulation files' were released but gives no URL; no new public repo found; Nature still links the pseudocode repo (checked 2026-09-23)
  - *Also relevant to:* reproducibility_methods, sim_to_real_exo_control
- **Experiment-free learning of exoskeleton assistance remains an unsolved problem** 🆕 — Collins, De Groote, Gregg, Huang, Lenzi, Sartori, Sawicki, Si, Slade, Young. bioRxiv (openRxiv) preprint, posted 2026-04-06. doi:10.64898/2026.04.01.715109 · [link](https://www.biorxiv.org/content/10.64898/2026.04.01.715109v1)
  - *Idea.* Energy-ratio plausibility check: metabolic saving per unit exo positive work should not exceed ~4 (prior devices ≤2.3); Luo et al. imply 5.5 (walking: 61.6 W / 11.2 W) and 6.6 (stairs). Fixed-profile replication (N=10, 4.8 kg, four timing shifts) found no significant reduction.
  - *Take from it.* Adopt its checklist as the programme's reporting bar: executable code, reward parameters, PPO hyperparameters, seeds, learning curves, run-to-run variability, model files; add an energy-ratio sanity check to every metabolic claim.
  - *Left untested for this programme.* Replicated the average torque profile, not the learned state-feedback network; no simulation replication of the learning pipeline, which is exactly what an open SMAT reconstruction could supply.
  - *On our server.* Reading only; energy-ratio check is computable from simulated exo power and a muscle metabolic model.
  - *Code and assets.* analysis code for Fig. 1 and supplement provided as Supplementary Data 1 of the preprint, not a repository (checked 2026-09-23)
  - *Also relevant to:* reproducibility_methods, sim_to_real_exo_control
- **MyoAssist 1.0: An Open-Source Framework for Neuromechanical Simulation of Physical Human-Device Interaction** 🆕 — Robbins, Son, Tan, Wang, van Kanten, Sartori, Durandau, Kumar, Caggiano, Song. bioRxiv (openRxiv) preprint, posted 2026-08-26. doi:10.64898/2026.08.25.746839 · [link](https://www.biorxiv.org/content/10.64898/2026.08.25.746839v1) · [code](https://github.com/neumovelab/myoassist)
  - *Idea.* Composable human–device–task environments in MyoSuite: 15 device models, lower-limb to 416-muscle models, terrain/velocity locomotion tasks, an RL framework (multi-actor human and device policies) and a controller-optimisation framework for structured reflex and spline controllers with standard evaluation.
  - *Take from it.* SMAT was built on MyoAssist; pin 1.0 (Aug 2026). Its multi-actor RL (network_index_handler) resembles SMAT's dual-actor setup; ctrl_optim's stance-phase spline + reflex CMA-ES code is a template, not a ready hip profile.
  - *Left untested for this programme.* Repo runs CPU MuJoCo 3.4 + Stable-Baselines3 (no MJX/Warp path); no SMAT-style staged co-adaptation pipeline found in the repo tree.
  - *On our server.* Pin myosuite 2.8.4 / mujoco 3.4 via uv; for GPU batching port the env to mjlab_myosuite or MJX; the 26-muscle human keeps per-env cost low.
  - *Code and assets.* active, Apache-2.0: rl_train (human and exo agents, network_index_handler multi-actor), ctrl_optim (reflex + 4-parameter/n-point spline exo controllers with pre-optimised results), 1.0.0 sibling pins; CPU MuJoCo 3.4 + Stable-Baselines3; last push 2026-08-31 (checked 2026-09-23)
  - *Also relevant to:* musculoskeletal_sims_rl
- **SMAT: Staged Multi-Agent Training for Co-Adaptive Exoskeleton Control** 📚 — Yuan, Androwis, Zhou. IEEE/RSJ IROS 2026 (to appear, per authors); arXiv preprint. arXiv:2603.07618 · doi:10.48550/arXiv.2603.07618 · [link](https://arxiv.org/abs/2603.07618) · [code](https://github.com/Fitz-Yuan/SMAT-Exo)
  - *Idea.* Two PPO actors (26-muscle MyoAssist human; bilateral hip exo, 18-D hip-kinematics+torque-history input) share one critic through four stages: human gait, added exo mass, exo-only with frozen human (6 Nm), co-adaptation (25 Nm). Reports 10.1% simulated hip-activation drop; 5-subject hardware positive power.
  - *Take from it.* The published simulated targets: 10.1% mean right-hip activation reduction (RF −13.5%, iliopsoas −10.5%, hamstrings −9.7%, GMax −6.6%), Stage 2 vs Stage 4 at 25 Nm; ablations (Stage-4-only → near-zero torque); offline GT-dataset check.
  - *Left untested for this programme.* No same-human exo-ON/OFF evaluation, no seeds or learning curves, no comparison with the closed-form maximiser of its own exo reward (û≈clip(ω/2 rad/s, ±0.8)), and the Stage 2→4 human reward change confounds the 10.1%.
  - *On our server.* Rebuildable from 2608.00715 supplement in MyoAssist; authors' CPU cost ~28 h/100M steps (~550M steps total), so GPU port is essential.
  - *Code and assets.* SMAT-Exo holds only a README ('Code coming soon'), 2 commits on 2026-07-15; Fitz-Yuan/SMAT is a project page (figures, PDF, videos), no code; paper promised code 'upon acceptance' (checked 2026-09-23)
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/research/smat-reproduction-methods-2026-09-13.md; sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/core-sprint-pdf-reading-01.md`
- **Staged Multi-Agent Training (SMAT) for Hip Exoskeletons: Metabolic and Biomechanical Validation of a Simulation-Trained Co-Adaptive Controller** 🆕 📚 — Yuan, Wolf, Androwis, Zhou. arXiv preprint (extended version of the IROS paper; IEEE journal under review, per authors), 2026. arXiv:2608.00715 · doi:10.48550/arXiv.2608.00715 · [link](https://arxiv.org/abs/2608.00715) · [code](https://github.com/Fitz-Yuan/SMAT-Exo)
  - *Idea.* Same SMAT policy (peak ~12 Nm, 50 Hz, IMU kinematics) tested on 8 adults with indirect calorimetry: net metabolic rate −19.7% vs passive device, −9.1% vs no-exo; passive 5.94 kg device costs +13.1%; positive-power ratio 0.98; speed and terrain generalisation.
  - *Take from it.* Supplement gives most training details: Algorithm S1, stage-wise reward weights (Table S2), per-joint imitation weights (S3), PPO hyperparameters (S4), Stage-4 reward α=0.3, β=0.15, λs=2, δ=0.8, ωs=2 rad/s.
  - *Left untested for this programme.* Hip ROM rose 44°→62° (+41%), consistent with negative-damping assistance, yet no velocity-law or phase-profile control arm; Ctrl-B results withheld; single speed metabolic test, n=8, no EMG.
  - *On our server.* Hardware results not reproducible here; take its simulation settings and the reported ~1.3 W metabolic saving per W exo positive power.
  - *Code and assets.* no code; SMAT-Exo placeholder README only (checked 2026-09-23)
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/research/smat-reproduction-methods-2026-09-13.md; sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/core-sprint-pdf-reading-01.md`
- **UniExo: Unified Multi-Skill Policies for Musculoskeletal Locomotion and Co-Adaptive Exoskeleton Control** 🆕 — Yuan, Wolf, Androwis, Zhou. arXiv preprint (submitted 2026-09-17). arXiv:2609.19690 · doi:10.48550/arXiv.2609.19690 · [link](https://arxiv.org/abs/2609.19690)
  - *Idea.* Distils four MyoLeg-80 imitation experts (walk, turn, run, backward) into one latent-conditioned policy, fine-tunes on stitched transitions, initialises a shared-weight per-leg exo network from a hip-moment predictor, then co-adapts both with PPO and a shared critic.
  - *Take from it.* The GPU recipe (MuJoCo Warp + mjlab + rsl_rl, 8192/2048 envs, 300/100 Hz, 3.7e4 steps/s on one Blackwell GPU) and exo reward: 3.0·net-moment offload + power term 0.3τ̄ω̄−0.15τ̄² + hip-activation + smoothness.
  - *Left untested for this programme.* No metabolic or EMG data, no seeds; its power term again peaks at τ̄=ω̄, yet no velocity-law baseline tests whether co-adaptation (flexion peak ~10% later, negative power −65–81%) beats it.
  - *On our server.* Experts took 22–37 h each on one RTX PRO 6000 Blackwell; a 32 GB 5090 likely needs fewer envs; single-skill walking suffices for Phase 1.
  - *Code and assets.* no repository; paper says code 'will be made publicly available'; Fitz-Yuan/mjlab_myosuite (created 2026-07-23) is an unmodified fork of MyoHub/mjlab_myosuite, 0 commits ahead (checked 2026-09-23)
  - *Also relevant to:* gpu_batched_physics, musculoskeletal_sims_rl
- **Experiment-free exoskeleton assistance via learning in simulation** 📚 — Luo, Jiang, Zhang, Zhu, Yu, Dominguez Silva, Wang, Rouse, B. Zhou, Yuk, X. Zhou, Su. Nature 630:353–359 (Editor's Note added 27 Jul 2026), 2024. doi:10.1038/s41586-024-07382-4 · [link](https://www.nature.com/articles/s41586-024-07382-4) · [code](https://github.com/IntelligentRobotLearning/pseudocode_learning_in_simulation)
  - *Idea.* Three networks trained simultaneously in simulation (motion imitation, muscle coordination, exo control) on a 50-DOF, 208-muscle model with domain randomisation; exo reward = reduced muscle activation; ~8 h on RTX 3090; reported −24.3/−13.1/−15.4% metabolic rate (walk/run/stairs).
  - *Take from it.* The architecture SMAT and UniExo descend from (X. Zhou co-authors all three) and the dispute's lesson: claims without runnable code, seeds and model files now draw an editorial note.
  - *Left untested for this programme.* Energy ratio (walking 5.5, stairs 6.6 J saved per J work per Collins) never reconciled with physiology in the paper; no independent replication with the learned network; no run-to-run variance.
  - *On our server.* Cannot be rebuilt from public materials; treat numbers as disputed, not as reproduction targets.
  - *Code and assets.* pseudocode only: 3 non-runnable .py stubs (undefined num_h1..., 'Network details elided'), last commit 2025-06-03; Learning_in_Simulation_sample_code is a byte-identical copy; code request issues open since 2024, authors cite IP process (2025-07-01) (checked 2026-09-23)
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/research/code-and-transfer-audit-2026-09-13.md`
  - *Also relevant to:* frontier_sweep_2026, sim_to_real_exo_control

### Should-read

- **Exoskeleton Control through Learning to Reduce Biological Joint Moments in Simulations** — You, Zhou. arXiv preprint, 2026. arXiv:2603.07629 · doi:10.48550/arXiv.2603.07629 · [link](https://arxiv.org/abs/2603.07629)
  - *Idea.* Same NJIT lab: RL human (304-muscle, GaitNet rewards) plus muscle-coordination network; a separate exo network (32-D hip/knee history + delay input) trained to reproduce biological joint moments, then checked offline against an open gait dataset (hip cross-correlation up to 0.98).
  - *Take from it.* The offline validation protocol also used by SMAT: feed recorded human kinematics to the trained exo network, compare torque timing and power with biological moments; explicit delay input shows timing shifts raise positive power.
  - *Left untested for this programme.* Reports torque/power agreement, not muscle or metabolic benefit; no hardware; idealised joint torques; no velocity- or phase-law comparison; agreement degrades at knee and high speed.
  - *On our server.* Protocol is cheap: needs only an open gait dataset with hip kinematics and inverse-dynamics moments plus the trained exo actor.
  - *Code and assets.* no code or data link in the paper (checked 2026-09-23)
- **Learning Hip Exoskeleton Control Policy via Predictive Neuromusculoskeletal Simulation** 📚 — Park, Song, Kang. arXiv preprint, 2026. arXiv:2603.04166 · doi:10.48550/arXiv.2603.04166 · [link](https://arxiv.org/abs/2603.04166) · [code](https://github.com/IlseungPark/Learning-Hip-Exo)
  - *Idea.* One privileged SAC teacher jointly outputs muscle-synergy excitations and raw hip-exo torques (low-pass filtered), trained over speeds 0.7–1.5 m/s and ±5° slopes in two stages (exo clamped to zero, then enabled), then distilled to a thigh-gyro TCN student.
  - *Take from it.* A single-agent alternative to SMAT's two actors with a matched no-exo comparison built in; modest simulated gains (≤3.4% activation, ≤7.0% positive joint power) calibrate expectations; learned flexion peak at 71% gait cycle.
  - *Left untested for this programme.* No metabolic hardware test; no two-agent or four-stage comparison; spline and delayed-moment profiles compared only on peak timing, not simulated benefit.
  - *On our server.* Stable-Baselines3 SAC, 30 envs, 1e8 steps: CPU-bound; no code, so reimplementation only.
  - *Code and assets.* project-page template only (index.html, static assets, uncustomised template README), no code (checked 2026-09-23)
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/research/code-and-transfer-audit-2026-09-13.md`
  - *Also relevant to:* sim_to_real_exo_control

### Reference

- **Gait Asymmetry from Unilateral Weakness and Improvement With Ankle Assistance: a Reinforcement Learning based Simulation Study** — Yuan, Androwis, Zhou. IEEE BioRob 2026, pp. 277–282. arXiv:2602.18862 · doi:10.1109/BioRob66782.2026.11681259 · [link](https://arxiv.org/abs/2602.18862)
  - *Idea.* Precursor of SMAT in MyoAssist: 26-muscle human and right-ankle exo actors with a shared centralised critic, both on the same imitation reward; strength scaled to 75/50/25% (ankle-ROM SI +6.4% → −47.1%); at 50%, co-trained assistance cut |SI| 25.8% → 18.5%.
  - *Take from it.* Confirms MyoAssist's framework provides the two-actor, shared-critic setup (here with a 65-D shared observation) and shows the authors' strength-scaling perturbation for robustness tests.
  - *Left untested for this programme.* Exo shares the human's imitation reward (no assistance objective of its own); simulation only; peak loading stayed biased toward the unimpaired limb.
  - *On our server.* Strength scaling = multiply each muscle's F_max by α; trivially reusable for SMAT robustness tests.
  - *Code and assets.* no code link in paper; no matching repo under Fitz-Yuan (checked 2026-09-23)
- **Reinforcement-Learning-Based Assistance Reduces Squat Effort with a Modular Hip–Knee Exoskeleton** — Ratnakumar, Tohfafarosh, Jauhri, Zhou. IEEE BioRob 2026, pp. 537–542. arXiv:2602.17794 · doi:10.1109/BioRob66782.2026.11681613 · [link](https://arxiv.org/abs/2602.17794)
  - *Idea.* NJIT RL-in-simulation controller mapping recent hip/knee angle and velocity histories to hip and knee torques, tested in 5 adults doing metronome squats: about 10% lower net metabolic rate vs zero-torque and no-exo, but reduced squat depth.
  - *Take from it.* Kinematic side effects accompany metabolic savings (smaller squat depth here, larger hip ROM in SMAT): report task kinematics beside every effort metric.
  - *Left untested for this programme.* Per abstract: baselines only zero-torque and no-exo (no simple-controller arm), no sim-predicted savings compared, n=5 preliminary.
  - *On our server.* Reading only; squat task is outside Phase 1 but its kinematic-side-effect lesson applies.
  - *Code and assets.* no code link in the arXiv record or abstract (checked 2026-09-23)
- **Simulation study of exoskeleton–musculoskeletal coupling for exoskeleton assistance via multi-agent reinforcement learning** 🆕 — Sun, Li, Deng, Wang. Medical & Biological Engineering & Computing (online ahead of print, 2026-07-22). doi:10.1007/s11517-026-03634-9 · [link](https://doi.org/10.1007/s11517-026-03634-9)
  - *Idea.* OpenSim 7-DOF bilateral lower-limb model and a hip exo as heterogeneous agents trained with MATD3 under centralised training/decentralised execution; reward mixes joint tracking, posture, core-muscle activation and exo action smoothness; simulated at 0.86, 1.2, 1.5 m/s.
  - *Take from it.* Independent confirmation that the two-agent, centralised-critic formulation is spreading beyond NJIT, with an off-policy MATD3 variant as an alternative to shared-critic PPO.
  - *Left untested for this programme.* Simulation only, no code found; an unassisted iliopsoas peak >3000 N (≈4× body weight for a 75 kg adult) warrants scrutiny; abstract reports no staging ablation or simple-controller baseline.
  - *On our server.* Reading only; paywalled; OpenSim-based, far slower than MuJoCo for RL.
  - *Code and assets.* no code link in abstract; none found by GitHub search (checked 2026-09-23)
  - *Also relevant to:* marl_shared_critic_partners
- **Comparison of Empirical and Reinforcement Learning (RL)-Based Control Based on Proximal Policy Optimization (PPO) for Walking Assistance: Does AI Always Win?** — Drewing, Ahmadi, Xiong, Sharbafi. Biomimetics 9(11):665, 2024. doi:10.3390/biomimetics9110665 · [link](https://doi.org/10.3390/biomimetics9110665)
  - *Idea.* Biarticular thigh exosuit (SEA-driven, mimicking hamstrings and rectus femoris): an empirical gait-knowledge controller versus a PPO controller optimised on a neuromuscular model; both cut hamstring activation and raised preferred speed, but the RL controller increased vastus and rectus femoris activity.
  - *Take from it.* Precedent for the programme's central control arm: a hand-designed controller matched against a simulation-trained RL controller on the same device, with muscle-level outcomes.
  - *Left untested for this programme.* Abstract shows no co-adapting learned human, outcomes limited to muscle activation and preferred speed (no metabolic cost), one exosuit.
  - *On our server.* Reading only; its exosuit (SEA, biarticular) context matters for Phase 2.
  - *Code and assets.* no code link in the Crossref record or abstract (checked 2026-09-23)
- **Robust walking control of a lower limb rehabilitation exoskeleton coupled with a musculoskeletal model via deep reinforcement learning** — Luo, Androwis, Adamovich, Nunez, Su, Zhou. Journal of NeuroEngineering and Rehabilitation 20:34, 2023. doi:10.1186/s12984-023-01147-2 · [link](https://doi.org/10.1186/s12984-023-01147-2)
  - *Idea.* Ancestor of the NJIT line: a rehabilitation-exoskeleton policy trained with DRL while coupled to a musculoskeletal human, using three independent networks (control, interaction-force prediction, muscle coordination) and domain randomisation of muscle strength; virtual tests only.
  - *Take from it.* Origin of the three-network decoupling reused in Luo 2024 and You & Zhou 2026; muscle-strength randomisation is a cheap robustness lever for the programme's human model.
  - *Left untested for this programme.* Position-target rehabilitation exoskeleton, not torque assistance for able-bodied walking; decoupled (not co-adaptive) training; virtual tests only, no hardware or metabolic outcome.
  - *On our server.* Reading only; no assets or code available.
  - *Code and assets.* no repository linked in abstract; see unverifiable note on IntelligentRobotLearning/Zero_shot_learning_for_human_robot_interaction (checked 2026-09-23)

### Already claimed by published work (cite it, compare against it, do not headline it)

- Four-stage human–exo curriculum with shared-critic PPO in MyoAssist yielding a positive-power hip policy that transfers without per-subject tuning — SMAT (Yuan, Androwis, Zhou; arXiv 2603.07618, IROS 2026).
- Metabolic validation of a simulation-trained co-adaptive hip controller: −19.7% vs passive device, −9.1% vs no-exo, n=8, plus speed/terrain generalisation — Yuan et al., arXiv 2608.00715.
- One co-adapted hip controller across walking, turning, running, backward walking and transitions, trained with MuJoCo Warp + mjlab and initialised from a hip-moment predictor — UniExo, arXiv 2609.19690.
- Experiment-free learning-in-simulation hip controller with reported −24.3/−13.1/−15.4% metabolic rate for walking/running/stairs — Luo et al., Nature 2024 (under Editor's Note since 27 Jul 2026).
- Energy-ratio implausibility of Luo et al. 2024 and a null fixed-profile hardware replication (N=10) — Collins et al., bioRxiv 10.64898/2026.04.01.715109.
- Single-agent exo RL against a reflex-based musculoskeletal walker transferring to hardware with −15.2% net metabolic cost (n=8) — Barati et al., RA-L 2026.
- Simulation-only optimisation of delayed-output-feedback hip gain and delay with a human-adaptation reward; optimal delay decreases with walking speed — Exo-Plore (Leem et al., ICLR 2026).
- Single joint policy (synergy prior) for muscles and hip-exo torque over speeds and slopes, distilled to an IMU student with preserved torque profiles (r=0.82) — Park, Song, Kang, arXiv 2603.04166.
- Heterogeneous MARL (MATD3, centralised training) for human–hip-exo coupling in OpenSim — Sun et al., MBEC 2026.
- Offline validation of simulation-trained exo networks against open-source biological moments, with delay tuning — You & Zhou, arXiv 2603.07629.

### Open questions this programme can attack

- Closed-form control arm: repeat SMAT's Stage-4 human training with the exo policy replaced by û = clip(ω/2 rad/s, ±0.8) plus the learned policy's measured slew-rate limit (and lagged variants), matched on RMS and peak torque; compare hip-activation change, positive-power fraction and hip ROM. Not run by SMAT, SMAT-ext or UniExo.
- Reward-confound control: evaluate the Stage-4 human with exo torque zeroed, and train a τ_max=0 sham Stage 3-4 with identical rewards, to separate assistance from the Stage 2→4 reward change behind the 10.1%. Absent from all SMAT papers.
- Full-cycle hip phase-profile arm: a bidirectional spline (flexion and extension peak times and magnitudes) or Exo-Plore's κ·u(t−Δt), optimised by CMA-ES inside the same MyoAssist human; no head-to-head with a co-adapted policy exists.
- Seed-level reproducibility: at least 5 seeds per stage with learning curves and pre-registered tolerances on the 10.1% mean and per-muscle −13.5/−10.5/−9.7/−6.6%, answering Collins et al.'s run-to-run variability demand; no SMAT or UniExo seed variance is reported.
- Is staging necessary? Compare the four-stage schedule with simultaneous training (as in Luo 2024) under an exo reward without the β·û² zero-torque attractor; SMAT's 'Stage 4 only' collapse (peak 0.14) conflates staging with that reward term.
- Model sensitivity: rerun SMAT on myolegs26 vs MyoLeg-80 (UniExo's model) and under 75/50% strength scaling (Yuan BioRob 2026 protocol); whether the simulated gain survives model changes is untested.
- Energy ratio in silico: simulated metabolic saving (muscle metabolics model) per joule of exo positive work for SMAT vs control arms, checked against Collins et al.'s bound of about 4; no SMAT-line paper reports it.
- Sprint regime with cable limits: staged co-adaptation for 200 m sprinting with a tension-only cable actuator model (force-rate, slack, bandwidth limits). SMAT trained at 1.25 m/s with ideal ±25 Nm torque; UniExo's run skill uses ideal ±15 Nm torque behind a 6 Hz low-pass filter.


---

## 2. The April–September 2026 frontier

**What this literature tells the programme**

- The April-September 2026 frontier moved on the human side, not the device side: two demonstration-free sprinting musculoskeletal controllers appeared (Bolt 2609.11083; lambda-hold 2608.17030), but neither includes a device, fatigue or a 200 m race.
- Engine and optimiser choices matter for sprint realism: Bolt's appendices report that MuJoCo constraint-solver joint limits destabilised sprint gaits and that PPO produced shorter-stride, less dynamic sprints than TD3/SAC at roughly three times the wall-clock. A MyoAssist + PPO Phase 2 inherits both risks until tested.
- Reproducibility pressure intensified: Nature added an Editor's Note (27 July 2026) to Luo et al. 2024 over data and code availability. Publisher metadata lists Xianlian Zhou, SMAT's last author, as a Luo 2024 co-author, which makes an open, independent SMAT reproduction more consequential.
- Simple hip controllers are published, strong and cheap to emulate: energy-gated positive-power assistance (PositiveAssist, walking to 3.5 m/s running) and optimized moment-to-torque maps (Powell 2026; Shepherd et al. roadmap). Learned co-adapted controllers should be compared against these, not only against zero torque.
- Effort-only outcomes mislead: inverse simulations overestimate optimal assistance because effort costs ignore the loss of joint stiffness (Luis 2026), and towed sprinting improved 30 m time ~3% with unchanged EMG (Skujyte 2026). Score sprint assistance by time and kinematics, with activation as secondary.
- Simulation validity can be tested by rank agreement: the replay-constrained prosthesis framework predicted which controllers performed best on hardware. Rank-order agreement with held-out data is a cheap validity metric for the programme.
- No paper in the window evaluated device controllers against held-out human policies. Zero-shot-coordination work supplies the protocol (inter-seed vs cross-implementation cross-play), and replaying recorded humans supplies a data-driven variant.
- Fatigue and energetics are missing from every sprint simulation found; open building blocks now exist (MetaboliSim's Mader model, AGPL; the 3CC model used by Tired Actor) but nobody has coupled them to a muscle-driven sprinter.

### Must-read

- **A Replay-Constrained Simulation Framework for Personalization of Powered Knee--Ankle Prosthesis Controllers** 🆕 — Le, Posh, Cheng, Ghaffari, Gregg. arXiv cs.RO, 2026-07-24. arXiv:2607.22858 · [link](https://arxiv.org/abs/2607.22858)
  - *Idea.* MuJoCo reproduces prosthetic knee-ankle dynamics while replaying each user's recorded hip kinematics and feedback-based ground reactions instead of modelling neuromuscular control; deep RL personalizes phase-dependent impedance, and simulation predicted hardware outcomes (r=0.96-0.997) in three transfemoral users.
  - *Take from it.* A validation template: report whether simulation rank-orders controllers as hardware (or held-out data) does. Replaying recorded human kinematics is a cheap held-out-partner test for co-adapted device policies.
  - *Left untested for this programme.* Human is replayed, not adaptive, so no co-adaptation; walking at 0.8 m/s only; prosthesis, not exoskeleton. Narrows O4's evaluation design (held-out recorded humans) without closing it; O1-O3 untouched.
  - *On our server.* CPU MuJoCo simulation of one prosthesis with replayed inputs, so cheap. Needs recorded gait data; no code release found.
  - *Code and assets.* none found in arXiv record or HTML
- **A roadmap for end-to-end task-agnostic exoskeleton control** 🆕 — Shepherd, Schonhaut, Scherpereel, Tourk, Young. Nature Machine Intelligence (Perspective), online 2026-08-24. doi:10.1038/s42256-026-01297-7 · [link](https://www.nature.com/articles/s42256-026-01297-7)
  - *Idea.* Perspective arguing exoskeleton control should move from task classification to end-to-end maps from real-time biological joint-moment estimates to torque; it reviews simulation-trained RL as an alternative limited by sim-to-real gaps and human adaptation that musculoskeletal simulations cannot yet capture.
  - *Take from it.* Use its scale-delay-filter (plus shaping) moment-to-torque map as a named simple baseline family beside velocity-proportional torque; its sim-to-real gap list is a ready threats-to-validity section.
  - *Left untested for this programme.* A Perspective, not an experiment. It flags human adaptation that simulations miss, which motivates O4 (cross-play against held-out human policies), but it closes none of O1-O4.
  - *On our server.* Paywalled Perspective; publisher page text was readable. No compute.
  - *Code and assets.* n/a (Perspective)
- **Lambda-Hold Control: Human-Like Movement Emerges from a Minimal Task Reward in Predictive Musculoskeletal Simulation** 🆕 📚 — Lee, Lee, Ahn. arXiv cs.RO, 2026-08-17. arXiv:2608.17030 · doi:10.48550/arXiv.2608.17030 · [link](https://arxiv.org/abs/2608.17030) · [code](https://lee-jun-hyuk-37.github.io/projects/lambda-hold/)
  - *Idea.* Policy sets per-muscle equilibrium-point thresholds (lambda), held over gait-phase intervals; a stretch-reflex law converts them to excitations. With a velocity-only reward, a 90-muscle SCONE/Hyfydy model learns human-like sprinting (~4 m/s) in about an hour.
  - *Take from it.* Candidate human-side action space for Phase 2: low query rate and reflex-grounded exploration make sprint learning cheap, leaving compute for the device agent. Its speed-only reward pairs naturally with a sprint-time objective.
  - *Left untested for this programme.* No device, cable actuator, co-adaptation or fatigue; peak speed (~4 m/s) is far below competitive sprinting. Narrows O3 (fast-learning sprinting human) but closes none of O1-O4; MuJoCo/MyoAssist portability untested.
  - *On our server.* About 1 h on an RTX 5070 plus 24-thread CPU. Runs on Hyfydy (separately licensed engine); code unreleased, so expect reimplementation.
  - *Code and assets.* Project page shows 'Code (TBA)'; not released as of 2026-09-23
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/research/06-lambda-hold-smat-sprint-architecture.md`
  - *Also relevant to:* physiology_grounded_control, sprint_biomech_exosuits
- **Learning Realistic Athletic Sprinting Without Demonstrations** 🆕 — Wang, Bianco, Tevet, Hicks, Liu, Delp, Fatahalian. SIGGRAPH Asia 2026 (per project page); arXiv cs.GR, 2026-09-10. arXiv:2609.11083 · doi:10.1145/3829340.3842159 · [link](https://arxiv.org/abs/2609.11083) · [code](https://github.com/willwng/bolt)
  - *Idea.* Bolt, a Warp GPU simulator reproducing OpenSim muscle-tendon dynamics (136 MTUs, elastic tendons), reaches ~1000x real time; FastTD3 trains excitation-space policies from termination rules plus a speed/joint-limit-force reward, yielding a ~10 s 100 m sprint matching sprinter data.
  - *Take from it.* Phase-2 human baseline and engine candidate. Appendices: PPO gave shorter-stride, less dynamic sprints (36-48 h vs ~12 h TD3/SAC); MuJoCo's constraint solver gave unstable gaits, both direct risks for a MyoAssist/PPO sprint build.
  - *Left untested for this programme.* No device, co-adaptation, 200 m, or fatigue (paper states fatigue is not modelled; maximal output held all race). Narrows O3 by supplying a validated sprinting human and GPU engine; does not close O3. O1, O2, O4 untouched.
  - *On our server.* Trained in under a day on an RTX 6000 PRO; FastTD3 keeps a 26.2M-sample replay buffer on-GPU; check it fits 32 GB. No license declared.
  - *Code and assets.* Public repos willwng/bolt (NVIDIA Warp simulator) and willwng/msk_envs (RL envs), last pushed Aug 2026; no license file declared (GitHub API, 2026-09-23)
  - *Also relevant to:* motion_imitation_rewards, physiology_grounded_control, sprint_biomech_exosuits
- **MetaboliSim: a Python implementation of the Mader model for dynamic and steady-state simulation of muscular energy metabolism** 🆕 — Dunst, Scharf, Hesse, Asteroth. arXiv q-bio.QM, 2026-06-06. arXiv:2606.08366 · doi:10.48550/arXiv.2606.08366 · [link](https://arxiv.org/abs/2606.08366) · [code](https://codeberg.org/3phos/metabolisim)
  - *Idea.* First open implementation of the full Mader model: a five-state ODE (phosphate potential, VO2, muscle and blood lactate, glycogen) plus steady-state MLSS equations, verified against published reference outputs and checked on constant-load, step, sprint and running protocols.
  - *Take from it.* A candidate energy/fatigue state for the 200 m task: coupling phosphate potential and lactate to muscle force capacity (our addition, untested) would let assistance matter late in the race, which Bolt ignores.
  - *Left untested for this programme.* Lumped whole-body energetics with no musculoskeletal or device coupling and no link from metabolic state to muscle force. Narrows O3's physiology gap only; O1, O2, O4 untouched.
  - *On our server.* Pure-Python ODE, negligible cost per step. AGPL-3.0: any distributed derivative must stay AGPL.
  - *Code and assets.* Open source, AGPL-3.0 (per abstract); repository not inspected
  - *Also relevant to:* sprint_biomech_exosuits
- **PositiveAssist: Energy-Gated Control for Positive Power Assistance of Exoskeleton in Walking, Running, and Stair Climbing** 🆕 — Zhou, Gao, Huang, Lin, Wu, Su. IEEE/ASME Transactions on Mechatronics (online 2026-06-12). doi:10.1109/TMECH.2026.3691108 · [link](https://doi.org/10.1109/TMECH.2026.3691108)
  - *Idea.* Two thigh IMUs estimate hip kinematics and predicted mechanical power; torque is gated to positive-work phases and extension assistance is synthesized from a delayed flexion profile. One fixed parameter set kept >97.8% (walking) and >94.8% (running) of delivered power positive across 0.75-3.5 m/s.
  - *Take from it.* A published, tuning-free power-gated hip controller spanning walking to running speeds: implement it as a second matched simple baseline beside velocity-proportional torque in both the SMAT reproduction and sprint phases.
  - *Left untested for this programme.* Abstract reports power positivity and transitions for six participants, no metabolic outcome, nothing above 3.5 m/s. Narrows O1's baseline set; closes none of O1-O4 (no simulation, co-adaptation or sprint).
  - *On our server.* Paywalled; abstract gives gating logic but not all constants. Cheap to emulate in simulation from hip velocity and estimated moment.
  - *Code and assets.* none found
  - *Also relevant to:* sprint_biomech_exosuits
- **Why inverse simulations overestimate optimal ankle exoskeleton assistance: the role of bi-articular coordination and joint stiffness** 🆕 — Luis, Gutierrez-Farewik, Afschrift. Journal of NeuroEngineering and Rehabilitation, 2026-07-21 (preprint Research Square 10.21203/rs.3.rs-9565943/v1). doi:10.1186/s12984-026-02106-3 · [link](https://doi.org/10.1186/s12984-026-02106-3) · [code](https://doi.org/10.6084/m9.figshare.c.8608543)
  - *Idea.* Inverse walking simulations across 0-100% of the biological plantarflexion moment show gastrocnemius bi-articularity caps metabolic savings, and rising assistance cuts ankle stiffness up to 55% via soleus de-recruitment, an impedance loss effort-based costs ignore, inflating simulated optimal assistance.
  - *Take from it.* Effort-only objectives (like activation-reduction rewards) can reward over-assistance. Report joint stiffness or impedance alongside activation when auditing SMAT and when scoring learned sprint assistance.
  - *Left untested for this programme.* Ankle, walking, inverse (not predictive or RL) simulation; no hip, running or co-adaptation. Adds a validity check for O1's activation metric but closes none of O1-O4.
  - *On our server.* Open access; inverse simulations are cheap and CPU-only. A stiffness metric is easy to add to MyoAssist logging.
  - *Code and assets.* Figshare collection linked to the article (contents not inspected)

### Should-read

- **Ensuring Interaction Safety in Multitask Exoskeleton Control: A Simulation-Trained Variable Impedance Framework** 🆕 — Ma, Li, Zhai, Han, Meng, Xia, Cheng. arXiv cs.RO, 2026-06-04. arXiv:2606.06370 · [link](https://arxiv.org/abs/2606.06370) · [code](https://anonymous.4open.science/r/human_exo_mocap_dataset-743B)
  - *Idea.* PPO synthesizes human muscle activations in simulation while the exoskeleton directly compensates biological joint torques; the data train an instruction-plus-proprioception policy predicting reference trajectories and variable impedance for nine tasks, with Lyapunov-bounded stiffness, cutting metabolic cost on hardware versus baselines.
  - *Take from it.* A non-co-adaptive alternative: generate assisted-human data with a fixed 'exo cancels biological torque' rule, then distil. A useful ablation arm against staged co-adaptation.
  - *Left untested for this programme.* Exo rule is fixed torque compensation, not co-adapted; abstract reports no sprint or partner-transfer test. Adds a comparison arm relevant to O2 but closes none of O1-O4.
  - *On our server.* PPO musculoskeletal data generation fits a one-GPU budget; the anonymous dataset link may expire.
  - *Code and assets.* Simulation dataset via anonymous link (per paper HTML); training code not found
- **Is Inter-Seed Cross-Play Enough? Evaluating the Robustness of Zero-Shot Coordination Algorithms to Implementation Details** 🆕 — Wolski, Hoernle, Forkel, Foerster. arXiv, 2026-08-04. arXiv:2608.03644 · [link](https://arxiv.org/abs/2608.03644)
  - *Idea.* Proposes cross-implementation cross-play, pairing agents from independently varied implementations rather than only different seeds, and applies it to Other-Play; for that algorithm, standard inter-seed cross-play proved a reasonable proxy for the stricter test.
  - *Take from it.* For O4, build held-out human policies that differ in implementation details (reward weights, network, PPO settings), not only seed, and report both inter-seed and cross-implementation cross-play.
  - *Left untested for this programme.* Discrete coordination games only; no continuous control, humans or physical coupling. Supplies O4's evaluation protocol but does not close O4; O1-O3 untouched.
  - *On our server.* Evaluation design only; the cost is training several human-policy variants, which GPU batching makes affordable.
  - *Code and assets.* none found in arXiv record or HTML
  - *Also relevant to:* marl_shared_critic_partners
- **Lower limb muscle activity under full and partial towing assistance in sprint running** 🆕 — Skujyte, Kamandulis, Genitrini, Satkunskiene et al.. Sports Biomechanics (online 2026-07-02). doi:10.1080/14763141.2026.2693711 · [link](https://doi.org/10.1080/14763141.2026.2693711)
  - *Idea.* Thirteen athletes sprinted 30 m unassisted, partially and fully towed by a motorised device: times improved 3.4% and 2.8% through longer strides and flight time and shorter contacts, stride frequency unchanged, while surface EMG of five muscles did not differ.
  - *Take from it.* Real assisted sprinting improved time without reducing muscle activity: score Phase 2 on sprint time, not activation, and use ~3% over 30 m as a plausibility anchor for simulated gains.
  - *Left untested for this programme.* External towing, not a hip exosuit; 30 m, not 200 m; no simulation. Gives O3 an empirical anchor but does not close it; O1, O2, O4 untouched.
  - *On our server.* Empirical reference only; no compute.
  - *Code and assets.* n/a (experimental study)
- **Optimized Mappings From Biological Hip Moment Estimates to Exoskeleton Torque Can Personalize Assistance Across Users and Generalize Across Tasks** 🆕 — Powell, Schonhaut, Molinaro, Young. IEEE Transactions on Medical Robotics and Bionics (online 2026-07-13). doi:10.1109/TMRB.2026.3712823 · [link](https://doi.org/10.1109/TMRB.2026.3712823)
  - *Idea.* Parametrizes moment-based hip control with delay, scaling and shaping terms and tunes it by metabolic HILO in nine subjects across two walking speeds and an incline: personalized maps cut metabolic cost 18.3% versus no exoskeleton, task-agnostic generic maps 8.4%.
  - *Take from it.* Effect sizes for a simple moment-mapping baseline (8-18% metabolic) against which simulated co-adapted controllers should be judged, plus a parametrization easy to reproduce in MyoAssist.
  - *Left untested for this programme.* Walking only, hardware HILO, no simulation or running. Informs O1's baseline choice but closes none of O1-O4.
  - *On our server.* Needs a joint-moment estimate; in simulation the biological moment is directly available, so this baseline is cheap.
  - *Code and assets.* none found
  - *Also relevant to:* sim_to_real_exo_control
- **Reflex-Informed Neuromuscular Reinforcement Learning for Muscle-Driven Locomotion** 🆕 — Zhou, Zhang, Ma, Cao, Xie, Zhang. arXiv cs.RO, 2026-09-10. arXiv:2609.11733 · [link](https://arxiv.org/abs/2609.11733)
  - *Idea.* A fixed phase-dependent reflex controller drives the muscles while an RL policy outputs four residual parameters modulating hip-swing, knee-support and ankle-propulsion reflex gains and thresholds; gait is more accurate, symmetric and consistent, and stays robust to weakness and perturbations without retraining.
  - *Take from it.* A second low-dimensional, physiology-grounded human controller (4 actions) to compare with lambda-hold and with SMAT's full-excitation PPO human; a candidate held-out partner family for O4.
  - *Left untested for this programme.* Nominal walking only; no running, sprint, device or co-adaptation. Supplies candidate partner policies for O4 but closes none of O1-O4.
  - *On our server.* Four-dimensional residual action space trains cheaply; simulator and code availability not confirmed.
  - *Code and assets.* none found in arXiv record or HTML
  - *Also relevant to:* physiology_grounded_control
- **Simulation of Adaptive Running With Flexible Sports Prosthesis Using Reinforcement Learning of Hybrid-Link System** 🆕 — Shimane, Yamamoto. IEEE Robotics and Automation Letters (online 2026-05-15); arXiv 2026-04-10. arXiv:2604.08882 · doi:10.1109/LRA.2026.3693933 · [link](https://arxiv.org/abs/2604.08882)
  - *Idea.* Couples a whole-body transtibial-amputee model with a Piece-wise Constant Strain model of a leaf-spring running prosthesis; RL with motion-capture imitation generates running under several virtual prosthesis stiffnesses, and cost of transport agrees with prior reports.
  - *Take from it.* Shows RL running simulations can sweep a device parameter (stiffness) and report energetic trade-offs; a model for sweeping exosuit cable stiffness and slack in Phase 2.
  - *Left untested for this programme.* Imitation-anchored, so the human cannot re-coordinate freely; passive device; no sprint-time objective or co-adaptation. Narrows O3 methodologically without closing it; O1, O2, O4 untouched.
  - *On our server.* Soft-rigid hybrid dynamics are custom, not a MuJoCo drop-in. Concept transfers; code not found.
  - *Code and assets.* none found in arXiv record or HTML
- **Simultaneous Forward and Inverse Human-in-the-Loop Optimization** 🆕 — Park, Collins. CoRL 2026 (accepted, per arXiv comment); arXiv 2026-09-18. arXiv:2609.22630 · [link](https://arxiv.org/abs/2609.22630)
  - *Idea.* Learns a forward model from control policy to user outcomes and uses it for active preference queries that infer an individual reward, then optimizes the final policy without extra trials; in simulation it tolerated heterogeneity, noise and nonstationarity and beat mutual-information querying on sample efficiency.
  - *Take from it.* Its simulated-user protocol with explicit nonstationarity is a template for testing device learners against adapting humans, and it treats the reward itself as user-specific and unknown.
  - *Left untested for this programme.* Low-dimensional HILO with abstract simulated users, not musculoskeletal agents or RL policies; no running or sprint. Tangential to O4 (nonstationary partners); closes none of O1-O4.
  - *On our server.* Bayesian active-learning scale; CPU-trivial. No code link found.
  - *Code and assets.* none found in arXiv record or HTML
- **Tired Actor: Fatigue-Informed Character Control** 🆕 — Zhang, Liu, Niu, Chen, Ma, Gao, Lu, Li. arXiv cs.RO, 2026-08-04. arXiv:2608.03528 · [link](https://arxiv.org/abs/2608.03528)
  - *Idea.* Injects the Three-Compartment Controller (3CC) fatigue model into physics-based motion-imitation policies so characters have finite, depleting capacity, then analyses how fatigue changes the naturalness, scalability and robustness of learned control.
  - *Take from it.* A tested way to put a fatigue state inside an RL policy's dynamics and observations; 3CC is a lighter alternative to the Mader model for the 200 m human.
  - *Left untested for this programme.* General motion imitation, not sprint racing; no device or co-adaptation. Narrows O3's fatigue gap in method only; O1, O2, O4 untouched.
  - *On our server.* 3CC adds a few states per actuator, negligible cost. Code not yet released.
  - *Code and assets.* Abstract says code will be made public; no link found

### Reference

- **Beyond Heuristics: A Standardized Real2Sim Pipeline for Physical Human Robot Interaction in Human-in-the-Loop Simulation** 🆕 — Yang, Wang, Tan, Chan et al.. arXiv, 2026-07-03. arXiv:2607.03017 · [link](https://arxiv.org/abs/2607.03017) · [code](https://jacekcoder.github.io/Bioweb2026/)
  - *Idea.* Identifies a 6-DoF viscoelastic pelvis-strap interface (12 stiffness/damping parameters) per subject with CMA-ES at a 'safe and comfortable' operating point; shared priors calibrate a new subject by refining 5 parameters, and calibrated interfaces yield accurate gait adaptation in a human digital twin.
  - *Take from it.* Soft human-device interfaces should be identified, not guessed: model exosuit strap and cuff compliance explicitly when imposing realistic cable-actuator limits in Phase 2.
  - *Left untested for this programme.* Overground balance assistant, not an exosuit; no RL device policy, running or co-adaptation. Narrows O3's interface-realism component only; O1, O2, O4 untouched.
  - *On our server.* CMA-ES identification needs subject data; without it, use published parameter ranges as priors.
  - *Code and assets.* Project page linked in paper HTML; code not confirmed
- **MuJoCoUni:Persistent Batched Runtime Primitives for MuJoCo** 🆕 — Jia, Wu. arXiv technical report, 2026-05-24. arXiv:2605.24922 · [link](https://arxiv.org/abs/2605.24922) · [code](https://github.com/unilabsim/mujoco_uni)
  - *Idea.* A downstream MuJoCo distribution adding a C++ BatchEnvPool that owns per-environment models and per-thread data workers for stateful batched stepping, sparse resets, domain randomization and batched sensor queries, while leaving MuJoCo's solver, contact and integrator semantics unchanged.
  - *Take from it.* A CPU-side throughput lever for the 64-core EPYC that keeps exact upstream MuJoCo semantics, useful for the SMAT reproduction, where GPU-port numerical differences would confound comparison.
  - *Left untested for this programme.* No musculoskeletal benchmark in the abstract; speedups for MyoAssist-scale models unknown. Supports O1/O2 infrastructure; closes none of O1-O4.
  - *On our server.* pip install mujoco-uni; check compatibility with MyoAssist's pinned MuJoCo version first.
  - *Code and assets.* Open-source pip package mujoco-uni; benchmark repo unilabsim/mujoco_uni_bench (per paper)
- **The effects of muscle fibre type distribution on gait biomechanics: A predictive simulation study** 🆕 — Daehlin, Ross, De Groote, Wakeling. bioRxiv (Bioengineering), v1 2026-04-15, v2 2026-09-03. doi:10.64898/2026.04.13.718234 · [link](https://doi.org/10.64898/2026.04.13.718234)
  - *Idea.* A muscle model with separate slow- and fast-twitch fibres inside predictive simulation (1.0-4.5 m/s) shows more slow fibres lower cost of transport in walking, while in running the effect on cost and stride parameters reverses around a threshold speed.
  - *Take from it.* A sprinting human needs fast-fibre physiology; this gives a two-fibre muscle formulation to weigh before trusting single-fibre Hill models at sprint speeds.
  - *Left untested for this programme.* Tops out at 4.5 m/s; no sprint, device, RL or fatigue. Narrows O3's physiology question marginally; closes none of O1-O4.
  - *On our server.* Two-fibre muscles are not native to MuJoCo; porting needs custom actuator code. CC-BY preprint.
  - *Code and assets.* none found in bioRxiv record
- **Unified comparison of spinal locomotion control architectures in neuromechanical simulations** 🆕 — Ton, Song. bioRxiv (Physiology), 2026-06-12. doi:10.64898/2026.06.09.731213 · [link](https://doi.org/10.64898/2026.06.09.731213)
  - *Idea.* Implements reflex, CPG-reflex, synergy and CPG-reflex-synergy controllers in one neuromechanical framework with shared models and optimisation: reflex and CPG-reflex-synergy best match human gait, and CPG-reflex-synergy is most versatile across speeds and slopes.
  - *Take from it.* A model for O2's design (same body, optimiser and metrics across several controllers) and for its caveat that results compare implementations, not biological hypotheses.
  - *Left untested for this programme.* Walking controllers only; no devices, RL, running or co-adaptation. Methodological precedent for O2 but closes none of O1-O4.
  - *On our server.* Reflex/CPG optimisation is CPU-bound and suits the 64-core EPYC. CC-BY preprint, not peer reviewed.
  - *Code and assets.* Authors state the framework and controllers are publicly shared; URL not checked

### Already claimed by published work (cite it, compare against it, do not headline it)

- Demonstration-free, muscle-driven full 100 m sprint from an open GPU (Warp) simulator implementing OpenSim muscle dynamics at ~1000x real time, validated against sprinter data (Wang et al., 2609.11083, SIGGRAPH Asia 2026).
- Human-like sprinting from a minimal velocity reward in about an hour via equilibrium-point (lambda) actions and reflex recruitment (Lee, Lee, Ahn, 2608.17030).
- Off-policy RL (TD3/SAC) beats PPO for muscle-driven sprinting, and MuJoCo's constraint solver degrades sprint gait versus force-based joint limits (Bolt appendices, 2609.11083).
- Replay-constrained simulation (recorded human kinematics plus simulated device) ranks personalized prosthesis controllers consistently with hardware (Le et al., 2607.22858).
- Tuning-free, positive-power-gated hip assistance across walking and running speeds from two thigh IMUs (PositiveAssist, TMECH 2026).
- Delay-scale-shape moment-to-torque maps personalized by HILO, 18.3% vs 8.4% generic metabolic reduction (Powell et al., TMRB 2026).
- Inverse simulations overestimate optimal ankle assistance because effort costs ignore stiffness loss (Luis et al., JNER 2026).
- Towing assistance improves sprint time without lowering EMG (Skujyte et al., Sports Biomechanics 2026).
- First open, verified implementation of the full Mader energy model including sprint protocols (MetaboliSim, 2606.08366).
- Fatigue (3CC) integrated into physics-based character control (Tired Actor, 2608.03528).
- Cross-implementation cross-play as a stricter zero-shot-coordination test (Wolski et al., 2608.03644).
- Controlled comparison of reflex, CPG and synergy locomotion controllers in one neuromechanical framework (Ton and Song, bioRxiv 2026).

### Open questions this programme can attack

- O1 remains open: no independent reproduction of SMAT, SMAT-ext or UniExo was found through 2026-09-23, and no paper compares a co-adapted exo policy with velocity-proportional, power-gated (PositiveAssist-style) or moment-mapped baselines under a reward-matched zero-torque control.
- O2 remains open: no open, GPU-batched, staged human-device co-adaptation benchmark with matched baselines appeared. Bolt (GPU musculoskeletal, no device) and the known Assistax are the nearest pieces.
- O3 remains open and untouched by any window paper: no simulated hip-exosuit assistance of sprinting at all, let alone 200 m sprint time under cable-actuator limits. Sprint simulators omit fatigue (Bolt states this) and devices; the only 2026 empirical anchor found is towing (~3% over 30 m).
- O4 remains open: no cross-play or partner-transfer evaluation of co-adapted device controllers against held-out human policies. Protocols exist (inter-seed vs cross-implementation cross-play; replayed recorded humans) but were never applied to human-device co-adaptation.
- Prerequisite for O3 in MuJoCo: whether MyoAssist/MuJoCo can produce realistic sprints at all, given Bolt's report that MuJoCo constraint-solver joint limits destabilised sprint gaits; a short feasibility test should precede Phase 2.
- Untested whether staged co-adaptation stays stable with off-policy learners (TD3/SAC), which Bolt found superior for sprinting, versus SMAT's PPO.
- No musculoskeletal sprinter couples an energetics or fatigue state (Mader, 3CC) to muscle force capacity; without it a 200 m objective reduces to a 100 m-style maximal effort.


---

## 3. Musculoskeletal simulators and RL for muscle-driven locomotion

**What this literature tells the programme**

- Pin the body before comparing numbers: MyoAssist 1.0 (2026-08-19) stopped bundling XMLs and now composes myolegs26 from myo_sim at build time (MyoLeg26 is labelled beta; free-root 3D; knee flexion is negative). SMAT (March 2026) predates 1.0, so pin a pre-1.0 commit or prove segment, muscle and contact equivalence before any tolerance check.
- GPU is where the field went: SMAT reported ~28 h per 100M steps on 8 CPU cores (~1k steps/s, per KB digest); its authors' UniExo runs MuJoCo Warp + mjlab + rsl_rl at 3.7x10^4 steps/s (8192 envs, one RTX PRO 6000 Blackwell, 80-MTU MyoLeg); MuscleMimic reports 1.3x10^4 steps/s for 416 muscles on an H100. MyoAssist itself is CPU SB3; MyoHub/mjlab_myosuite (forked by SMAT's first author) and MyoSuite's mjx branch are the GPU on-ramps, and neither ships a hip-exo task.
- MuJoCo muscles are Hill-type FLV with OpenSim-identical activation dynamics (10/40 ms) but inelastic tendons, no pennation and sphere/cylinder-only wrapping (MuJoCo modeling docs). Beyond Kinematics finds MuJoCo imitation activations track EMG far worse than HyFyDy (r 0.11 vs 0.40) while kinematics match; MuscleMimic and UniExo report weak EMG agreement too. Treat SMAT-style simulated activation reductions as model outputs and add an EMG or Hyfydy cross-check before any mechanism claim.
- The human reward shapes the exo result: Schumacher et al. get mocap-free natural gait only with adaptive a^3 effort + excitation smoothness + active-muscle penalty (metabolic-energy and cost-of-transport rewards gave worse kinematics); UniExo's human uses imitation + balance + energy + root-velocity terms and its exo reward mixes power, moment offload, muscle saving and smoothness. Log every reward term per step so any exo benefit can be decomposed.
- Structured baselines already exist: MyoAssist ships Song-Geyer reflexes (51/63 parameters per leg, 13 muscle groups, runs on myolegs22/26/80) with 4-parameter and n-point stance-phase torque splines tuned by CMA-ES, but preoptimized sets are 2D only (0.75-2.0 m/s) and the spline interface targets ankle actuators, so a hip phase profile needs small code changes. Barati et al. (RA-L 2026) got 15.2% hardware metabolic reduction from a policy trained against a fixed reflex walker.
- Exploration options if PPO stalls on 26 or 80 muscles: DEP-RL (pip, pretrained MyoLeg/Hyfydy baselines), Lattice (latent correlated noise; used by KINESIS), synergy action spaces (Park et al. 2026; SAR, RSS 2023), residual RL on four reflex gains (Zhou et al., arXiv 2609.11733, 2D Hyfydy), and Qflex value-guided flow exploration (ICLR 2026, arXiv 2601.19707). None has been tested with a second, co-adapting device agent.
- Sprint realism gap: among verified papers the fastest muscle-driven RL gait is 5.2 m/s (22-muscle H1622 in Hyfydy, Schumacher et al.); MuscleMimic validates running only at 1.8 m/s, Choi et al. reach 2.2 m/s, UniExo's hardware jog is 2.25 m/s. No rigid-tendon MuJoCo body is shown sprinting, and tendon elasticity should matter most there (inference), so Phase-2 claims need a compliant-tendon check.
- Benchmarks drifted away from gait: MyoChallenge moved from chase-tag locomotion (2023) to prosthesis locomotion with myoOSL (2024) to soccer penalty kicks and table tennis (2025, arXiv 2605.15650); myosuite.org lists no 2026 edition (checked 2026-09-23). No challenge covers exoskeleton assistance or sprinting, so the programme must define its own tolerances and baselines.

### Must-read

- **Beyond Kinematics: Benchmarking Simulation Fidelity for Muscle-Driven Imitation Learning** 🆕 — Ahmad, Borden, Tucker. arXiv preprint, 2026-09-18 (submitted to ICRA 2027). arXiv:2609.21909 · [link](https://arxiv.org/abs/2609.21909)
  - *Idea.* Imitates one subject's walking (0.6-2.2 m/s) in SCONE/HyFyDy (H1090/H2190, elastic Millard tendons) and MuJoCo/MuscleMimic (240-muscle MyoSim, inelastic tendons): kinematics similar, but activation-EMG RMSE/r are 0.164/0.40 (HyFyDy) versus 0.344/0.11 (MuJoCo).
  - *Take from it.* Do not claim muscle-level or metabolic fidelity from MuJoCo activations without an EMG check; report kinematic, activation and torque agreement separately; reuse its 8-muscle EMG comparison protocol.
  - *Left untested for this programme.* Single subject, imitation only, no device, no metabolic comparison; the 3D MuJoCo model failed the 140 s clip; no myolegs26 test; unknown whether activation error biases simulated exo benefit.
  - *On our server.* Protocol is cheap to replicate on our stack with any mocap+EMG walking set; the HyFyDy arm needs a license.
  - *Code and assets.* Checked 2026-09-23: no repository linked; paper promises OpenSim-to-reference data for MuscleMimic and a trained subject-specific HyFyDy model.
  - *Also relevant to:* motion_imitation_rewards
- **Musculoskeletal Motion Imitation for Learning Personalized Exoskeleton Control Policy in Impaired Gait** 🆕 — Choi, Park, Halilaj, Kang. arXiv preprint, 2026-04-10. arXiv:2604.09431 · doi:10.48550/arXiv.2604.09431 · [link](https://arxiv.org/abs/2604.09431)
  - *Idea.* Imitation-trained H2190 (90-muscle, Hyfydy) human, then a later SAC stage for hip/knee/ankle exo torques; simulated metabolic cost (Umberger/Uchida) falls 4.57%/6.95% (hip, walk/run) and 6.15%/13.81% (ankle) over 0.6-2.2 m/s; deficit models get asymmetric assistance.
  - *Take from it.* Compute anchor on our exact GPU: SAC, 96 Hyfydy envs, 600M steps in ~48 h on an RTX 5090; simulated hip benefit in running is small (6.95%), which sets Phase-2 expectations.
  - *Left untested for this programme.* No hardware test; running only to 2.2 m/s; no fixed-versus-adapting-human ablation, rate-limited velocity-proportional baseline, sprint speeds or cable-actuator limits reported.
  - *On our server.* No code; replicable only via SCONE/Hyfydy plus SB3 SAC; license required.
  - *Code and assets.* Checked 2026-09-23: no code link in the paper.
  - *Also relevant to:* motion_imitation_rewards, sprint_biomech_exosuits
- **Towards Embodied AI with MuscleMimic: Unlocking full-body musculoskeletal motor learning at scale** — Li, Wang, Ziliotto, Simos, Kovecses, Durandau, Mathis. arXiv preprint, 2026-03-26. arXiv:2603.25544 · doi:10.48550/arXiv.2603.25544 · [link](https://arxiv.org/abs/2603.25544) · [code](https://github.com/amathislab/musclemimic)
  - *Idea.* JAX PPO motion imitation for muscle-actuated humanoids on MuJoCo Warp: 416-muscle MyoFullBody and 126-muscle bimanual models, SMPL retargeting, 8192 envs at ~1.3x10^4 steps/s on one H100; walking/running kinematics r 0.90/0.81, EMG r only 0.2-0.6.
  - *Take from it.* Evidence that MyoSim muscle models train on MJWarp at scale on the same MuJoCo 3.4 that MyoAssist pins; reuse its JAX PPO (single-epoch updates) and GPU-to-CPU policy transfer check.
  - *Left untested for this programme.* No legs-only 26/80-muscle model, no device or external exo torque, tracking reward only, running validated only at 1.8 m/s, no sprinting, and no 32 GB-GPU memory/throughput figures.
  - *On our server.* Benchmarked on H100 80 GB; a 32 GB RTX 5090 needs fewer envs; UniExo ran MJWarp on a Blackwell workstation GPU.
  - *Code and assets.* Checked 2026-09-23: Apache-2.0, last push 2026-09-21 (release tag 'preprint'); JAX 0.7.2 + mujoco 3.4.0 + warp-lang 1.10; PPO training, SMPL retargeting, Hugging Face checkpoints (amathislab/mm-fullbody-base); training needs Linux + NVIDIA GPU.
  - *Also relevant to:* gpu_batched_physics
- **Emergence of natural and robust bipedal walking by learning from biologically plausible objectives (journal title; arXiv title: Natural and Robust Walking using Reinforcement Learning without Demonstrations in High-Dimensional Musculoskeletal Models)** — Schumacher, Geijtenbeek, Caggiano, Kumar, Schmitt, Martius, Haeufle. iScience 28(4):112203 (2025); preprint arXiv 2309.02976 titled 'Natural and Robust Walking using Reinforcement Learning without Demonstrations in High-Dimensional Musculoskeletal Models'. arXiv:2309.02976 · doi:10.1016/j.isci.2025.112203 · [link](https://doi.org/10.1016/j.isci.2025.112203) · [code](https://github.com/martius-lab/depRL)
  - *Idea.* Mocap-free RL (DEP-RL) learns near-natural walking in four models (18-90 muscles; Hyfydy and MuJoCo MyoLeg) with r = r_vel - c_effort - c_pain; c_effort = alpha*a^3 + excitation smoothness + active-muscle count, alpha adapted by a constrained-optimization schedule; running at 5.2 m/s shown.
  - *Take from it.* A mocap-free human reward to compare against SMAT's imitation stage: r_vel flat above target speed plus adaptive a^3 effort; their finding that metabolic-energy or cost-of-transport rewards gave worse kinematics.
  - *Left untested for this programme.* No exoskeleton or external device; no 26-muscle MyoAssist body; MyoLeg gaits were less human-like than Hyfydy ones; no co-adaptation, metabolic validation, or sprint speeds in 80-90-muscle models.
  - *On our server.* pip install deprl; Hyfydy is CPU-based but licensed; the free MyoLeg route gives less natural gait.
  - *Code and assets.* Checked 2026-09-23: depRL (MIT, last push 2025-12-05) has training configs and pretrained Hyfydy/sconegym and MyoLeg baselines; cost terms live in tgeijten/sconegym gaitgym.py; Hyfydy requires a trial or paid license.
  - *Also relevant to:* physiology_grounded_control
- **KINESIS: Motion Imitation for Human Musculoskeletal Locomotion** 📚 — Simos, Chiappa, Mathis. ICRA 2026 (arXiv v3 2026-03-25; repo README keeps the v1 title 'KINESIS: Reinforcement Learning-Based Motion Imitation for Physiologically Plausible Musculoskeletal Motor Control'), 2025. arXiv:2503.14637 · [link](https://arxiv.org/abs/2503.14637) · [code](https://github.com/amathislab/Kinesis)
  - *Idea.* Model-free imitation on the 80-muscle MyoLeg (up to 290 muscles in v2.0) from 1.8 h of KIT locomotion including running: Lattice-exploration experts trained by negative mining and fused by a mixture-of-experts; the prior is reused for goal reaching and penalty kicks.
  - *Take from it.* A pretrained 80-muscle locomotion prior as a Phase-2 human comparator and imitation-reward recipe; weigh its EMG-correlation claim against Beyond Kinematics and MuscleMimic.
  - *Left untested for this programme.* No exoskeleton or external torque, no metabolic estimate, no sprint-speed test reported, and no check that the imitation prior stays valid when a device changes joint moments.
  - *On our server.* CPU-threaded (MuscleMimic cites ~10 days on 128 CPU envs + A100); feasible on 64 cores but slow; 30 GB RAM caps env count.
  - *Code and assets.* Checked 2026-09-23: v2.0 (2026-02-03), BSD-3-Clause per README; training/eval code and pretrained checkpoints via Hugging Face; KIT motions must be fetched from AMASS; CPU-thread training.
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/simulation/KINESIS-PREPARATION.md`
  - *Also relevant to:* motion_imitation_rewards
- **DEP-RL: Embodied Exploration for Reinforcement Learning in Overactuated and Musculoskeletal Systems** — Schumacher, Haeufle, Buechler, Schmitt, Martius. ICLR 2023 (notable top-25%, per repo README); arXiv 2022. arXiv:2206.00484 · [link](https://arxiv.org/abs/2206.00484) · [code](https://github.com/martius-lab/depRL)
  - *Idea.* Blends differential extrinsic plasticity (DEP), a self-organizing controller that within seconds produces correlated, state-space-covering muscle excitations, into RL training to fix exploration in overactuated musculoskeletal systems; faster, more robust reaching and locomotion learning than standard action noise.
  - *Take from it.* A drop-in exploration fix if PPO on myolegs26 or 80-muscle legs stalls; pretrained MyoLeg and Hyfydy baselines to benchmark our walker against.
  - *Left untested for this programme.* Never tested with an attached exoskeleton or a second learning agent; unknown whether DEP exploration helps or destabilizes staged human-exo co-adaptation; no GPU-batched implementation.
  - *On our server.* CPU tonic implementation, MIT; a JAX/GPU port would be our own work.
  - *Code and assets.* Checked 2026-09-23: MIT, pip install deprl, last push 2025-12-05; tonic-based; pretrained MyoLeg (incl. MyoChallenge chase-tag) and Hyfydy walking/running baselines.
  - *Also relevant to:* physiology_grounded_control

### Should-read

- **Muscle Synergy Priors Enhance Biomechanical Fidelity in Predictive Musculoskeletal Locomotion Simulation** 📚 — Park, Choi, Ahn, Ahn. arXiv preprint, 2026-03-11 (v2 2026-05-28). arXiv:2603.10474 · [link](https://arxiv.org/abs/2603.10474) · [code](https://github.com/IlseungPark/Walk-RL)
  - *Idea.* SAC on Hyfydy H2190 (90 muscles) with a 30-D action: 10 NMF synergies per leg (10x40 matrix from one subject's inverse analysis) plus 10 trunk activations; stable 0.7-1.8 m/s and +/-6 degree walking with more physiological knee kinematics and moments than direct muscle control.
  - *Take from it.* A synergy action space as a fidelity and exploration control arm for our walker; the sum(a^2) effort term and the synergy-versus-unconstrained comparison design; Walk-RL code as a starting point.
  - *Left untested for this programme.* Single-subject synergies fixed across speeds; running untested; no device in this paper; unknown whether synergy constraints change the size of simulated exo benefit.
  - *On our server.* Hyfydy license needed; a synergy basis for myolegs26 muscles could be re-derived by static optimization.
  - *Code and assets.* Checked 2026-09-23: Walk-RL created 2025-11-26, last push 2026-06-26, no license; per KB audit it holds H2190 .hfd/.scone models, a 10x40 synergy matrix, SAC scripts and vendored sconegym, no trained models; project page ces40320.github.io/WebHomepage__Walk-RL.
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/research/code-and-transfer-audit-2026-09-13.md`
  - *Also relevant to:* physiology_grounded_control
- **Latent Exploration for Reinforcement Learning** — Chiappa, Marin Vargas, Huang, Mathis. NeurIPS 2023 (per repo README). arXiv:2305.20065 · [link](https://arxiv.org/abs/2305.20065) · [code](https://github.com/amathislab/lattice)
  - *Idea.* Lattice injects temporally correlated noise into the policy's latent layer, giving actuator-correlated action noise (full-covariance Gaussian); works with PPO and SAC; on MyoSuite reaching/manipulation it raised reward and found 20-60% more energy-efficient policies.
  - *Take from it.* Cheap exploration upgrade for PPO over many muscles (KINESIS uses it on 80-muscle legs); test whether it lowers co-contraction and effort cost in our walker.
  - *Left untested for this programme.* Original results cover reaching and manipulation, not gait with a device; untested in two-agent human-exo training or GPU-batched PPO; no myolegs26 ablation.
  - *On our server.* Old SB3 1.6.1 code; porting the latent-noise layer to rsl_rl or JAX is small.
  - *Code and assets.* Checked 2026-09-23: MIT, last push 2024-02-23; built on Stable-Baselines3 1.6.1 (Recurrent PPO and SAC); README notes gym/MyoSuite version conflicts.
- **MyoSim: Fast and physiologically realistic MuJoCo models for musculoskeletal and exoskeletal studies** — Wang, Caggiano, Durandau, Sartori, Kumar. ICRA 2022, pp. 8104-8111. doi:10.1109/ICRA46639.2022.9811684 · [link](https://doi.org/10.1109/ICRA46639.2022.9811684) · [code](https://github.com/MyoHub/myo_sim)
  - *Idea.* Automatic pipeline that converts OpenSim musculoskeletal models into MuJoCo, including hybrid musculoskeletal-exoskeletal models, claimed over two orders of magnitude faster than prior tools; adds fatigue and sarcopenia and demos exoskeleton co-simulation.
  - *Take from it.* Provenance of the myo_sim leg bodies MyoAssist composes and the precedent for device co-simulation; read its conversion checks before trusting muscle-level outputs.
  - *Left untested for this programme.* Predates the 26-muscle leg (still beta); abstract lists exoskeleton co-simulation only as a use case, with no lower-limb gait, EMG or metabolic validation stated.
  - *On our server.* pip install myo-sim; plain MuJoCo; myoconverter can re-convert OpenSim models if needed.
  - *Code and assets.* Checked 2026-09-23: myo_sim Apache-2.0, last push 2026-09-16; MyoLeg (80 muscles) 'stable', MyoLeg26 (26 muscles) 'beta'; OpenSim converter MyoHub/myoconverter last push 2024-10-22.
- **SCONE: Open Source Software for Predictive Simulation of Biological Motion** — Geijtenbeek. Journal of Open Source Software 4(38):1421, 2019. doi:10.21105/joss.01421 · [link](https://doi.org/10.21105/joss.01421) · [code](https://github.com/tgeijten/scone-core)
  - *Idea.* Predictive-simulation software: parameterized controllers (e.g., reflex-based gait) optimized by CMA-ES against objectives such as metabolic cost, on OpenSim or the faster Hyfydy engine (elastic Millard-type tendons, pennation); sconegym exposes it to Python RL.
  - *Take from it.* The compliant-tendon comparator: rerun key Phase 1/2 controllers on H2190 (90 muscles) to test whether conclusions survive tendon elasticity; Park's and Choi's exo work already uses this stack.
  - *Left untested for this programme.* For this programme: no transfer of MuJoCo-trained exo policies into Hyfydy bodies, no GPU batching, no sprint-speed exosuit study found in its gyms.
  - *On our server.* CPU engine suits the 64-core EPYC; clear Hyfydy license terms before depending on it.
  - *Code and assets.* Checked 2026-09-23: scone-core Apache-2.0 (last push 2026-09-09); sconegym Apache-2.0 (last push 2026-05-15); Hyfydy engine is closed, licensed software (trial available), no paper found.
- **A neural circuitry that emphasizes spinal feedback generates diverse behaviours of human locomotion** — Song, Geyer. The Journal of Physiology 593(16):3493-3511, 2015. doi:10.1113/JP270228 · [link](https://doi.org/10.1113/JP270228) · [code](https://github.com/neumovelab/myoassist/tree/main/ctrl_optim/ctrl/reflex)
  - *Idea.* A CPG-free spinal controller of 10 reflex modules for stance and swing produces 3D walking and running, speed changes, slopes, stairs, turning and obstacle avoidance in a neuromechanical model, arguing feedback integration matters more than central pattern generation.
  - *Take from it.* The structured human MyoAssist already ships: co-optimize reflex gains with a hip-exo profile by CMA-ES to test whether SMAT's gain needs a learned, co-adapting human.
  - *Left untested for this programme.* Reflex parameters are optimized per behaviour, not adapted online to assistance; no exoskeleton; unknown whether reflex-human exo benefit matches RL-human benefit in myolegs26 at 1.25 m/s.
  - *On our server.* 63-126 reflex parameters plus an exo spline; CMA-ES parallelizes across 64 CPU cores, no GPU needed.
  - *Code and assets.* Checked 2026-09-23: reimplemented in MyoAssist ctrl_optim (51 params per leg 2D / 63 in 3D, CMA-ES; 13 muscle groups, runs on myolegs22/26/80) and in osim-rl loco_reflex_song2019.py.
  - *Also relevant to:* physiology_grounded_control

### Reference

- **MyoChallenge 2024: A New Benchmark for Physiological Dexterity and Agility in Bionic Humans** — Wang, Tan, Hodossy, Lyu, Schumacher, ... Su, Song, Gionfrida, Sartori, Durandau, Kumar, Caggiano. NeurIPS 2025 Datasets and Benchmarks Track (Advances in NeurIPS 38, pp. 69751-69773; proceedings page dated 2026-04-23). doi:10.52202/085713-2100 · [link](https://papers.nips.cc/paper_files/paper/2025/hash/5a8f69523f9511a5706568c552de0ebb-Abstract-Datasets_and_Benchmarks_Track.html) · [code](https://github.com/MyoHub/myosuite)
  - *Idea.* Benchmark report: prosthetic passover manipulation (myoMPL) and locomotion over varied terrain with myoOSL (bilateral MyoLeg with a transfemoral amputation plus Open Source Leg); >50 teams, >290 submissions; imitation learning, muscle synergies and model-based RL beat baselines about 10x.
  - *Take from it.* The closest community benchmark for joint biological-plus-device leg control; its winning strategies (imitation, synergies, model-based RL) are candidate recipes for the human agent.
  - *Left untested for this programme.* Device is a prosthesis, not an assistive exoskeleton; no metabolic metric, no co-adaptation of a device policy, no running or sprinting track.
  - *On our server.* Environment installs with MyoSuite on CPU; useful as a smoke test for our training runner.
  - *Code and assets.* Checked 2026-09-23: tasks live in MyoSuite (v2.12.0, 2026-04-23, Apache-2.0); winning-solution code not checked.
- **Deep reinforcement learning for modeling human locomotion control in neuromechanical simulation** — Song, Kidzinski, Peng, Ong, Hicks, Levine, Atkeson, Delp. Journal of NeuroEngineering and Rehabilitation 18 (2021). doi:10.1186/s12984-021-00919-y · [link](https://doi.org/10.1186/s12984-021-00919-y) · [code](https://github.com/stanfordnmbl/osim-rl)
  - *Idea.* Reviews neuromechanical simulation and deep RL for human locomotion and reports the NeurIPS 2017-2019 Learn to Move competitions (>1300 teams), whose top teams produced turning and walk-to-stand transitions without reference motion data.
  - *Take from it.* The field's framing of RL controllers as testable hypotheses about human control, its validation checklist, and the osim-rl Song-Geyer reflex code MyoAssist cites.
  - *Left untested for this programme.* Predates GPU-batched muscle simulation, MuJoCo muscle bodies and exoskeleton co-adaptation; its call for physiological validation of RL controllers remains open for assisted gait.
  - *On our server.* Read only; osim-rl has been inactive since 2022.
  - *Code and assets.* Checked 2026-09-23: osim-rl MIT, last push 2022-01-24 (inactive), OpenSim-based.

### Already claimed by published work (cite it, compare against it, do not headline it)

- Mocap-free RL produces near-natural, terrain-robust walking in 80-90-muscle 3D models from effort/pain objectives (Schumacher et al., iScience 2025).
- An open, composable human + device + terrain MuJoCo framework with RL and reflex-optimization pipelines for exoskeletons and prostheses (MyoAssist 1.0, Robbins et al., bioRxiv 2026).
- GPU-parallel (MuJoCo Warp) motion imitation with a 416-muscle full body, validated on walking and running kinematics (MuscleMimic, Li et al., arXiv 2026).
- Kinematic imitation fidelity does not imply EMG-faithful muscle activations in MuJoCo; elastic-tendon HyFyDy agrees better with EMG (Beyond Kinematics, Ahmad et al., arXiv 2026; also MuscleMimic's own EMG analysis).
- A single hip-exo policy co-adapted by multi-agent RL with a multi-skill (walk/turn/run/backward) 80-MTU human policy and deployed on hardware without mode switching (UniExo, Yuan et al., arXiv 2026).
- An 80-muscle MyoLeg imitation prior with EMG-correlated activations and downstream control tasks (KINESIS, Simos et al., ICRA 2026).
- Simulation-only hip/ankle exo policies from musculoskeletal imitation + RL cut simulated metabolic cost in walking and running and personalise to muscle deficits (Choi et al., arXiv 2026).
- An RL hip-exo policy trained against a fixed reflex-driven planar walker transfers zero-shot with 15.2% net metabolic reduction in eight people (Barati et al., RA-L 2026).
- Synergy-constrained action spaces improve biomechanical fidelity of predictive 3D RL walking (Park et al., arXiv 2026) and learning efficiency on MyoLeg terrains (SAR, Berg et al., RSS 2023).

### Open questions this programme can attack

- Is co-adaptation necessary? Missing experiment: on one myolegs26 body at 1.25 m/s, compare SMAT-style staged co-adaptation, an exo policy trained against a frozen human (Barati-style), u = k * normalised hip velocity with SMAT's torque cap and a rate limit, and a CMA-ES-tuned hip phase profile co-optimized with Song-Geyer reflexes, with fixed seeds and pre-registered tolerances.
- Does the simulated exo benefit survive tendon compliance? Missing experiment: evaluate the reconstructed SMAT policy's torque profile and the velocity-proportional controller in Hyfydy H2190 (elastic tendons), comparing activation and metabolic deltas with the rigid-tendon MuJoCo result.
- CPU-vs-GPU equivalence for a human + device model: missing experiment: roll the same myolegs26 + Hippo_L1 policy in CPU MuJoCo and MuJoCo Warp and compare gait, contact and exo power traces (MuscleMimic checked transfer only for its human-only models).
- Throughput on the programme's GPU is unpublished for 26/80-muscle legs with a device: missing experiment: env-count vs memory vs steps/s sweep in mjlab/MJWarp on the RTX 5090 (32 GB, sm_120) and 30 GB host RAM before fixing training budgets.
- Exploration under two-agent training: missing experiment: Stage-4-style co-adaptation with Gaussian vs Lattice vs synergy human actions, measuring training stability and seed-to-seed variance of the exo benefit.
- Metric dependence: SMAT reports simulated muscle-activation reductions while Choi et al. report Umberger/Uchida metabolic cost; missing experiment: compute sum(a^2), sum(a^3) and two metabolic models on identical rollouts to show how much the exo benefit depends on the proxy.
- Cable realism: assist_sim's HMEDI_L1 models hip cables as spatial tendons, but no paper compares ideal hip torque (Hippo_L1) with a cable transmission (slack, tension cap, bandwidth) inside co-adaptation; missing experiment: identical training on both devices, then the same with Moon-style exosuit limits.
- Sprint-speed muscle simulation: missing experiment: 80-muscle MyoLeg (rigid tendon) versus H2190 (elastic) at sprint speeds under an identical reward, comparing contact time, peak GRF and plantarflexor fiber work before adding the hip exosuit.


---

## 4. GPU-batched physics (the throughput lever)

**What this literature tells the programme**

- GPU non-determinism is documented behaviour, not a defect: MJWarp 3.14.0 does not support Warp's deterministic mode (maintainer, 2026-09-10); a maintainer determinism API (PR #1687, DeterminismType flags) opened 2026-09-22, and a community implementation (PR #1422) cost 30-80% throughput. Keep native CPU MuJoCo as the bitwise reference and design parity statistically.
- Not every CPU-GPU gap is chaos: MJWarp #1662 (IMPLICIT, 1.45e12 versus 22.7 rad/s, fixed by #1663 before 3.14.0) and #1510 (CCD versus box-box collider behaviour, reproducible in MuJoCo C) were defects or configuration effects. Run contact-free, fixed-collider and deterministic-CPU checks before attributing divergence to chaos.
- Published parity evidence for muscle models is weak: UniExo reports none; MuscleMimic compares policy-level metrics; MyoSuite 3's CPU-versus-mjlab myoLegWalk test only bounds observation differences below 50; msk-warp reports 20/50 and 45/50 native-versus-Warp exceedances of 1e-4 after one and four control steps on myolegs26. Even CPU-to-CPU replay of myoLegWalk jumps to 4.22e-5 after ~25 steps.
- Borrow port-validation statistics from climate modelling: Rosinski-Williamson perturbation-growth envelopes for early horizons, CESM-ECT ensemble consistency (151 perturbed members, PCA, three test runs, 0.5% false-positive rate) for full strides, with UF-CAM-ECT showing nine-step tests can suffice; GPUSimBench's within-run and between-run W1 metrics are the robotics analogue.
- Physics is unlikely to be the binding constraint: the probe reached ~235k control transitions/s physics-only at nworld=8192, mjlab's RTX 5090 nightly spends 54-68% of time in the environment layer, and UniExo's full pipeline sustains 3.7e4 environment steps/s including PPO. Profile physics, environment layer and learner separately.
- Muscle-model GPU cost concentrates in tendon kinematics (MJWarp nightly MyoArm: ~40% of per-step time; 1.41M steps/s at 8,192 worlds on an RTX 6000 Ada), so 26- versus 80-muscle legs should scale with tendon count and wrapping more than with DoF.
- Blackwell (sm_120) works when every wheel is a CUDA 12.8+ build: warp-lang 1.17 (CUDA 12.9), JAX >= 0.6.0, PyTorch cu128. MyoSuite's MJX extra (jax<0.5.3) predates this, and offscreen rendering beside Warp in one headless process can segfault (mjlab #1160).
- Version drift confounds parity and precedent numbers: MuscleMimic pins MuJoCo 3.4.0, mjlab ~=3.11, Newton ~=3.12 and the probe 3.14.0; 3.13-3.14 carry breaking solver and tendon changes (e.g., tendon actuatorfrclimited now defaults to 'auto'). Freeze one release for both the CPU reference and GPU runs.

### Must-read

- **GPUSimBench: Towards Scalable and Reliable GPU-Accelerated Simulators in Embodied AI** 🆕 — Zhang, Yuan, Yan, Ma, Li, Pang, Yudin. arXiv preprint (accepted to IROS 2026). arXiv:2607.13059 · doi:10.48550/arXiv.2607.13059 · [link](https://arxiv.org/abs/2607.13059)
  - *Idea.* Benchmarks seven GPU simulators (Isaac Lab, ManiSkill, Genesis, Madrona, MuJoCo Warp, MJX, MuJoCo Playground) for real-world alignment, scaling and determinism, using Wasserstein-1 distances between final-state distributions across parallel environments and across repeated fixed-seed runs.
  - *Take from it.* Reuse its two metrics, within-run parallel W1 and between-run W1, as a parity template. MuJoCo Warp showed both variabilities (Type 3); MJX showed neither at reported precision (RTX 5070).
  - *Left untested for this programme.* Rigid cubes and a Panda arm only: no muscles, tendons or gait; no comparison against CPU MuJoCo; MuJoCo Warp version unstated; no formal hypothesis test or tolerance.
  - *On our server.* Metrics are cheap to reproduce on the 5090; add a CPU-MuJoCo ensemble as the reference distribution.
  - *Code and assets.* No repository link in v1 (2026-07-06); the text says the benchmark and protocol will be released on a project website, which was not located; checked 2026-09-23
- **MyoSuite 3.0 release branch (ms3; pull request #406): CPU Gymnasium and mjlab/MuJoCo Warp backends** 🆕 📚 — Caggiano, Hodossy, Fischer, Wang, MyoSuite Team (per ms3 README citation). GitHub pull request (open), 2026. [link](https://github.com/MyoHub/myosuite/pull/406) · [code](https://github.com/MyoHub/myosuite/tree/ms3)
  - *Idea.* Makes CPU Gymnasium and mjlab (MuJoCo Warp) the supported backend pair under one env_id, bound by a five-invariant contract (observation layout, action mapping, control timing, identical XML, fixed normalization); MJX is labelled experimental; myoLegWalk is ported with 403-D observations and 80-D muscle actions.
  - *Take from it.* Adopt its frozen-rollout replay tests and contract. Even CPU-to-CPU replay of myoLegWalk jumps to 4.22e-5 after ~25 steps (contact ordering), so tolerances must be horizon-specific.
  - *Left untested for this programme.* Its GPU-gated CPU-versus-mjlab myoLegWalk diagnostic asserts only finite, below-50 observation differences ('trajectories need not be identical yet'); no statistical parity, myolegs26 or hip-exoskeleton task.
  - *On our server.* Unreleased: pin a commit. The mjlab extra resolves to mjlab's ~=3.11 MuJoCo pin; the MJX extra caps jax<0.5.3, predating JAX's CUDA 12.8 builds.
  - *Code and assets.* PR #406 (ms3 into dev) open since 2026-09-15, 171 commits; ms3 head 2026-09-23; latest tagged release still v2.12.0 (2026-04-23); mjlab extra: mjlab>=1.4.0, mujoco-warp>=3.7.0, warp-lang>=1.12.0, torch>=2.13.0; checked 2026-09-23
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/simulation/METHODS-AND-BACKENDS.md`
- **mjlab: A Lightweight Framework for GPU-Accelerated Robot Learning** — Zakka, Liao, Yi, Le Lay, Sreenath, Abbeel. arXiv preprint, 2026. arXiv:2601.22074 · doi:10.48550/arXiv.2601.22074 · [link](https://arxiv.org/abs/2601.22074) · [code](https://github.com/mujocolab/mjlab)
  - *Idea.* Pairs Isaac Lab's manager-based API (observations, rewards, events, terminations, curricula) with MuJoCo Warp, exposing native MjModel/MjData, CUDA-graph stepping, per-world randomization, MJCF-wrapped or native actuators including muscles, and NaN/Inf detection with a replayable rolling state buffer.
  - *Take from it.* Its nightly benchmark runs on an RTX 5090 at 4,096 envs: environment-layer overhead is 54-68%; G1 tracking gives 730k physics-only versus 249k full-environment control steps/s (2026-09-23). Use its NaN replay unattended.
  - *Left untested for this programme.* Scope is rigid-body robots: the paper has no muscle or tendon task, no throughput tables, and no CPU-MuJoCo parity or determinism analysis.
  - *On our server.* Pins mujoco(-warp) ~=3.11 while the probe used 3.14. Issue #1160: headless EGL rendering beside Warp segfaults on sm_120; render in a separate process.
  - *Code and assets.* Apache-2.0; v1.6.0 (2026-08-09, also on PyPI); pins mujoco and mujoco-warp ~=3.11.0, warp-lang>=1.14, rsl-rl-lib==5.5.1, torch from the cu128 index; main pushed 2026-09-22; checked 2026-09-23
- **MuJoCo Warp (MJWarp): GPU-optimized version of the MuJoCo physics simulator, designed for NVIDIA hardware** 📚 — Google DeepMind and NVIDIA. GitHub repo + documentation, 2025. [link](https://mujoco.readthedocs.io/en/stable/mjwarp/index.html) · [code](https://github.com/google-deepmind/mujoco_warp)
  - *Idea.* Warp re-implementation of MuJoCo for batched simulation on NVIDIA GPUs, optimized for throughput rather than latency. Supports all MJCF actuator, tendon and wrapping types, raises exceptions on unsupported features (e.g., non-zero geom margin with some CCD colliders), and is documented as non-deterministic on GPU.
  - *Take from it.* Size nconmax/njmax, capture CUDA graphs, check Data.overflow. Nightly MyoArm benchmark (63 muscles, 8,192 worlds, RTX 6000 Ada): 1.41M steps/s, 85 s JIT, 1.77 GB; tendon kinematics take ~40% of step time.
  - *Left untested for this programme.* No CPU-versus-GPU parity for contact-rich muscle models; GPU determinism unsupported in 3.14.0 (API PR #1687 opened 2026-09-22; open PR #1533 lists tendon and actuator-moment accumulations as order-sensitive); nightlies use Ada, not sm_120.
  - *On our server.* Use 3.14.0 on both sides: it includes the IMPLICIT Coriolis-derivative fix (#1663) for a 1.45e12 versus 22.7 rad/s CPU mismatch. Deterministic reference: native MuJoCo.
  - *Code and assets.* Apache-2.0; v3.14.0 released 2026-09-22 (PyPI mujoco-warp 3.14.0 same day); repo created 2025-03-17; nightly benchmarks on gh-pages (last MyoArm row 2026-09-03); no technical report found; checked 2026-09-23
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/simulation/METHODS-AND-BACKENDS.md`
- **A new ensemble-based consistency test for the Community Earth System Model (pyCECT v1.0)** — Baker, Hammerling, Levy, Xu, Dennis, Eaton, Edwards, Hannay et al.. Geoscientific Model Development 8, 2829-2840, 2015. doi:10.5194/gmd-8-2829-2015 · [link](https://doi.org/10.5194/gmd-8-2829-2015) · [code](https://github.com/NCAR/PyCECT)
  - *Idea.* Replaces bit-for-bit reproducibility with a statistical test: a 151-member ensemble differing only by O(1e-14) initial perturbations defines PCA score distributions of standardized global means; runs from a new platform fail when the same PCs fall outside 2 sigma.
  - *Take from it.* Transferable decision rule: three test runs; fail if at least three PCs exceed 2 sigma in at least two runs (0.5% false-positive rate). Follow-up UF-CAM-ECT (Milroy 2018) needs only nine time steps.
  - *Left untested for this programme.* Climate model without contacts, discrete events or learned controllers; annual global means must be replaced by gait statistics, and power against small physics bugs must be re-established for locomotion.
  - *On our server.* A ~150-rollout perturbed CPU ensemble is cheap on 64 cores; treat pyCECT as a reference implementation, not a drop-in tool.
  - *Code and assets.* Apache-2.0; PyCECT release 3.3.1 (2024-06-14); last push 2026-06-15; checked 2026-09-23

### Should-read

- **Scaling Whole-Body Human Musculoskeletal Behavior Emulation for Specificity and Diversity** — Wei, Zuo, Zhuang, Gong, Liu, Sui. arXiv preprint, 2026. arXiv:2603.29332 · doi:10.48550/arXiv.2603.29332 · [link](https://arxiv.org/abs/2603.29332)
  - *Idea.* Runs the ~700-muscle MS-Human-700 model on MuJoCo Warp, chosen over MJX because active contact and constraint sets vary, and adds adversarial reward aggregation and value-guided flow exploration to emulate walking, running, dance, cartwheels and backflips.
  - *Take from it.* Only RTX 5090 muscle-model numbers found: forward dynamics 7,107 SPS versus 2,469 on 224 CPU cores; training 4,460 SPS on one GPU versus 1,326 for an SB3 CPU baseline; 2 ms step, 50 Hz control.
  - *Left untested for this programme.* No state-level CPU-versus-GPU trajectory comparison; environment counts behind the SPS figures appear only in plots (training trials used 2,048 envs); code unreleased; no exoskeleton.
  - *On our server.* Direct 5090 evidence: 700 muscles train at ~4.5k SPS; 26- or 80-muscle legs should be faster, but that is unmeasured.
  - *Code and assets.* Project page https://lnsgroup.cc/research/MS-Emulator/ shows 'Code Coming Soon'; checked 2026-09-23
- **msk-warp: MJWarp musculoskeletal differentiation RL environment** — mar-yan24 (individual developer). GitHub repo, 2026. [link](https://github.com/mar-yan24/msk-warp) · [code](https://github.com/mar-yan24/msk-warp)
  - *Idea.* Individual research code for MyoLeg26 (the myolegs26 beta model: nq=47, nv=46, 26 muscles) on MuJoCo Warp that compares native float64 MuJoCo and Warp states at 1, 4 and 16 physics steps and checks simulation gradients against finite differences.
  - *Take from it.* Closest precedent on the programme's model: native-versus-Warp forward cases exceeded a 1e-4 joint-velocity tolerance in 20/50 states after one control step and 45/50 after four; direct-Warp replays varied across repetitions.
  - *Left untested for this programme.* Self-reported and unreviewed; uses an unmerged MJWarp PR stack, not a release; short horizons only; no ensemble statistics or exoskeleton; its five-seed PPO baseline never walked (0/160 survivors).
  - *On our server.* Ran on an RTX 4060 laptop; reuse its hash-pinned manifests and preregistered gates, not its patched backend.
  - *Code and assets.* Apache-2.0; no releases; README status dated 2026-09-13; last push 2026-09-23; requires a local stack of unmerged MJWarp PR #1423 (differentiable stepping), MuJoCo 3.10.0, Warp 1.14.0; checked 2026-09-23
- **Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning** — Rudin, Hoeller, Reist, Hutter. Conference on Robot Learning (CoRL 2021). arXiv:2109.11978 · doi:10.48550/arXiv.2109.11978 · [link](https://arxiv.org/abs/2109.11978) · [code](https://github.com/leggedrobotics/legged_gym)
  - *Idea.* Shows that PPO with thousands of parallel simulated robots on one workstation GPU trains ANYmal locomotion in minutes, analyses which algorithm components matter in this massively parallel regime, and adds a game-inspired terrain curriculum; policies transfer to hardware.
  - *Take from it.* Flat terrain in under four minutes, rough in twenty. mjlab and UniExo train with rsl_rl, the PPO library released with it, so re-tune rollout length and minibatching for SMAT at thousands of GPU environments.
  - *Left untested for this programme.* Rigid quadruped with PD-controlled joints on PhysX; no muscles, multi-agent co-adaptation, simulator parity or determinism analysis.
  - *On our server.* Isaac Gym is superseded by Isaac Lab (legged_gym last pushed 2025-05); take the recipe through rsl_rl in mjlab, not legged_gym.
  - *Code and assets.* legged_gym (Isaac Gym; custom licence, no releases) last pushed 2025-05-29; companion PPO library rsl_rl v5.5.1 (2026-09-09) is pinned by mjlab; checked 2026-09-23
- **The Accumulation of Rounding Errors and Port Validation for Global Atmospheric Models** — Rosinski, Williamson. SIAM Journal on Scientific Computing 18, 552-564, 1997. doi:10.1137/S1064827594275534 · [link](https://doi.org/10.1137/S1064827594275534)
  - *Idea.* Studies how machine-rounding-sized differences grow in the NCAR CCM2 climate model and proposes validating ports by checking that port-induced differences grow no faster than rounding-level perturbations of the original code.
  - *Take from it.* Direct recipe for CPU-versus-MJWarp: perturb CPU initial states at float32 rounding scale, record divergence growth curves, then require the GPU-versus-CPU curve to stay inside that envelope over early steps.
  - *Left untested for this programme.* Baker et al. report it breaks for ill-conditioned CAM5 physics, where tolerances are exceeded within a few steps; contact-rich gait may saturate similarly. No code, contacts or controllers.
  - *On our server.* Cheap (dozens of paired rollouts); use it for short horizons and single swing phases, ensemble tests for full strides.
  - *Code and assets.* No code (method paper)

### Reference

- **MuJoCo XLA (MJX) documentation** 📚 — Google DeepMind (MuJoCo team). documentation, 2026. [link](https://mujoco.readthedocs.io/en/stable/mjx.html) · [code](https://github.com/google-deepmind/mujoco/tree/main/mjx)
  - *Idea.* Documents MJX's two implementations: MJX-JAX, a JAX re-implementation supporting muscle dynamics, gain and bias with fixed and spatial tendons, and MJX-Warp, MuJoCo Warp behind the JAX API, supporting all actuator, tendon and wrapping types with faster contacts.
  - *Take from it.* Use MJX-JAX only when JAX autodiff or JAX trainers are required; for NVIDIA throughput prefer MJWarp (humanoid: 3.35M SPS pure Warp versus 2.96M through JAX FFI).
  - *Left untested for this programme.* The page gives no precision, determinism or MuJoCo-C agreement guarantees and no muscle-model benchmarks; single-scene MJX-JAX can be 10x slower than MuJoCo.
  - *On our server.* JAX CUDA wheels are built with CUDA 12.8+ from jax 0.6.0; test older pins such as MyoSuite's jax<0.5.3 before relying on sm_120.
  - *Code and assets.* Part of google-deepmind/mujoco (Apache-2.0); PyPI mujoco-mjx 3.14.0 (2026-09-22); no dedicated MJX paper found; checked 2026-09-23
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/simulation/METHODS-AND-BACKENDS.md`
- **Isaac Lab: A GPU-Accelerated Simulation Framework for Multi-Modal Robot Learning** 📚 — NVIDIA: Mittal, Roth, Tigue, Richard, Zhang, Du et al.. arXiv preprint, 2025. arXiv:2511.04831 · doi:10.48550/arXiv.2511.04831 · [link](https://arxiv.org/abs/2511.04831) · [code](https://github.com/isaac-sim/IsaacLab)
  - *Idea.* Successor to Isaac Gym combining GPU PhysX, tiled RTX rendering, actuator and sensor models, domain randomization and a manager-based task API; outlines integration with Newton, the Warp-based engine that uses MuJoCo Warp as its primary backend.
  - *Take from it.* Origin of the manager-based API mjlab copies. Isaac Lab 3.0 Early Access (2026-09-16) runs physics=newton_mjwarp without Isaac Sim, a fallback host for MJWarp if mjlab stalls.
  - *Left untested for this programme.* No muscle or tendon models; MJCF muscle import through Newton is undocumented in the paper; no CPU-MuJoCo parity or determinism study.
  - *On our server.* Full Isaac Sim lists 32 GB minimum RAM (server has 30 GB); only the kit-less Newton path looks practical. GA targeted late October 2026.
  - *Code and assets.* BSD-3-Clause; v3.0.0-EA (2026-09-16) built for Isaac Sim 6.1, Warp 1.16 and Newton 1.5.2, with kit-less physics=newton_mjwarp; GA targeted end of October 2026; checked 2026-09-23
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/simulation/METHODS-AND-BACKENDS.md`
- **MuJoCo Playground** — Zakka, Tabanpour, Liao, Haiderbhai, Holt, Luo, Allshire, Frey et al.. arXiv preprint, 2025. arXiv:2502.08844 · doi:10.48550/arXiv.2502.08844 · [link](https://arxiv.org/abs/2502.08844) · [code](https://github.com/google-deepmind/mujoco_playground)
  - *Idea.* Open-source MJX-based robot-learning suite covering quadrupeds, humanoids, dexterous hands and arms, with Madrona batch rendering, JAX PPO training in minutes on one GPU, and zero-shot sim-to-real transfer from state and pixel policies.
  - *Take from it.* Ready A/B harness: the same tasks run with --impl warp under JAX PPO or rsl_rl PPO, and v0.2.0 made MuJoCo Warp the default; throughput tables are per-environment on one A100.
  - *Left untested for this programme.* No musculoskeletal environments; the paper predates the MuJoCo Warp default; no MJX-versus-MuJoCo-C numerical or statistical comparison.
  - *On our server.* Good for backend A/B checks on rigid tasks; its JAX stack needs CUDA 12.8+ JAX wheels on sm_120.
  - *Code and assets.* Apache-2.0; v0.2.0 (2026-03-16) made MuJoCo Warp the default implementation for all envs; main requires mujoco>=3.6.0, warp-lang>=1.17.0, brax>=0.14.2; checked 2026-09-23
- **mjlab_myosuite: Interface of myosuite with mjlab** — MyoHub (MyoSuite team). GitHub repo, 2025. [link](https://github.com/MyoHub/mjlab_myosuite) · [code](https://github.com/MyoHub/mjlab_myosuite)
  - *Idea.* Early-prototype bridge registering MyoSuite environments with mjlab's training stack; its minimal_myoleg branch adds standalone MyoLeg, MyoSkeleton and MyoLegsTorso velocity and balance tasks with tendon/synergy observations and actions on public mjlab.
  - *Take from it.* Starting point for MyoLeg-on-mjlab task configs. The Fitz-Yuan fork, presumed UniExo-related (identity unverified), matches upstream on all four branches, so no UniExo exoskeleton code is public here.
  - *Left untested for this programme.* Its 'parity' tests compare reward weights and configs against an mjlab fork, not physics; no CPU-versus-GPU trajectories or exoskeleton.
  - *On our server.* Stale since March 2026 and tracks unpinned mjlab git HEAD; MyoSuite's ms3 mjlab backend supersedes it.
  - *Code and assets.* Apache-2.0; 'Early Prototype', no releases; main last commit 2026-02-05, branch minimal_myoleg 2026-03-06; fork Fitz-Yuan/mjlab_myosuite (created 2026-07-23) is identical to upstream on all four branches; checked 2026-09-23
- **NVIDIA Warp: a Python framework for GPU-accelerated simulation, robotics, and machine learning** 📚 — NVIDIA. GitHub repo + documentation, 2022. [link](https://nvidia.github.io/warp/) · [code](https://github.com/NVIDIA/warp)
  - *Idea.* Python kernel language that JIT-compiles to CUDA or CPU and underlies MuJoCo Warp and Newton; since v1.15 it offers opt-in deterministic modes (RUN_TO_RUN bit-exact on one GPU architecture, GPU_TO_GPU across architectures) that record, sort and reduce atomics.
  - *Take from it.* Use it for custom deterministic kernels (e.g., reward or statistics reductions); cost depends on atomic contention, and overflows inside CUDA-graph capture go unreported, so size deterministic_max_records conservatively.
  - *Left untested for this programme.* MJWarp does not support Warp's deterministic mode (maintainer, 2026-09-10; API PR #1687 open); enabling it silently dropped convex contacts (#1635). Determinism costs for muscle models are unmeasured.
  - *On our server.* warp-lang 1.17.0 (CUDA 12.9 wheels) ran on the 5090 in the probe; v1.12.1 fixed crashes when processes share a kernel cache on CUDA 12.8/12.9 builds.
  - *Code and assets.* Apache-2.0; v1.17.0 (2026-08-31), PyPI wheels built with CUDA Toolkit 12.9, CUDA 13.0 wheels on GitHub Releases; deterministic execution modes since v1.15.0 (2026-07-07); checked 2026-09-23
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/simulation/METHODS-AND-BACKENDS.md`

### Already claimed by published work (cite it, compare against it, do not headline it)

- SMAT-style human-exoskeleton co-adaptation trained on MuJoCo Warp/mjlab with an 80-muscle MyoLeg and a bilateral hip controller (UniExo, arXiv 2609.19690, September 2026).
- GPU (MuJoCo Warp)-trained muscle policies re-evaluated on CPU MuJoCo with consistent metrics and unchanged top ablations (MuscleMimic, arXiv 2603.25544).
- A consumer RTX 5090 with MuJoCo Warp out-trains a 224-core CPU cluster on a ~700-muscle whole-body model (MS-Emulator, arXiv 2603.29332).
- GPU-batched simulators, including MuJoCo Warp, show run-to-run and inter-environment variability under fixed seeds, quantified with Wasserstein-1 (GPUSimBench, arXiv 2607.13059).
- A CPU-Gymnasium/mjlab cross-backend contract with frozen-rollout parity tests for MyoSuite tasks (MyoSuite 3 ms3 branch, PR #406, unreleased).
- Bitwise-deterministic MJWarp stepping via sorted contacts, stable constraint rows and deterministic reductions (community PRs #1422/#1533; maintainer PR #1687; all open).
- Ensemble-based statistical consistency testing as a replacement for bit-for-bit reproducibility after ports (Baker et al. 2015; Milroy et al. 2018; Rosinski and Williamson 1997).
- Massively parallel single-GPU PPO for legged locomotion in minutes (Rudin et al., CoRL 2021).

### Open questions this programme can attack

- No published state-level or distributional parity test between CPU MuJoCo and MuJoCo Warp for a contact-rich, muscle-driven leg (myolegs26 or the 80-muscle MyoLeg), with or without an attached exoskeleton.
- No ensemble-consistency protocol adapted to gait: choice of summary statistics (stride time and length, GRF peaks, joint-angle and activation profiles, metabolic proxies), perturbation-ensemble design and false-positive calibration for CPU-versus-GPU physics.
- No test that CPU-trained SMAT policies (arXiv 2603.07618/2608.00715) behave equivalently on MJWarp, or that MJWarp-trained SMAT policies survive CPU evaluation, at the distribution level.
- The contact and parity effect of disabling MULTICCD (needed to load mesh-margin models on MJWarp 3.14.0) is unmeasured; the CPU reference must use the same flag.
- Deterministic-mode coverage of tendon and muscle paths in MJWarp, and its throughput cost on muscle models, are unknown (PR #1533 still lists tendon lengths and actuator moments as order-sensitive).
- No physics / environment-layer / learner throughput breakdown for muscle-plus-exoskeleton training on a 32 GB consumer Blackwell GPU; UniExo reports one aggregate number on a 96 GB card.
- Float32 (GPU) versus float64 (CPU) effects on stiff muscle activation dynamics and tendon wrapping are unquantified for gait.
- Sprint regime (80-muscle runner, high speed, impacts) has no GPU-backend parity evidence; MuscleMimic and MS-Emulator track running but report no state-level backend comparison.


---

## 5. PPO and the on-policy details that move results

**What this literature tells the programme**

- Transition counting is almost certainly per environment. PPO's Algorithm 1 requires minibatch <= N*T, and SB3 and CleanRL both define n_steps per env. A 16,384 minibatch cannot fit an aggregate 2,048-step rollout. Per-env gives 65,536 samples per update, 4 minibatches and up to 80 gradient steps per update before target-KL stopping.
- Picking a codebase silently picks SMAT's unspecified flags. SB3 (MyoAssist's base): no observation or reward normalisation, no value clipping, bootstraps timeouts, stops all epochs when a minibatch's approx-KL exceeds 1.5x target. CleanRL: normalises observations (clipped to ±10) and rewards, clips value loss, treats truncation as terminal, checks KL once per epoch at 1x target. Hundal et al. 2025 show such differences can flip conclusions.
- Code evidence from MyoAssist HEAD b1baf69 (2026-08-25; SMAT's own code is not public): SB3 PPO subclass with SubprocVecEnv and no running observation normalisation. Actors use a tanh-bounded mean and one state-independent log_std vector spanning all human and exo action dims. log_std_init is 0.0 in the tutorial JSON but -2.0 in the dataclass default (initial std 1.0 vs 0.14).
- 'Freezing an actor' is under-defined. With one log_std vector shared across both actors, freezing the human network does not freeze its log-std entries unless they are masked. Under SB3's latent-entropy bonus the entropy gradient pushes every log-std up at a constant rate, so a frozen actor's exploration noise can keep growing. Specify, and log, per-actor log_std at every stage.
- Expected effect sizes for the sweep. Observation normalisation was crucial on 4 of 5 MuJoCo tasks. A 100x-smaller last policy layer gave +66% on Humanoid, and tanh vs clip +30% on HalfCheetah. Value normalisation was crucial on 2 of 5 tasks and hurt on 1 (Andrychowicz). Clipped-Gaussian muscle policies sat within 5% of a bound for 89% of actions (He 2026). State-dependent vs state-independent std showed no clear effect.
- Honest comparison protocol. Use at least 10 seeds per arm, or 20 for the default-config pilot that sizes power. Report IQM of the final evaluation window with 95% percentile-bootstrap CIs plus min-max IPR-90 spread, compared at equal environment steps. Re-evaluate sweep winners on fresh seeds and correct for the number of arms.
- Equal budgets: fix total environment steps per arm. If an arm changes samples per update, keep minibatch size and learning rate fixed and vary optimisation steps (Beukman 2026). Report wall-clock separately, since rankings can change under wall-clock rather than sample budgets (Hamed et al. 2026, arXiv 2607.17326, verified, not selected).
- Checkpoint selection: max-over-training protocols are not comparable with final-performance results, and on Atari 100k the gap exceeded real algorithm differences (Agarwal). Picking the best of many checkpoints or configs inflates scores (Patterson's maximisation bias). Fix the rule before sweeping, e.g. the mean of the last K evaluations with deterministic and stochastic policies both logged.

### Must-read

- **Where Entropy Is Measured Matters: Policy Geometry in Bounded Continuous-Control PPO** 🆕 — He, Zhou, Wang, Xue, Fei. arXiv preprint (Aug 2026). arXiv:2608.24488 · [link](https://arxiv.org/abs/2608.24488)
  - *Idea.* In an 80-muscle MyoLeg task using SB3 PPO (entropy coefficient 1e-3), a clipped Gaussian put 89% of muscle commands within 5% of a bound and 82% of means outside [0,1]. With tanh policies, executed-action entropy H(a) cut near-bound occupancy from 71% (latent H(u)) to 19%.
  - *Take from it.* Log each actor's near-bound occupancy (|a-bound|<0.05) and the fraction of means outside bounds. Sweep entropy space {latent H(u) (SB3 default), none, executed H(a)} at SMAT's 0.001/0.003 coefficients.
  - *Left untested for this programme.* Three seeds per condition, one MyoLeg model plus Dog-Stand. More interior actions did not raise return. No exoskeleton co-adaptation, Beta policies, or gait/metabolic outcomes.
  - *On our server.* Directly reproducible in MyoAssist/SB3: changing the entropy space is a few lines in the loss, and occupancy logging costs nothing.
  - *Code and assets.* paper promises an archival package (MyoLeg/SB3 and Dog/CleanRL code, hashed checkpoints); no public URL found 2026-09-23
  - *Also relevant to:* physiology_grounded_control
- **Empirical Design in Reinforcement Learning** — Patterson, Neumann, White, White. JMLR 2024. arXiv:2304.01315 · [link](https://arxiv.org/abs/2304.01315)
  - *Idea.* Practical guide to RL experiments: performance measures, tolerance vs confidence intervals, number of runs, hypothesis tests, and maximisation bias in hyperparameter selection. Long-tailed run distributions needed about 20-30 runs, and maximising over configurations inflates reported performance.
  - *Take from it.* Use their two-stage workflow: sweep on tuning seeds, then re-run chosen configs on fresh seeds and report only those (bootstrapped variant if affordable). Flag winners at sweep-range edges. Report tolerance intervals.
  - *Left untested for this programme.* Worked examples are small classic-control and DQN tasks. No compute recipe for expensive 100M-step runs, staged curricula or multi-agent co-adaptation.
  - *On our server.* Paper only. The protocol costs extra seeds, not new code.
  - *Code and assets.* no code link in the arXiv record
  - *Also relevant to:* reproducibility_methods
- **The 37 Implementation Details of Proximal Policy Optimization** — Huang, Dossa, Raffin, Kanervisto, Wang. ICLR Blog Track 2022. [link](https://iclr-blog-track.github.io/2022/03/25/ppo-implementation-details/) · [code](https://github.com/vwxyzjn/ppo-implementation-details)
  - *Idea.* Line-by-line audit of openai/baselines PPO listing 37 details. Continuous-control defaults: state-independent log-std initialised at 0, actions clipped for the env but stored unclipped, running observation normalisation clipped to ±10, reward scaling, value-loss clipping, truncation not bootstrapped.
  - *Take from it.* Use as the checklist for every unspecified SMAT flag. Record whether obs/reward normalisation, value clipping and truncation bootstrapping are on (SB3 and CleanRL defaults differ). Always log approx-KL and clipfrac.
  - *Left untested for this programme.* Documents defaults rather than measuring their effects. Nothing on multi-agent critics or bounded [0,1] muscle actions, and no effect sizes for most continuous-control details.
  - *On our server.* Free to read. CleanRL's single-file PPO is a readable base for a two-actor, shared-critic variant.
  - *Code and assets.* public (last push 2024-03); the reference CleanRL (github.com/vwxyzjn/cleanrl; JMLR 23(274) 2022, arXiv 2111.08819) is active, last push 2026-04
- **The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games** — Yu, Velu, Vinitsky, Gao, Wang, Bayen, Wu. NeurIPS 2022 Datasets and Benchmarks. arXiv:2103.01955 · doi:10.52202/068431-1787 · [link](https://arxiv.org/abs/2103.01955) · [code](https://github.com/marlbenchmark/on-policy)
  - *Idea.* Ablates PPO factors in cooperative multi-agent games (MPE, SMAC, GRF, Hanabi). Value-target normalisation never hurt and often helped. Critic inputs that combine global and agent-specific features won. Fewer epochs, no minibatch splitting, clip below 0.2 and large batches worked best.
  - *Take from it.* Adopt running value-target normalisation in the shared critic. Give the critic global state plus agent-specific features. Sweep epochs {5,10,20} and minibatches {1,4}: SMAT's 20 epochs x 4 minibatches exceeds MAPPO's advice.
  - *Left untested for this programme.* Discrete cooperative games with homogeneous agents. No continuous musculoskeletal control, heterogeneous human and device actors, staged freezing, or target-KL early stopping interacting with epoch count.
  - *On our server.* Every factor is a flag. The epoch/minibatch sweep costs about 6 arms x seeds of CPU time on the EPYC.
  - *Code and assets.* public, MIT, last push 2024-07
  - *Also relevant to:* marl_shared_critic_partners
- **Deep Reinforcement Learning at the Edge of the Statistical Precipice** — Agarwal, Schwarzer, Castro, Courville, Bellemare. NeurIPS 2021 (Outstanding Paper). arXiv:2108.13264 · [link](https://arxiv.org/abs/2108.13264) · [code](https://github.com/google-research/rliable)
  - *Idea.* With 3-10 runs, point estimates mislead. Report stratified-bootstrap interval estimates, IQM instead of mean or median, performance profiles and probability of improvement. Percentile CIs hold from about 10 runs. Max-over-training protocols are not comparable with final-performance results.
  - *Take from it.* Run at least 10 seeds per sweep arm. Report IQM of final-window return with 95% percentile-bootstrap CIs and probability of improvement over the SMAT-default arm. Never mix max-checkpoint and final-checkpoint numbers.
  - *Left untested for this programme.* Validated mainly on Atari 100k and multi-task aggregates. Single-task SMAT comparisons lose the stratification benefit. Staged training and correlated evaluation episodes within a run are not treated.
  - *On our server.* pip install rliable; each analysis takes seconds of CPU.
  - *Code and assets.* public, Apache-2.0, archived read-only since 2024; still pip-installable
  - *Also relevant to:* reproducibility_methods
- **What Matters In On-Policy Reinforcement Learning? A Large-Scale Empirical Study** — Andrychowicz, Raichuk, Stańczyk, Orsini et al.. ICLR 2021 (published there as 'What Matters for On-Policy Deep Actor-Critic Methods? A Large-Scale Study'). arXiv:2006.05990 · [link](https://arxiv.org/abs/2006.05990)
  - *Idea.* Trains over 250,000 agents on five MuJoCo tasks, varying more than 50 on-policy choices with 3 seeds each. Observation normalisation, initial action std, last-layer scale, value normalisation, discount and transitions per iteration matter most; std parameterisation and advantage normalisation barely matter.
  - *Take from it.* Make observation normalisation the baseline. Sweep initial std {0.5, 1.0} with a 100x-smaller last policy layer, and tanh vs clip. Test value normalisation per task. Keep advantage normalisation. Skip state-dependent std.
  - *Left untested for this programme.* Single-agent MuJoCo, 1-2M steps, 3 seeds per configuration. Tanh vs clip was tested without an entropy bonus. No [0,1] muscle actuators, shared multi-agent critic, staged training or actor freezing.
  - *On our server.* Paper only. Each recommendation maps to an SB3 or CleanRL flag; one ablation arm costs about one SMAT stage per seed.
  - *Code and assets.* no code link in the arXiv record or paper text

### Should-read

- **Performance Variation in Deep Reinforcement Learning** 🆕 — Tanaka, Mahmood. arXiv preprint (Jun 2026). arXiv:2606.06746 · [link](https://arxiv.org/abs/2606.06746) · [code](https://github.com/WINUprj/eval-perf-variation)
  - *Idea.* Argues that confidence intervals on the mean hide run-to-run variation. Proposes min-max IPR-90 (normalised 5th-95th percentile range) and run-wise percentile plots, using 100 runs per task on 59 MuJoCo/DMC tasks. PPO varied more than SAC, and LayerNorm narrowed PPO's variation.
  - *Take from it.* Report min-max IPR-90 of final return for each SMAT arm next to IQM CIs. When means tie, prefer the arm with lower spread. Test LayerNorm in actors and critic as a variance-reduction arm.
  - *Left untested for this programme.* Single-agent, no parallel environments, 10M-step PPO. The 100 runs per task are unaffordable for 100M-step SMAT stages. No staged or multi-agent training.
  - *On our server.* The statistic is trivial to compute, but reliable 5th and 95th percentiles need many seeds (the paper used 100).
  - *Code and assets.* public, last push 2026-08-04
- **Preventing Learning Stagnation in PPO by Scaling to 1 Million Parallel Environments** — Beukman, Khetarpal, Zheng, Dabney, Foerster, Dennis, Lyle. RLC 2026 (accepted); arXiv v1 Mar 2026, v2 Jul 2026. arXiv:2603.06009 · [link](https://arxiv.org/abs/2603.06009)
  - *Idea.* Models PPO's outer loop as noisy stochastic optimisation. Plateaus arise when the policy step size (set by regularisation strength and epochs) is too large for the gradient noise (set by samples per update). Tuning Adam's learning rate cannot fix this, but more parallel samples can.
  - *Take from it.* Treat per-env vs aggregate counting as a 32x change in samples per update. When scaling samples, keep minibatch size and learning rate fixed and add optimisation steps. Sweep epochs {5,10,20} jointly with rollout size.
  - *Left untested for this programme.* Evidence comes from JAX 2D physics (Kinetix, procedural locomotion) and IsaacGym dexterous-hand tasks. No musculoskeletal tasks, multi-agent critics, or CPU-bound 32-env regimes like SMAT.
  - *On our server.* The principle applies at 32-64 envs. Million-env results need GPU simulation, which MyoAssist lacks.
  - *Code and assets.* none found (paper text and first author's GitHub checked 2026-09-23)
- **On the Mistaken Assumption of Interchangeable Deep Reinforcement Learning Implementations** — Hundal, Xiao, Cao, Dong, Rigger. ICSE 2025 (IEEE/ACM 47th Int. Conf. on Software Engineering). arXiv:2503.22575 · doi:10.1109/ICSE55347.2025.00222 · [link](https://arxiv.org/abs/2503.22575) · [code](https://doi.org/10.5281/zenodo.14249024)
  - *Idea.* Differential testing of five PPO implementations on 56 Atari games with matched hyperparameters: three reached superhuman scores in about 50% of trials, two in under 15%. Code-level inconsistencies, including timeout handling and value clipping, were implicated, and interchanging implementations flipped a replicated study's conclusion.
  - *Take from it.* Pin one PPO codebase and version for all SMAT arms. Never compare runs across libraries. When porting, diff timeout bootstrapping, value clipping and KL-stopping semantics against SB3 first.
  - *Left untested for this programme.* Discrete Atari only. No continuous or bounded actions, no multi-agent critics, and no measure of which single inconsistency drives continuous-control gaps.
  - *On our server.* A differential check is cheap: two codebases x 10 seeds on one short SMAT stage.
  - *Code and assets.* archived artifact on Zenodo (link from paper)
- **A Method for Evaluating Hyperparameter Sensitivity in Reinforcement Learning** — Adkins, Bowling, White. NeurIPS 2024. arXiv:2412.07165 · [link](https://arxiv.org/abs/2412.07165) · [code](https://github.com/jadkins99/hyperparameter_sensitivity)
  - *Idea.* Defines hyperparameter sensitivity across a set of environments and applies it to PPO normalisation variants over 4.3M runs on Brax MuJoCo. Advantage normalisations raised tuned performance but also sensitivity. Symlog value targets lowered performance, and observation normalisation may slightly reduce sensitivity.
  - *Take from it.* When sweeping observation, value and advantage normalisation, re-tune lr in each arm (at least {3e-5, 5e-5, 1e-4}), since a fixed-lr comparison can misattribute gains. Keep per-minibatch advantage normalisation on.
  - *Left untested for this programme.* Single-agent Brax tasks on short budgets. Running value-target normalisation (PopArt-style), bounded muscle actions and multi-agent shared critics were not included.
  - *On our server.* The method is analysis only. Applying it means a small lr grid per arm, multiplying runs by 3-5.
  - *Code and assets.* public, last push 2024-11
- **Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO** — Engstrom, Ilyas, Santurkar, Tsipras, Janoos, Rudolph, Madry. ICLR 2020. arXiv:2005.12729 · [link](https://arxiv.org/abs/2005.12729) · [code](https://github.com/MadryLab/implementation-matters)
  - *Idea.* Code-level optimisations in reference PPO (value clipping, reward scaling, orthogonal init, Adam annealing) explain most of PPO's gain over TRPO. Reward normalisation, annealing and initialisation significantly shifted Humanoid and Walker2d reward. Clipping alone did not keep probability ratios inside the trust region.
  - *Take from it.* Treat reward scaling, orthogonal init and lr annealing as sweep factors, not constants. Log the max probability ratio and KL per update to confirm clip 0.15 and target-KL 0.01 really bound policy change.
  - *Left untested for this programme.* Ablation grid on two MuJoCo tasks, 5 seeds, 2019-era baselines. No bounded muscle actions, multi-agent critics, KL early stopping or observation-normalisation ablation in the main grid.
  - *On our server.* The ablation grid is cheap to mirror with SB3 flags on short runs.
  - *Code and assets.* public, MIT, last push 2024-07
- **How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement Learning Experiments** — Colas, Sigaud, Oudeyer. arXiv preprint (tutorial), 2018. arXiv:1806.08295 · [link](https://arxiv.org/abs/1806.08295) · [code](https://github.com/flowersteam/rl-difference-testing)
  - *Idea.* Tutorial linking seed count to type-I and type-II errors for Welch's t-test and bootstrap tests. Two runs of the identical DDPG algorithm with 5 seeds each were declared significantly different. Bootstrap tests need at least 20 samples, and power analysis underestimates the seeds required.
  - *Take from it.* Run a pilot of at least 20 seeds of the SMAT-default config to estimate run-to-run SD. Size each comparison by power analysis (Welch's t-test, alpha<=0.05, corrected for the number of arms) and round N up.
  - *Left untested for this programme.* Single-task HalfCheetah examples. No guidance for many-arm sweeps sharing a baseline, sequential testing, or staged training where early stages gate later ones.
  - *On our server.* The formulas and code are trivial; the 20-seed pilot is the real cost.
  - *Code and assets.* public, unmaintained since 2018
- **Improving Stochastic Policy Gradients in Continuous Control with Deep Reinforcement Learning using the Beta Distribution** — Chou, Maturana, Scherer. ICML 2017 (PMLR 70:834-843). [link](https://proceedings.mlr.press/v70/chou17a.html)
  - *Idea.* Clipping an infinite-support Gaussian to bounded actions biases the policy gradient. A Beta policy has finite support, is bias-free, and converged faster with TRPO and ACER on Gym/MuJoCo continuous-control tasks.
  - *Take from it.* Add a Beta-policy arm for the 26 muscle excitations ([0,1] support) and a rescaled Beta for exo torques. Compare it with clipped and tanh Gaussians at equal steps and seeds.
  - *Left untested for this programme.* Tested with TRPO and ACER, not PPO with clipping and target-KL. No high-dimensional muscle actuation. He et al. 2026 did not test Beta, so its boundary geometry is untested.
  - *On our server.* SB3 has no Beta distribution. Needs a custom Distribution subclass; torch.distributions.Beta covers sampling and log-prob.
  - *Code and assets.* none linked on the PMLR page
- **Learning values across many orders of magnitude** — van Hasselt, Guez, Hessel, Mnih, Silver. NeurIPS 2016. arXiv:1602.07714 · [link](https://arxiv.org/abs/1602.07714)
  - *Idea.* PopArt adaptively normalises learning targets with running mean and scale (ART) and rescales the output layer to preserve unnormalised predictions (POP). Value estimates then survive abrupt changes in return magnitude without reward clipping.
  - *Take from it.* For the shared critic across SMAT's four stages, sweep {no value normalisation, running target normalisation, PopArt}. PopArt should matter most at stage switches, where reward terms and return scale jump.
  - *Left untested for this programme.* Motivated by and shown on value-based Atari learning. Never tested with PPO in staged multi-agent continuous control or with actor freezing.
  - *On our server.* About a critic-head's worth of code; SB3 has no built-in PopArt or value-target normalisation.
  - *Code and assets.* no official code

### Reference

- **Stable-Baselines3: Reliable Reinforcement Learning Implementations** — Raffin, Hill, Gleave, Kanervisto, Ernestus, Dormann. JMLR 22(268):1-8, 2021. [link](https://jmlr.org/papers/v22/20-1364.html) · [code](https://github.com/DLR-RM/stable-baselines3)
  - *Idea.* Tested PyTorch RL library that MyoAssist's rl_train subclasses. In current PPO source, n_steps is per environment, sampled Gaussian actions are clipped only for the env, timeouts bootstrap, and target_kl stops all remaining epochs once a minibatch's approx-KL exceeds 1.5x target.
  - *Take from it.* Read SMAT's '2048 steps' as per env: 65,536 samples per update in 4 minibatches of 16,384. SB3 defaults: no VecNormalize, log_std_init 0, clip_range_vf None, advantage normalisation on.
  - *Left untested for this programme.* Library paper with no ablations. Its defaults (no observation or reward normalisation) differ from CleanRL and baselines and were not benchmarked for musculoskeletal or multi-agent PPO.
  - *On our server.* Already a MyoAssist dependency, so there is no porting cost.
  - *Code and assets.* public, MIT, active (last push 2026-09-09, master 2.9.2a0); PPO source checked 2026-09-23
- **Proximal Policy Optimization Algorithms** — Schulman, Wolski, Dhariwal, Radford, Klimov. arXiv preprint, 2017. arXiv:1707.06347 · [link](https://arxiv.org/abs/1707.06347) · [code](https://github.com/openai/baselines)
  - *Idea.* Defines the clipped surrogate, optimised for K epochs on minibatches drawn from N actors x T timesteps. MuJoCo defaults: T=2048 per actor, 10 epochs, minibatch 64, Adam 3e-4, gamma 0.99, lambda 0.95, learned std, no entropy bonus, 3 seeds.
  - *Take from it.* Algorithm 1 requires minibatch M <= N*T. SMAT's 16,384 minibatch only fits 2,048 steps per env (N*T = 65,536), so adopt per-env counting as the primary reading.
  - *Left untested for this programme.* No ablation of normalisation, action bounding, value clipping or seed count. One million steps with 3 seeds per task.
  - *On our server.* Reference only.
  - *Code and assets.* public (ppo2), MIT, effectively unmaintained (last push 2024-08)

### Already claimed by published work (cite it, compare against it, do not headline it)

- Observation normalisation, initial action std and last-layer initialisation are among the most influential PPO continuous-control choices (Andrychowicz et al. 2021).
- Code-level optimisations, not the clipped objective, explain most of PPO's advantage over TRPO, and clipping alone does not enforce the trust region (Engstrom et al. 2020).
- PPO implementations with matched hyperparameters are not interchangeable and can flip study conclusions (Hundal et al. 2025).
- Clipped-Gaussian PPO muscle policies in MyoLeg concentrate at action bounds, and entropy measurement space (latent vs executed) changes mean-variance geometry (He et al. 2026).
- Value normalisation and critic input design strongly affect multi-agent PPO with a centralised critic; fewer epochs and less minibatching help (Yu et al. 2022).
- Point estimates from 3-10 runs are unreliable; IQM with stratified bootstrap CIs and performance profiles are the recommended remedy (Agarwal et al. 2021).
- Maximising over hyperparameter configurations or checkpoints inflates reported performance (Patterson et al. 2024; Agarwal et al. 2021).
- PPO plateaus can come from too few samples per update relative to the policy step size, and more parallel environments fix them (Beukman et al. 2026).
- Normalisation variants that raise tuned PPO performance also raise hyperparameter sensitivity (Adkins et al. 2024).
- Beta policies remove the bias of clipped Gaussians on bounded actions (Chou et al. 2017).
- Uncertainty in the mean understates run-to-run variation; LayerNorm narrows PPO variation (Tanaka & Mahmood 2026).

### Open questions this programme can attack

- No study measures these PPO implementation choices in human-exoskeleton co-adaptation with two heterogeneous actors and a shared critic.
- How actor freezing and staged curricula interact with log-std, entropy bonus and shared-critic value targets in PPO is unstudied.
- Beta vs clipped vs tanh Gaussian has not been compared for high-dimensional muscle control under PPO with an entropy bonus (He et al. 2026 tested Gaussian variants only).
- There are no published run-to-run variance estimates for 100M-step musculoskeletal PPO to size seed budgets; a pilot is required.
- In the studies reviewed here, target-KL early-stopping semantics (per-minibatch 1.5x in SB3 vs per-epoch 1x in CleanRL) were not ablated at high epoch counts like SMAT's 20.
- Whether observation-normalisation statistics should be frozen, reset or shared across stages and between the two actors is unaddressed.
- Checkpoint-selection rules based on gait or assistance metrics rather than return have not been examined for bias.


---

## 6. Two agents, shared critics, schedules and partner transfer

**What this literature tells the programme**

- Treat the actor-update schedule as a continuous knob, not a staged-vs-simultaneous switch. Multi-timescale learning (Nekoei et al., 2302.02792) contains simultaneous updates (equal rates), sequential updates (slow rate 0, i.e. SMAT Stage 3) and fixed two-timescale learning as special cases, and HAPPO (2109.11251) adds a principled sequential order. Sweeping these at fixed reward weights and torque scale is the cleanest way to separate schedule from curricula.
- A staged-vs-simultaneous difference may come from equilibrium selection or initialisation rather than better optimisation. ACPO (2606.30072) shows MAPPO-style and HAPPO-style updates can settle in suboptimal Nash equilibria depending on initialisation. Chasnov et al. (Sci Rep 2025) found that a machine's adaptation rule and rate moved real human-machine pairs between Nash and Stackelberg outcomes, and Su & Guo (2503.07319) formalise multiple equilibria. UniExo (2609.19690, the SMAT authors) replaced the frozen-human RL stage with supervised exo initialisation from the human's hip moments followed by joint shared-critic PPO. 'Simultaneous from the Stage-2 human' and 'supervised exo initialisation + simultaneous' are therefore mandatory controls.
- Critic design is an unspecified axis, not a detail. MAPPO lists value normalisation and critic input among five factors critical to PPO performance. Lyu et al. (JAIR 2023) show critic centralisation is not strictly beneficial and that state-based critics can add bias and variance for partially observing actors. SMAT's exo actor sees only an 18-D hip window, so compare critic inputs before attributing gains to 'sharing'.
- PPO settings interact with partner non-stationarity. MAPPO recommends at most 10 epochs on hard tasks, no minibatch splitting and a clip below 0.2, while SMAT uses 20 epochs, 4 minibatches and a clip of 0.15. IPPO's (2011.09533) strength was linked to robustness to some non-stationarity, and trust-region bounds for decentralised PPO (Sun et al., AAMAS 2023, 2202.00082) justify bounding per-agent ratios by agent count. Hold these equal across arms or sweep them explicitly.
- Co-trained partners overfit to each other, and the co-training score hides it. Self-play agents failed with a held-out proxy human (Carroll 2019), and independently trained agents fail in cross-play without symmetry-aware training (Other-Play 2020). Assistax found a coordination gap on 625 withheld humanoids that narrows only when train and test partners overlap. In simulation SMAT evaluates its exo only with its co-trained human; its offline replay on recorded gait tests input generalisation, not closed-loop partner transfer.
- Vary held-out humans along several axes, not only seeds. The axes are implementation details (inter-seed cross-play was an adequate proxy for Other-Play in 2608.03644, with 8 or more seeds per implementation), reward shaping and preferences (Assistax preferences; ZSC with diverse reward shapings, 2604.25076) and impairments (Clegg et al. 1909.06682 co-trained human and robot dressing policies per impairment; the SMAT authors' unilateral-weakness models, 2602.18862). Each independent human costs a Stage 1-2 run (about 480M transitions at SMAT scale), so the partner-transfer test depends on GPU physics or validated proxy budgets.
- Treating a human and a device as two learning agents with a shared or centralised critic is an occupied framing. Wu et al. (NeurIPS 2022, prosthesis, one critic on a shared cost), Sun et al. (MBEC 2026, hip exo, MATD3 CTDE) and SMAT/UniExo (shared-critic PPO) already use it. Publishable novelty has to come from mechanism isolation at matched budget and from partner transfer, not from the two-agent formulation.

### Must-read

- **Assistax: A Multi-Agent Hardware-Accelerated Reinforcement Learning Benchmark for Assistive Robotics** — Hinckeldey, Fosong, Rubavicius, Miller, McInroe, Zhang, Wollstadt, Albrecht, Ramamoorthy. RLC 2026 (arXiv v1 July 2025; v3 July 2026). arXiv:2507.21638 · [link](https://arxiv.org/abs/2507.21638) · [code](https://github.com/assistive-autonomy/assistax)
  - *Idea.* JAX/MuJoCo-MJX assistive tasks where a torque-controlled robot and a simulated humanoid are co-trained with MARL (IPPO, MAPPO, MASAC; no parameter sharing), plus an ad hoc teamwork pipeline: 630 pre-trained humanoids per task varying conventions, preferences and disabilities.
  - *Take from it.* Copy its protocol: train the robot with few partners (5), test on withheld ones (625), release the partner zoo. Its coordination gap narrows when train and test partners overlap, so report overlap.
  - *Left untested for this programme.* Muscle-driven humans and locomotion (its Brax humanoid acts through a few torque-controlled arm joints) and staged co-training; its held-out evaluation trains robots against frozen pre-trained humanoids, not co-adapted ones.
  - *On our server.* One GPU: IPPO 40M steps in about 20 min (1024 envs, A100). Partner zoo on Hugging Face; a cheap sandbox to debug cross-play tooling.
  - *Code and assets.* official
- **Human adaptation to adaptive machines converges to game-theoretic equilibria** — Chasnov, Ratliff, Burden. Scientific Reports 15 (2025); arXiv 2023. arXiv:2305.01124 · doi:10.1038/s41598-025-12998-1 · [link](https://arxiv.org/abs/2305.01124) · [code](https://github.com/dynams/web)
  - *Idea.* Three human-subject experiments (n=20 each) in quadratic-cost games: the machine's adaptation rule and rate selected the co-adaptation outcome, Nash at slow gradient-descent rates, human-led Stackelberg at fast rates, and conjectural or machine-optimal equilibria with policy-space learners.
  - *Take from it.* Frame staged vs simultaneous training as equilibrium selection. Changing rates in simultaneous gradient play does not move stationary points (their note), so test whether SMAT staging changes the endpoint or only the path.
  - *Left untested for this programme.* Deep RL learners on both sides, physical coupling and locomotion; humans chose scalar actions in quadratic-cost games through a browser, with general-sum costs rather than a shared assistance reward.
  - *On our server.* No compute; motivates a cheap test: vary the exo-to-human learning-rate ratio in simultaneous training and check whether the endpoint moves.
  - *Code and assets.* official
  - *Also relevant to:* hilo_coadaptation_theory
- **Dealing With Non-stationarity in Decentralized Cooperative Multi-Agent Deep Reinforcement Learning via Multi-Timescale Learning** — Nekoei, Badrinaaraayanan, Sinha, Amini, Rajendran, Mahajan, Chandar. CoLLAs 2023 (PMLR 232). arXiv:2302.02792 · [link](https://arxiv.org/abs/2302.02792)
  - *Idea.* Independent (simultaneous) learning need not converge; sequential learning, where one agent updates while the others are frozen, converges to an agent-by-agent optimum but is slow. Multi-timescale learning rotates one fast learner while others learn slowly; MTPPO matches or beats IPPO on 12 EPyMARL tasks.
  - *Take from it.* Its parameterisation spans the schedule space: slow rate 0 is SMAT Stage 3, equal rates is Stage 4. Sweep rate ratio and switching period at fixed reward and torque to isolate schedule from curricula.
  - *Left untested for this programme.* Continuous musculoskeletal control, agents of very unequal size and plasticity, a shared critic (it uses per-agent critics), and schedules coupled to curricula; only discrete-action EPyMARL benchmarks were tested.
  - *On our server.* Two learning rates and a switching period: a few config lines on the two-actor PPO. Cheap to sweep at proxy budgets, 5+ seeds.
  - *Code and assets.* none-found
- **On Centralized Critics in Multi-Agent Reinforcement Learning** — Lyu, Baisero, Xiao, Daley, Amato. Journal of Artificial Intelligence Research 77 (2023). arXiv:2408.14597 · doi:10.1613/jair.1.14386 · [link](https://arxiv.org/abs/2408.14597) · [code](https://github.com/lyu-xg/on-centralized-critics-in-marl)
  - *Idea.* Formal and empirical analysis of centralised vs decentralised critics in CTDE actor-critic: critic centralisation is not strictly beneficial, and state-based critics can introduce bias and variance relative to history-based critics when actors observe only part of the state.
  - *Take from it.* Treat critic input as a sweep axis: SMAT's exo actor sees only an 18-D hip window and the critic inputs are unspecified. Compare state, history and state+history critics before crediting the 'shared critic'.
  - *Left untested for this programme.* Physically coupled continuous control where one critic serves two actors with very different observations and action sizes, and effects on partner transfer; experiments use small cooperative benchmarks (Dec-Tiger, particle, SMAC).
  - *On our server.* Critic variants change only the critic network input; each is one extra arm at proxy budget. Author code shows the input constructions.
  - *Code and assets.* official
- **Trust Region Policy Optimisation in Multi-Agent Reinforcement Learning** — Kuba, Chen, Wen, Wen, Sun, Wang, Yang. ICLR 2022. arXiv:2109.11251 · [link](https://arxiv.org/abs/2109.11251) · [code](https://github.com/cyanrain7/TRPO-in-MARL)
  - *Idea.* Multi-agent advantage decomposition lemma plus a sequential update scheme: agents update one at a time in a random permutation, each weighting its advantage by the already-updated agents' new/old policy ratios, giving monotonic joint improvement without parameter sharing (HATRPO, HAPPO).
  - *Take from it.* HAPPO is the principled sequential-schedule arm: fixed human-then-exo vs exo-then-human vs random order at equal budget. Its ratio-weighted advantage shows how a shared critic's advantage should change after the partner updates.
  - *Left untested for this programme.* Stage-length freezing (millions of steps), agents with very different action size and plasticity, and whether update order changes which joint equilibrium is reached; ACPO (2606.30072) argues alternating updates can stall at suboptimal Nash equilibria.
  - *On our server.* Two agents add one ratio product per minibatch; negligible cost. PKU-MARL/HARL (PyTorch) is the maintained implementation to port into the MyoAssist PPO loop.
  - *Code and assets.* official
- **"Other-Play" for Zero-Shot Coordination** — Hu, Lerer, Peysakhovich, Foerster. ICML 2020. arXiv:2003.02979 · [link](https://arxiv.org/abs/2003.02979) · [code](https://github.com/facebookresearch/hanabi_SAD)
  - *Idea.* Self-play converges on arbitrary conventions that fail with independently trained partners. Other-Play trains under random relabelling by known environment symmetries, yielding convention-free policies; evaluated by cross-play matrices of independently trained agents in Hanabi and preliminarily with humans.
  - *Take from it.* Adopt cross-play as the partner-transfer test: an exo-seed by human-seed matrix, off-diagonal vs diagonal benefit. Left-right mirror symmetry of gait is a candidate symmetry group for a bilateral hip exoskeleton.
  - *Left untested for this programme.* Continuous control with asymmetric roles (human vs device) and approximate rather than exact symmetries; whether physically coupled dynamics produce arbitrary conventions at all (e.g., exo torque timing tuned to one gait).
  - *On our server.* Evaluation-only once policies exist; the cost is training independent humans (about 480M transitions each at SMAT Stages 1-2 scale).
  - *Code and assets.* official

### Should-read

- **ACPO: Agent-Chained Policy Optimization for Multi-Agent Reinforcement Learning** 🆕 — Matsunaga, Na, Guntara, Sanner, Poupart, Lee, Kim. RLC 2026 (RLJ). arXiv:2606.30072 · [link](https://arxiv.org/abs/2606.30072)
  - *Idea.* Shows the joint policy gradient decomposes exactly into per-agent terms built from per-agent score functions and decentralised critics, so independent actor updates form one joint-gradient step. Argues MAPPO-style independent and HAPPO-style alternating updates can stall at suboptimal Nash equilibria.
  - *Take from it.* Its matrix-game example, where the equilibrium MAPPO or HAPPO reach depends on initialisation, suggests SMAT's pre-trained human may decide the outcome. Test staging against 'simultaneous from the Stage-2 human'.
  - *Left untested for this programme.* Two heterogeneous, physically coupled agents with musculoskeletal dynamics and staged curricula; evaluated on warehouse, SMACv2 and MA-MuJoCo, with gains growing with agent count, so the two-agent benefit may be small.
  - *On our server.* No code found; per-agent critics and chained updates for two agents are a moderate PyTorch change. Treat as an optional arm.
  - *Code and assets.* none-found
- **Human Machine Co-Adaptation Model and Its Convergence Analysis** 📚 — Su, Li, Guo, Duffield. arXiv preprint, 2025. arXiv:2503.07319 · [link](https://arxiv.org/abs/2503.07319)
  - *Idea.* Gives sufficient conditions under which cooperative adaptive MDPs (finite, factored human, robot and shared states) converge to a unique Nash equilibrium, and adjusts value evaluation and policy improvement to favour the best (minimal-cost) equilibrium when several exist; numerical examples only.
  - *Take from it.* Vocabulary and conditions for arguing why staged and simultaneous schedules could land on different joint policies; read with Chasnov et al. and ACPO when interpreting SMAT ablations.
  - *Left untested for this programme.* Function approximation, stochastic policy gradients, continuous control and any wearer; transition and reward matrices are assumed known (KB reading 06).
  - *On our server.* Theory only; no compute.
  - *Code and assets.* none-found
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/coadaptation-convergence-primary-reading-06.md`
  - *Also relevant to:* hilo_coadaptation_theory
- **Human Machine Co-adaption Interface via Cooperation Markov Decision Process System** 📚 — Guo, Cheng, Li, Li, Duffield, Su. arXiv preprint (final retitled version: Knowledge-Based Systems 291:111572, 2024, doi 10.1016/j.knosys.2024.111572), 2023. arXiv:2305.02058 · [link](https://arxiv.org/abs/2305.02058)
  - *Idea.* Models robot-assisted rehabilitation as a cooperative two-agent MDP (patient and robot) at a high abstraction layer and proposes procedures that gate each agent's policy improvement on instantaneous or accumulated value gains to curb co-adaptation non-stationarity; validated only on a numerical example.
  - *Take from it.* A value-gated switching rule (switch which actor learns when its improvement stalls) is a cheap adaptive-schedule arm to set beside fixed SMAT stage lengths.
  - *Left untested for this programme.* Function approximation, PPO, continuous musculoskeletal control and real wearers; it uses finite tabular MDPs with known models. The KBS version's large-scale result remains unverified (KB reading 05).
  - *On our server.* Scheduler logic only: track per-actor value improvement across PPO iterations and toggle learning flags; negligible compute.
  - *Code and assets.* none-found
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/coadaptation-rate-primary-reading-05.md`
  - *Also relevant to:* hilo_coadaptation_theory
- **Human-Robotic Prosthesis as Collaborating Agents for Symmetrical Walking** — Wu, Zhong, Wallace, Gao, Huang, Si. NeurIPS 2022. doi:10.52202/068431-1980 · [link](https://proceedings.neurips.cc/paper_files/paper/2022/hash/aed42bb2e45857928418e4fe23d8cbcb-Abstract-Conference.html)
  - *Idea.* Collaborative MARL for a human and a robotic knee prosthesis: separate human and robot actors with one critic learned on the shared cost (not local costs, since they are physically coupled), tuning phase-wise impedance in OpenSim walking; beats single-agent, tailored MADDPG and COMA baselines.
  - *Take from it.* Prior art for SMAT's core design (two actors, one critic on a shared cost, physical coupling). Its with/without-human-influence ablation is a template for isolating what the second learner contributes.
  - *Left untested for this programme.* Muscle-level human control, deep PPO, staged schedules and held-out users: networks have 6 hidden units, the robot sets 12 impedance parameters per gait cycle, and all evaluation is simulated with injected sensor noise.
  - *On our server.* Conceptual precedent; the tiny networks and OpenSim setup are not reusable. No code link found.
  - *Code and assets.* none-found
- **Collaborating with Humans without Human Data** — Strouse, McKee, Botvinick, Hughes, Everett. NeurIPS 2021. arXiv:2110.08176 · [link](https://arxiv.org/abs/2110.08176)
  - *Idea.* Fictitious Co-Play trains an agent as best response to a frozen population of self-play partners plus their past checkpoints, supplying skill and convention diversity; in Overcooked it beats self-play, population play and behaviour-cloning play with novel agents and humans.
  - *Take from it.* SMAT already produces checkpoints (Stage 1-2 humans at different skill levels, across seeds). Training the exo against that frozen population is the obvious remedy arm if cross-play shows poor transfer.
  - *Left untested for this programme.* Continuous physical coupling where partners differ in dynamics, not only conventions; whether early-checkpoint (unskilled) humans help or harm an assistive controller; joint fine-tuning after population training.
  - *On our server.* Checkpoints are free by-products; one exo run per population. Evaluation still needs held-out humans outside the population.
  - *Code and assets.* none-found
- **Is Independent Learning All You Need in the StarCraft Multi-Agent Challenge?** — de Witt, Gupta, Makoviichuk, Makoviychuk, Torr, Sun, Whiteson. arXiv preprint, 2020. arXiv:2011.09533 · [link](https://arxiv.org/abs/2011.09533) · [code](https://github.com/uoe-agents/epymarl)
  - *Idea.* Independent PPO, each agent learning only its own local value function, matches or beats state-of-the-art joint-learning methods on SMAC with little tuning; variant comparisons suggest its strength comes partly from robustness to some forms of environment non-stationarity.
  - *Take from it.* Include IPPO (separate human and exo critics, simultaneous updates) as the control arm: if the shared critic cannot beat it at matched transitions, the 'shared critic' is not the mechanism.
  - *Left untested for this programme.* Physically coupled heterogeneous agents with a shared assistance reward, muscle actuation, staged schedules and partner transfer; SMAC is a discrete-action game.
  - *On our server.* Cheapest arm: two critics instead of one, same rollouts. EPyMARL has a reference IPPO; port the logic, not the code.
  - *Code and assets.* third-party
- **On the Utility of Learning about Humans for Human-AI Coordination** — Carroll, Shah, Ho, Griffiths, Seshia, Abbeel, Dragan. NeurIPS 2019. arXiv:1910.05789 · [link](https://arxiv.org/abs/1910.05789) · [code](https://github.com/HumanCompatibleAI/human_aware_rl)
  - *Idea.* In Overcooked-AI, agents trained by self-play or population-based training coordinate well with themselves but poorly with a held-out proxy human (behaviour cloning on separate data); agents trained with a human model do better; a user study shows the same pattern, less strongly.
  - *Take from it.* Separate the training partner from the evaluation proxy: a human fitted to different data or trained independently is the minimum honest partner-transfer test for the exo.
  - *Left untested for this programme.* Continuous biomechanical coupling where the device changes the partner's dynamics, and partner models that adapt to the device (the behaviour-cloned proxy is non-adaptive).
  - *On our server.* For SMAT the proxy is an independently trained or data-imitating human, costing one Stage 1-2 run each.
  - *Code and assets.* official

### Already claimed by published work (cite it, compare against it, do not headline it)

- Human and assistive device as two cooperating RL agents with one critic on a shared cost in biomechanical simulation: Wu et al., NeurIPS 2022 (knee prosthesis, OpenSim, doi 10.52202/068431-1980). Human plus hip exoskeleton as heterogeneous MARL agents with a CTDE critic: Sun et al., Med Biol Eng Comput 2026 (doi 10.1007/s11517-026-03634-9). Staged or shared-critic PPO co-adaptation of a musculoskeletal human and a hip exoskeleton, with hardware results: SMAT (2603.07618, 2608.00715) and UniExo (2609.19690).
- Sequential one-agent-at-a-time updates converge where simultaneous independent updates may not, and multi-timescale PPO interpolates between them: Nekoei et al., CoLLAs 2023 (2302.02792). Sequential trust-region updates with a monotonic-improvement guarantee: HATRPO/HAPPO (2109.11251), HARL (2304.09870), A2PO (2302.06205).
- Alternating best-response and independent updates can converge to initialisation-dependent suboptimal Nash equilibria, with an exact decentralised joint-gradient fix: ACPO, RLC 2026 (2606.30072).
- Co-trained or self-play agents fail with held-out or independently trained partners, and partner-diversity training mitigates it: Carroll 2019 (1910.05789), Other-Play 2020 (2003.02979), FCP 2021 (2110.08176), MEP (2112.11701), HSP (2302.01605), COLE (2302.04831). Shown for assistive physical HRI with a withheld humanoid population: Assistax (2507.21638).
- Critic centralisation is not strictly beneficial, and state-based critics can be biased: Lyu et al., AAMAS 2021 (2102.04402) and JAIR 2023 (2408.14597).
- Cooperative co-adaptive MDPs with gated policy improvement and Nash-equilibrium convergence conditions for human-machine rehabilitation: Guo et al. 2023 / Knowledge-Based Systems 2024, Su et al. 2025 (2503.07319), and An et al. DAMMRL, IEEE TNNLS 2026 (doi 10.1109/tnnls.2026.3685832).
- A machine's adaptation rule and rate select Nash vs Stackelberg outcomes with real humans: Chasnov et al., Scientific Reports 2025 (2305.01124).
- A frozen pre-trained musculoskeletal human policy used as a fixed evaluator for co-optimising a device's structure and controller: Zuo et al. 2026 (2603.09218).

### Open questions this programme can attack

- No paper found tests partner transfer in human-device co-adaptation (SMAT, UniExo, MBEC 2026, Wu 2022). The open test is a cross-play matrix of exo seeds against independently trained humans (varying seeds, implementations, reward shapings and impairments). Score it as the benefit retained relative to a partner-specific best response, the BR-Prox idea of ZSC-Eval (2310.05208).
- No study separates the update schedule from the curricula in human-device co-adaptation. The open design crosses schedules {SMAT staging, simultaneous, simultaneous from the Stage-2 human, HAPPO order, multi-timescale ratio and switching period} with {reward curriculum on/off} x {torque curriculum on/off} at matched transitions. Each arm is cheap once throughput is solved.
- Shared critic vs MAPPO-style centralised critic vs IPPO vs ACPO-style decentralised critics has not been compared in a physically coupled, strongly asymmetric pair (26 muscles vs 2 torques, exo observing an 18-D window). Lyu et al.'s bias and variance analysis gives falsifiable predictions.
- Does staging change the endpoint or only the path? Restart simultaneous training from the staged endpoint and vice versa, and check whether each joint policy is a fixed point of the other schedule.
- Remedy side: does training the exo FCP-style against a frozen population of SMAT human checkpoints (across stages and seeds) buy held-out transfer without losing the co-trained partner's benefit?
- Prosthesis side: no 2023-2026 paper was found that trains a musculoskeletal human and a prosthesis controller as two deep-RL agents. Wu et al. 2022 used impedance parameters and 6-unit networks, and 2607.22858 (2026) replays recorded hip kinematics instead of modelling the human.


---

## 7. Motion imitation, rewards and reference data

**What this literature tells the programme**

- Every muscle-driven imitation pipeline found uses DeepMimic-style exponential kernels, but widths vary by orders of magnitude with error units: DeepMimic pose 2 / velocity 0.1 (summed, rad), Choi 2026 position 2 / velocity 0.05, KINESIS 200 on keypoint metres / 5 on velocities. SMAT's single exp(-8·err²) for both positions and velocities cannot be interpreted until err's units and summation are fixed (my inference).
- Kinematic tracking does not certify physiology: MuscleMimic reports joint-angle r = 0.90 but muscle-EMG r of only 0.2 to 0.6; Beyond Kinematics finds MuJoCo/MyoSim activations far from EMG (pooled r 0.11) versus Hyfydy (0.40); Liu 2026 shows motion-only imitation mis-times foot contact and prolongs stance. SMAT's metabolic and toe-off claims inherit these risks.
- Reference symmetry is a design choice: Choi 2026 mirrors its clip across the sagittal plane, and the MyoAssist digest notes segmented.npz builds the left leg by rolling the right 50%. Measure the reference's own left-right r and toe-off before training; UniExo's policy imitating AMASS walking spent only 53% of the cycle in stance, far from SMAT's ~58% toe-off target.
- Speed handling is under-documented: none of the papers read uses SMAT's reference-velocity scaling (target speed / reference pelvis speed). Chiu 2024 builds speed-conditioned references from Camargo's 28-speed ladder and finds a larger speed-reward share yields asymmetric gait; Camargo's 1.20/1.25/1.30 m/s trials allow a direct scaled-versus-recorded reference test.
- Licences split the field: kinetics-rich lab datasets are CC BY 4.0 or CC0 (Camargo, van der Zee, Scherpereel, Fukuchi 2017/2018, Schreiber 2019, AddBiomechanics), whereas the mocap libraries behind UniExo and LocoMuJoCo (LAFAN1; LocoMuJoCo default datasets, including a single-subject 1.25 m/s walk) are CC BY-NC-ND 4.0, and AMASS is installed separately under its own licence. Prefer CC BY/CC0 references for a shareable reconstruction.
- Open sprint data are scarce: Haralabidis 2021 (one sprinter, ~10 m/s single-stance clips, CC BY 4.0) and Dorn 2012 (one subject to 9.49 m/s, MIT) are the only near-maximal sets found; other running datasets stop at 4.5 to 5 m/s (Fukuchi 2017, Hamner & Delp 2013) and LAFAN1's two sprint takes are kinematics-only. Reference-free sprinting (Bolt, Lambda-Hold) validated against these sets is the practical Phase-2 route.
- Reference processing moves results too: MuscleMimic's Mocap-Body retargeting raised joint-angle and velocity errors versus GMR-Fit; UniExo took knee flexion directly from SMPL because IK produced a crouch; MuscleMimic found early-termination thresholds of 1 m or more converged higher than 0.25 to 0.5 m. Fix the processing pipeline before comparing references.

### Must-read

- **A comprehensive, open-source dataset of lower limb biomechanics in multiple conditions of stairs, ramps, and level-ground ambulation and transitions** — Camargo, Ramanathan, Flanagan, Young. J Biomech 119:110320; data on Mendeley (10.17632/fcgm3chfff, k9kvm5tn3f, jj3r5f9pnf), 2021. doi:10.1016/j.jbiomech.2021.110320 · [link](https://data.mendeley.com/datasets/fcgm3chfff)
  - *Idea.* 22 able-bodied adults; treadmill walking at 28 speeds (0.5 to 1.85 m/s in 0.05 m/s steps, seven trials) plus level ground, ramps and stairs. OpenSim IK and ID at 200 Hz, GRF, 11-muscle EMG, IMUs, goniometers and gait-cycle segmentation as MATLAB tables.
  - *Take from it.* Best-documented 1.25 m/s reference: the exact speed with GRF and OpenSim IK, 22 subjects for subject choice or averaging, and 1.20/1.30 m/s neighbours to test SMAT-style speed scaling against recorded gait.
  - *Left untested for this programme.* Speeds change within each treadmill trial, so steady 1.25 m/s windows must be cut using the conditions table; no running.
  - *On our server.* CC BY 4.0; 24.5 GB across three Mendeley parts; walking 0.5 to 1.85 m/s.
  - *Code and assets.* dataset; MATLAB scripts (STRIDES.m, RUN_OSIM.m) in scripts.zip
- **DeepMimic: Example-Guided Deep Reinforcement Learning of Physics-Based Character Skills** — Peng, Abbeel, Levine, van de Panne. ACM TOG 37(4) (SIGGRAPH 2018). arXiv:1804.02717 · doi:10.1145/3197517.3201311 · [link](https://arxiv.org/abs/1804.02717) · [code](https://github.com/xbpeng/DeepMimic)
  - *Idea.* Tracks one reference clip with weighted exponential-kernel rewards: pose exp(-2Σ‖Δq‖²), velocity exp(-0.1Σ‖Δq̇‖²), end-effector exp(-40Σ‖Δp‖²), centre of mass exp(-10‖Δp_c‖²), weights 0.65/0.1/0.15/0.1. A phase variable in the state, reference state initialization and early termination are critical.
  - *Take from it.* SMAT's unspecified phase handling maps onto DeepMimic's phase variable, RSI and early termination. Its pose and velocity kernels differ 20-fold (2 vs 0.1), unlike SMAT's shared exp(-8·err²); pin SMAT's error units before tuning.
  - *Left untested for this programme.* Torque-driven PD characters only: no muscles, no gait metrics such as symmetry or toe-off. The authors list the need for a synchronized phase variable as a limitation.
  - *On our server.* Trivial to reimplement in MyoAssist; maintained reference code in MimicKit (Apache-2.0).
  - *Code and assets.* public, MIT, last push 2025-11-27 (GitHub API, 2026-09-23); maintained successor xbpeng/MimicKit (Apache-2.0) implements DeepMimic, AMP, ASE, ADD
- **Muscular strategy shift in human running: dependence of running speed on hip and ankle muscle performance** — Dorn, Schache, Pandy. J Exp Biol 215:1944-1956; data SimTK project runningspeeds, 2012. doi:10.1242/jeb.064527 · [link](https://simtk.org/projects/runningspeeds)
  - *Idea.* Nine subjects ran overground from slow running to maximal sprinting; above about 7 m/s the strategy shifts from longer strides (ankle plantarflexors) to faster strides (hip muscles). SimTK releases one representative subject (JA1) at 3.56, 5.20, 7.00 and 9.49 m/s with models.
  - *Take from it.* The only open full-body data found near maximal sprint speed (9.49 m/s) across a speed ladder: tests whether a reference-free sprinter reproduces the >7 m/s shift to stride frequency.
  - *Left untested for this programme.* Archive contents (GRF, strides, markers vs IK) not inspected because the SimTK download timed out; one subject; 2011-era OpenSim formats.
  - *On our server.* MIT Use Agreement (Stanford, 2012); 2 MB zip; overground 3.56 to 9.49 m/s.
  - *Code and assets.* dataset (RunningDataModels.zip, 2 MB; contents not inspected)
  - *Also relevant to:* sprint_biomech_exosuits

### Reference

- **AddBiomechanics Dataset: Capturing the Physics of Human Motion at Scale** — Werling, Kaneda, Tan, Agarwal, Skov, Van Wouwe, Uhlrich, Bianco et al.. arXiv preprint; processing tool in PLOS ONE 18:e0295152 (2023, 10.1371/journal.pone.0295152), 2024. arXiv:2406.18537 · [link](https://addbiomechanics.org/download_data.html)
  - *Idea.* Re-processes public motion and force-plate studies with one automated pipeline into 273 subjects, 70+ hours and 24M frames: scaled skeletons, joint positions, velocities, accelerations, GRFs and joint torques. Sources include Camargo 2021, van der Zee 2022, Moore 2015 and Hamner 2013.
  - *Take from it.* One consistent processing route for walking and running references across source datasets, separating the effect of reference source from processing pipeline when comparing gait metrics.
  - *Left untested for this programme.* No sprint source identified in the source table; speed labels must come from original metadata; skeleton coordinates versus MyoAssist's 36 not checked.
  - *On our server.* CC BY 4.0; single archive (~4 h at 50 Mbps per the site); speeds follow the source studies.
  - *Code and assets.* dataset; AddBiomechanics web tool

### Already claimed by published work (cite it, compare against it, do not headline it)

- Muscle-driven imitation of a public treadmill reference, fine-tuned into hip and ankle exoskeleton assistance across 0.6 to 2.2 m/s and for simulated weakness (Choi et al. 2026, Hyfydy, arXiv 2604.09431).
- Multi-skill (walk, turn, backward, run) MuJoCo/MyoLeg imitation from AMASS and LAFAN1 with a co-adaptive hip exoskeleton, tested on six participants at 0.76 to 2.25 m/s (UniExo, arXiv 2609.19690, same group as SMAT).
- Head-to-head MuJoCo/MyoSim versus Hyfydy imitation benchmark against EMG on a shared reference (Ahmad et al. 2026, arXiv 2609.21909).
- Reference-free, muscle-driven 100 m sprinting on one GPU with comparison to an elite sprinter and EMG timing (Wang et al. 2026, Bolt, arXiv 2609.11083).
- Kinetics-aware (GRF/CoP) imitation rewards versus motion-only for walking joint moments (Liu et al. 2026, torque-driven, arXiv 2603.12408).
- Speed-conditioned adversarial imitation from synthetic speed-scaled references built on Camargo data (Chiu et al. 2024, torque-driven, arXiv 2412.03949).
- Large-scale MuJoCo muscle imitation with walking (1.2 m/s) and running (1.8 m/s) validation against public EMG datasets (MuscleMimic, arXiv 2603.25544; KINESIS, arXiv 2503.14637).
- Experiment-free exoskeleton assistance via learning in simulation (Luo et al., Nature 2024, 10.1038/s41586-024-07382-4; title verified here, content covered by the sim_to_real_exo_control and smat_uniexo_line clusters).

### Open questions this programme can attack

- No study found isolates how reference choice (dataset, subject, recorded versus speed-scaled, mirrored versus raw) moves left-right symmetry r and toe-off % in muscle-driven imitation; SMAT's Stage-1 targets make this a cheap ablation (MyoAssist npz vs Camargo 1.25 m/s vs van der Zee 1.25 m/s, each raw and mirrored).
- No open, full-stride, multi-subject maximal-sprint dataset with GRF was found; Phase-2 validation must rely on single-subject sets (Haralabidis 2021, Dorn 2012) and published summary curves.
- Kinetics-aware rewards (GRF/CoP) have not been tested in muscle-driven exoskeleton co-adaptation; whether they correct stance timing (toe-off) in MyoAssist is open.
- Provenance of MyoAssist's short_reference_gait.npz (89.8 s, 500 Hz, mean 1.28 m/s) remains undocumented; matching its cadence and joint ranges against Camargo, van der Zee or Scherpereel trials could identify it or justify replacing it.
- A hand-over from imitation (walk/jog references) to reference-free speed maximisation (Bolt, Lambda-Hold) within one MuJoCo muscle model with an exoskeleton was not found.
- MuJoCo-specific risks at sprint speed are untested in MyoAssist: Beyond Kinematics attributes weaker EMG fidelity partly to inelastic MuJoCo tendons, and the Bolt authors saw unstable sprint gaits with the MuJoCo constraint solver.


---

## 8. Exoskeleton control that reached hardware, and the matched baselines

**What this literature tells the programme**

- Matched baselines with human evidence already exist as two-parameter, phase-free laws: DOFC τ=κ[sin θR−sin θL](t−Δt) (Lim 2019; coded in Exo-Plore), negative damping Γ=βRq̇ (Ramella 2025), velocity-gated springs (Zhang 2026) and moment-proportional τ=α·M(t−d) (Molinaro 2024, Powell 2026, An 2026).
- Deployed sim-trained policies see short proprioceptive windows (Luo: ~40 ms of thigh angle/velocity; Park: one thigh gyro), so they are functionally close to those laws. Fit the laws to the learned policy's torque and test whether the residual carries any benefit.
- Comparator arms decide headlines: Manzoori's reflex law was −18% vs passive but −8.8% vs no-device; Collins modelled rather than measured the device-mass cost. Run no-device, zero-torque (mass-matched) and assisted arms for SMAT and every baseline.
- Tuning budget is a confound as large as controller class: Powell's single law gave 18.3% personalised vs 8.4% task-agnostic. Give each baseline the same number of simulated evaluations as SMAT's policy search.
- Report positive device power and the energy ratio with every saving. The Collins–Luo dispute turns on 5.5 vs 2.4 J saved per J; Collins puts the best prior hip value at ≈2.3. A simulated saving implying more than 4 should be treated as a modelling bug until explained.
- Timing reference is a hidden parameter: Collins swept 0–15% shifts from heel strike, Luo defines phase 0 at peak torque, and An 2026 found delay changed joint work but not metabolic rate. Sweep delay or phase for every baseline and pre-register the phase definition.
- Mechanical proxies are not metabolic outcomes (An 2026; Zhang 2026 reports work only; Park reports waveforms only). SMAT's simulated muscle-activation saving needs an explicit energetics model before it is compared with human metabolic results.
- Transfer evidence is partial everywhere: Park shows waveform transfer without efficacy, Barati shows efficacy without simple baselines, and no complete code exists for Luo, Park or Barati. For cable exosuits, validate tension delivery on the bench (Bardi, Wang) before judging any high-level policy.

### Must-read

- **Task-agnostic exoskeleton control via biological joint moment estimation** 📚 — Molinaro DD, Scherpereel KL, Schonhaut EB, Evangelopoulos G, Shepherd MK, Young AJ. Nature (published online 2024-11-13). doi:10.1038/s41586-024-08157-7 · [link](https://www.nature.com/articles/s41586-024-08157-7) · [code](https://doi.org/10.24433/CO.7641031.v2)
  - *Idea.* Moment-proportional control: a TCN estimates hip and knee biological moments from onboard exoskeleton sensors; command = 20% (hip) or 15% (knee) of the estimate, delayed 100 ms (hip) or 50 ms (knee), low-pass filtered. Energetics fell 5.3-19.7% vs zero-torque across ten activities.
  - *Take from it.* In simulation the true hip moment is free, so τ=0.2·M_hip(t−0.1 s), low-passed and capped, is a strong oracle baseline; add estimator-level noise for a deployable variant.
  - *Left untested for this programme.* Beat an idealised classifier/spline/impedance baseline, but no comparison with phase-free kinematic laws (DOFC, damping) or simulation-trained policies; Collins et al. compute its level-walking energy ratio at only 0.8.
  - *On our server.* Dataset and deployment code released; oracle moments come free from MuJoCo muscle forces, so this baseline costs one extra rollout config.
  - *Code and assets.* Code Ocean capsule to deploy/test trained estimators and dataset doi:10.35090/gatech/75759, both linked in the paper; not executed
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/molinaro-supplement-reading-03.md`
- **Delayed Output Feedback Control for Gait Assistance With a Robotic Hip Exoskeleton** — Lim B, Lee J, Jang J, Kim K, Park YJ, Seo K, Shim Y. IEEE Transactions on Robotics 35(4):1055-1062, 2019. doi:10.1109/TRO.2019.2913318 · [link](https://doi.org/10.1109/TRO.2019.2913318)
  - *Idea.* Delayed output feedback control: y(t)=sin θR(t)−sin θL(t) from low-pass-filtered hip angles; τR(t)=−κ·y(t−Δt), τL(t)=+κ·y(t−Δt) (form and signs as coded in Exo-Plore). Two parameters, no phase or terrain estimator; stability analysed on a leg-swing model; treadmill metabolic validation.
  - *Take from it.* Primary matched baseline: phase-free, deployable sensors only, two parameters. Tune (κ, Δt) with the same torque cap, RMS budget and simulator budget as SMAT; Exo-Plore's human-matched setting is κ=8 Nm, Δt=0.25 s.
  - *Left untested for this programme.* Abstract reports no effect size (Luo 2026 cites ≈19.8-21% at 10.9 Nm peak); no running or sprint tests in the abstract; never compared with a simulation-trained policy on the same device.
  - *On our server.* Trivial in MyoAssist: filtered-angle ring buffer plus a 2-D (κ, Δt) sweep; Exo-Plore bounds κ∈[0,21] Nm, Δt∈[0,0.5] s.
  - *Code and assets.* No author code; third-party DOFC implementation in Exo-Plore src/core/Device.cpp (CC BY-NC-SA 4.0)

### Should-read

- **Design and Validation of a Modified Delayed Output Feedback Controller for Hip Exoskeleton Assistance** 🆕 — Yoon S, Lee D, Lee HJ, Koo S. IEEE Transactions on Neural Systems and Rehabilitation Engineering 34:1921-1931 (record created 2026-04-08). doi:10.1109/TNSRE.2026.3682054 · [link](https://doi.org/10.1109/TNSRE.2026.3682054)
  - *Idea.* Modified DOFC adds harmonic components to delayed, amplified hip-angle feedback, still tuned by two parameters; parameters optimised in forward-dynamics gait simulation driven by an RL neural controller, then tested on people: metabolic reduction comparable to DOFC with 8.8% less mechanical power.
  - *Take from it.* Closest precedent for 'optimise a simple law in an RL-driven gait simulation, then transfer'; also check closed-loop stability of every baseline (they report stability up to 45 W via short-term Lyapunov exponents).
  - *Left untested for this programme.* Harmonic form, participant count and effect sizes not seen (abstract only); walking only; no comparison against a learned policy or velocity-based law.
  - *On our server.* Open access (CC BY 4.0); fetch the PDF from IEEE or PubMed (PMID 41950129) to get the harmonic formula.
  - *Code and assets.* none found; article CC BY 4.0 but IEEE PDF blocked here, read at abstract level
- **Effects of Assistance Delay on Joint Mechanics and Energetics in Biological Torque Control of a Hip Exoskeleton** 🆕 — An J, Lee R, Peng J, Halilaj E, Kang I. arXiv preprint (2026-09-21). arXiv:2609.25417 · [link](https://arxiv.org/abs/2609.25417)
  - *Idea.* Biological torque control τ(t)=filter(0.2·M̂hip(t−d)), capped 18 Nm, M̂ from a single-thigh-IMU TCN (950-ms window); delays 40-320 ms vs zero-torque, n=8, level/ramp walking. Delay changed joint-work unloading but not net metabolic rate (−5.24% overall; +1.23% on descent).
  - *Take from it.* Mechanical proxies and metabolic outcome diverged across delays, so simulated muscle-activation or joint-work savings (SMAT's metric) must not be read as metabolic; sweep delay for the moment baseline.
  - *Left untested for this programme.* Scale fixed at 0.2; no kinematic-law or learned-policy comparator; eight participants, level and ramp walking only; preprint, not yet peer reviewed.
  - *On our server.* Same oracle-moment pipeline as Molinaro; a five-level delay sweep is cheap in simulation.
  - *Code and assets.* none found
- **Versatile Exoskeleton Control Supports Elderly Joint Energetics During Hip-Intensive Tasks** 🆕 — Zhang J, Divekar NV, Krishnan C, Gregg RD. IEEE Transactions on Neural Systems and Rehabilitation Engineering (early access, record created 2026-09-10); arXiv v2 2026-08-13. arXiv:2603.22580 · doi:10.1109/TNSRE.2026.3732581 · [link](https://arxiv.org/abs/2603.22580)
  - *Idea.* Velocity-modulated virtual springs: unidirectional extension and flexion torsion springs on hip angle, each scaled by a sigmoid of hip angular velocity, plus task-context attenuation for descent and a torso-gated sit-to-stand spring; fixed parameters across tasks, 250 Hz, 4.6-kg device.
  - *Take from it.* A second velocity-based law with 2026 human data: velocity gating aligns torque with positive hip power (power-profile cosine similarity 0.89); hip biological positive work fell 24.7% in eight older adults.
  - *Left untested for this programme.* No metabolic or running data—biological work is a mechanical endpoint; parameters were tuned by optimisation plus one young user's feedback before testing older adults.
  - *On our server.* Sigmoid-gated spring is three lines of code; exact coefficients are in equation images—extract from the PDF before implementing.
  - *Code and assets.* none found
- **Adaptive Negative Damping Control for User-Dependent Multi-Terrain Walking Assistance With a Hip Exoskeleton** — Ramella G, Ijspeert A, Bouri M. IEEE ICORR 2025, pp. 1340-1346. arXiv:2503.03662 · doi:10.1109/ICORR66766.2025.11063198 · [link](https://arxiv.org/abs/2503.03662)
  - *Idea.* Virtual negative damping: Γ = β·R·q̇, R=[1 −1; 0 1] acting on stance and swing hip velocities (4-Hz filtered; stance leg = extending leg by velocity sign), β∈[1.0, 2.5] N·m·s/rad, adapted online by Bayesian optimisation of hip ROM minus jerk.
  - *Take from it.* Human anchor for the velocity-proportional baseline: fixed β=2.3 cut metabolic cost 7.2% vs free walking (n=5, 1.1 m/s, 4.4-kg eWalk) with <2% negative power; the programme's k·ω law is a single-joint, low-passed variant.
  - *Left untested for this programme.* Five participants, one treadmill speed, no zero-torque or phase-profile comparator; the optimiser's ROM-minus-jerk objective is not energetic; running-speed stability untested.
  - *On our server.* Minutes to implement in MyoAssist; sweep β at equal RMS torque against SMAT.
  - *Code and assets.* none found
- **Evaluation of controllers for augmentative hip exoskeletons and their effects on metabolic cost of walking: explicit versus implicit synchronization** — Manzoori AR, Malatesta D, Primavesi J, Ijspeert A, Bouri M. Frontiers in Bioengineering and Biotechnology 12 (2024-03-12). doi:10.3389/fbioe.2024.1324587 · [link](https://doi.org/10.3389/fbioe.2024.1324587)
  - *Idea.* Same device, two simple laws, 23 naive walkers at 4 km/h: Simple Reflex Controller (torque from relative foot loading: stance extension, swing flexion; implicit synchronisation) vs hip-phase-based predefined torque bursts (explicit). Metabolic −18.0% vs −11.6% relative to passive device.
  - *Take from it.* Only the reflex law beat no-exo (−8.8%): report no-device, passive/zero-torque and assisted arms; include one continuous state-driven law and one phase profile in the matched set.
  - *Left untested for this programme.* Torque magnitude and delivered power were not matched between controllers (SRC gave more power); single speed; no learned controller.
  - *On our server.* Foot-contact forces are free MuJoCo sensor readings; both laws are simple to replicate.
  - *Code and assets.* none found
- **Sensorless model-based tension control for a cable-driven exosuit** 📚 — Bardi E, Esser A, Wolf P, Gandolla M, Ambrosini E, Pedrocchi A, Riener R. Wearable Technologies 5 (2024-12-10). arXiv:2406.18412 · doi:10.1017/wtc.2024.21 · [link](https://doi.org/10.1017/wtc.2024.21)
  - *Idea.* Force-sensor-free cable tension control: an inverse Bowden-friction model maps desired tension to motor torque using separate affine fits for raising and lowering, blended by a sigmoid of joint velocity (IMU); load cell used only for identification and evaluation.
  - *Take from it.* Bench baseline for Phase-2 torque delivery: identify direction-dependent friction, run feedforward compensation, quantify reversal errors—before crediting any high-level policy with an outcome.
  - *Left untested for this programme.* Upper-limb gravity support only (n=17); torque RMSE 0.71 Nm (18%) at 50% support; no gait, sprint-rate reversals or bandwidth; printed sigmoid sign inconsistent (KB reading).
  - *On our server.* Needs a load cell only for calibration; refit coefficients for each spool, sheath and routing.
  - *Code and assets.* none public; data and analysis scripts on request (per KB reading)
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/bardi-tension-control-reading-04.md`

### Reference

- **Finite-Time Robust Control for Bowden Cable-Driven Exoskeletons With Time-Varying Cable Configurations** 🆕 — Wang Z, Zhou Z, Mai J, Wang Q. IEEE Transactions on Control Systems Technology 34(5):2901-2908 (Sep 2026). doi:10.1109/TCST.2026.3713361 · [link](https://doi.org/10.1109/TCST.2026.3713361)
  - *Idea.* Nonsingular terminal sliding-mode tracking controller for multi-DOF Bowden-cable exoskeletons whose cable configuration changes with wearer motion; no accurate model parameters needed, finite-time convergence via Lyapunov analysis; validated in simulation and experiments on a Bowden-cable hip exoskeleton.
  - *Take from it.* Sprint hip excursions change cable routing quickly; test transmission tracking under time-varying configuration on the bench, separately from the assistance policy.
  - *Left untested for this programme.* Tracking-only evaluation (abstract); no human energetic or performance outcome; sprint-rate reversals and slack not shown.
  - *On our server.* Hardware-stage reference; for simulation only its transmission limits matter.
  - *Code and assets.* none found; read at abstract level

### Already claimed by published work (cite it, compare against it, do not headline it)

- Training a hip-exoskeleton policy entirely in musculoskeletal simulation and transferring it to hardware with a metabolic benefit (Luo 2024, contested; Barati 2026; SMAT 2026).
- Distilling a privileged simulation teacher into a single-IMU student for hip assistance, validated by torque-waveform agreement (Park 2026).
- Optimising DOFC-family parameters in RL or musculoskeletal gait simulation, including a human-trend validation and a sim-to-human transfer (Exo-Plore 2026; Yoon 2026).
- Velocity-proportional (negative damping) or velocity-gated hip assistance lowering metabolic cost or biological work (Ramella 2025; Zhang 2026).
- Scale/delay/shape mappings of estimated hip moment, including personalisation and delay sweeps against zero-torque (Molinaro 2024; Powell 2026; An 2026).
- Energy-ratio plausibility audits of sim-to-real claims and fixed mean-profile replay replications (Collins 2026; rebutted by Luo 2026).
- Head-to-head comparison of implicit (state-driven) and explicit (phase-based) hip controllers on one device with passive and no-device arms (Manzoori 2024).
- Force-sensor-free model-based tension control for cable exosuits (Bardi 2024) and robust Bowden hip-exoskeleton tracking under time-varying cable configuration (Wang 2026).

### Open questions this programme can attack

- No study found compares a simulation-trained hip policy with DOFC, velocity-proportional and phase-profile controllers at matched peak/RMS torque, positive power and tuning budget, either in simulation or on one device.
- No energy-ratio (metabolic saving per joule of positive device work) check is reported for SMAT or any other simulation-trained hip policy's simulated benefit.
- No fitted-law distillation test found: how much of a learned hip policy's torque, and of its benefit, a two-parameter DOFC or k·ω law reproduces.
- No simulation-trained hip controller has been evaluated for sprinting or maximal running; the fastest learned-in-simulation hardware result found is Luo's 2 m/s running (13.1%), itself disputed.
- No simulation-trained high-level policy transferred to a cable-driven hip exosuit with human outcomes was found; cable work covers low-level tension or tracking (Bardi 2024, Wang 2026).
- Only DOFC has a simulated-versus-human trend validation (Exo-Plore); velocity-proportional and moment-proportional laws have none, so simulated baseline benefits are unvalidated.
- Luo 2026's claimed code and data release could not be located on 2026-09-23, so the learning-in-simulation dispute still cannot be adjudicated by re-running the original pipeline.


---

## 9. Human-in-the-loop optimisation and co-adaptation

**What this literature tells the programme**

- Real adaptation is slow and multi-timescale: novice ankle-exoskeleton users needed about 109 min of assisted walking to become expert while their optimal torque magnitude kept drifting (Poggensee & Collins 2021); hip-exosuit benefit plateaued after about two 20-min sessions and persisted five months (Panizzolo 2019); step frequency re-optimizes within minutes and re-converges within seconds (Selinger 2015). SMAT stages have no calibrated mapping onto these times, so report stage length in environment steps and do not call stages human acclimation phases without a calibration.
- Two gradient learners are not a wearer and a device. With a best-responding human, the machine's adaptation rate moved outcomes from Nash to human-led Stackelberg, and the authors note that rate changes alone do not move the stationary points of simultaneous gradient play (Chasnov et al. 2025). In SMAT it is freezing one actor that creates leader-follower structure; report learning-rate or stage-length effects as optimisation-dynamics effects and use cross-play between checkpoints to test which equilibrium was reached.
- Co-adaptation convergence results (Guo 2023 / KBS 2024; Su 2025) need finite MDPs, exact alternating policy iteration, ergodic chains and an information condition. None holds for PPO musculoskeletal sprint episodes with absorbing finish states, so use them to define baselines (fixed alternation, instantaneous and accumulated thresholds) and a tabular sanity test, never as a guarantee (KB readings 05-06).
- Non-stationary partners break standard optimisers: time-varying landscapes slowed BO and favoured exploitative or forgetting variants in simulation (Kutulakos & Slade 2024; Kim, Chishty & Sergi 2025), and a time-decaying kernel beat standard BO in hip-exoskeleton speed HILO (Kim & Sergi 2026). Any update-schedule comparison should include a device-side forgetting baseline and a novice-drift scenario.
- The objective changes the optimum: speed-optimal ankle assistance differed from energy-optimal assistance and was idiosyncratic (Song & Collins 2021). SMAT's reported outcomes are walking muscle activation and metabolic cost; sprint-time-optimal assistance has to be optimised and reported on its own terms, not inferred from walking-optimal timing.
- Simulated HILO is established practice, with surrogate landscapes (Kutulakos & Slade 2024), explicit motor-learning models (Kim, Chishty & Sergi 2025) and an RL neuromechanical human (Exo-Plore 2026). Each models a fixed landscape, a low-dimensional learner or an adapted steady state; none reproduces a wearer's multi-joint learning trajectory. Exo-Plore also flags stateless Hill muscles as problematic for fast running, a validity caveat for sprint simulation.
- No HILO of sprint assistance was found (searches on 2026-09-23). Running HILO is ankle, treadmill and metabolic (Witte 2020), and the sprint exosuit copied a simulation-derived hip profile under admittance control, leaving individual optimisation to future work (Moon et al. 2023, local PDF scirobotics.adf5611.pdf). Fatigue will limit later human sprint work to a few evaluations, which favours simulation-seeded priors and few-shot or preference-based tuning. That work stays human-run and lab-gated.
- In people, device updates and training exposure are confounded: biofeedback doubled energy savings and reached fully-adapted-level benefit in a quarter of the time (Lakmazaheri & Collins 2026), and an adaptive-gain controller shortened adaptation to about a third (Koller et al. 2015). Human comparisons of update schedules therefore need exposure-matched, counterbalanced, sham-controlled designs like Kim & Sergi 2026.

### Must-read

- **Validation of Dynamic Bayesian Optimization for Human-in-the-Loop Optimization of Exoskeleton Control at User-Driven Walking Speed** 🆕 — Kim, Sergi. bioRxiv preprint (v1 posted 2026-06-15). doi:10.64898/2026.06.10.731447 · [link](https://doi.org/10.64898/2026.06.10.731447)
  - *Idea.* Sixteen adults completed two counterbalanced 40-iteration HILO visits with a bilateral hip exoskeleton (torque-pulse amplitude, timing, duration) maximizing speed on a user-driven treadmill. Dynamic BO, whose time kernel down-weights older observations, exceeded BO's speed gains at three of four validation iterations.
  - *Take from it.* Treat the wearer as non-stationary: time-decaying kernels, interleaved validation iterations, counterbalanced optimizer order and a variability-matched sham form the design pattern for any later human comparison of update schedules.
  - *Left untested for this programme.* Walking capped at 1.6 m/s, 40 iterations per visit, healthy adults, sham tested in only three participants; no running or sprinting, and no learning model separating adaptation from fatigue or noise.
  - *On our server.* local PDF; DBO is a small change to any GP-BO library and can be tested first on the Kutulakos bench.
  - *Code and assets.* no code or data link in the bioRxiv v1 PDF (checked 2026-09-23)
- **On human-in-the-loop optimization of human–robot interaction** — Slade, Atkeson, Donelan, Houdijk, Ingraham, Kim, Kong, Poggensee, Riener, Steinert, Zhang, Collins. Nature 633(8031):779-788 (Perspective), 2024. doi:10.1038/s41586-024-07697-2 · [link](https://doi.org/10.1038/s41586-024-07697-2)
  - *Idea.* Perspective by twelve HILO groups: because human responses to devices cannot be modelled or predicted accurately enough, empirically optimize device characteristics on each user's measured performance; it walks through each key HILO decision across contexts and lists open algorithmic and scientific questions.
  - *Take from it.* Use its walkthrough of key HILO decisions as the checklist for the later human-study plan, and to state which of those decisions SMAT-style simulation replaces or merely assumes.
  - *Left untested for this programme.* Perspective without new data. Full text was paywalled and not read here, so whether it treats sprinting or models adaptation-optimizer interaction quantitatively is unchecked; read it before citing specifics.
  - *On our server.* Reading only; nature.com redirected to a login page on 2026-09-23, so institutional access is needed.
  - *Code and assets.* n/a (Perspective; no code)
- **Simulating human-in-the-loop optimization of exoskeleton assistance to compare optimization algorithm performance** — Kutulakos, Slade. bioRxiv preprint (v1 2024-04-09; no journal version listed by bioRxiv). doi:10.1101/2024.04.05.587982 · [link](https://doi.org/10.1101/2024.04.05.587982) · [code](https://github.com/Harvard-Slade-Lab/Simulating-Human-in-the-Loop-Optimization)
  - *Idea.* Gaussian-process surrogates of the metabolic landscape, fitted to five subjects' CMA-ES ankle-exoskeleton HILO data, replace measurements to simulate HILO for experts (static landscape), novices (landscape interpolated between subjects over 80 evaluations, ~160 min) and 4-20 parameters, comparing CMA-ES, cross-entropy, BO and exploitative BO.
  - *Take from it.* A cheap, reusable bench for optimizer and update-schedule comparisons: BO variants converged fastest for static experts (~60 evaluations), exploitative BO tracked the drifting novice optimum best, and no algorithm won everywhere.
  - *Left untested for this programme.* Adaptation is linear interpolation between two subjects' landscapes, not a learning process; surrogates were fitted to non-uniform CMA-ES samples; ankle walking only; simulated rankings were not tested prospectively in people.
  - *On our server.* local PDF; notebooks are CPU-light; swap in a sprint-time surrogate from the musculoskeletal sprinter.
  - *Code and assets.* official, MIT; Jupyter notebooks, dataset spreadsheet and saved GP models; last push 2024-04-11; the paper's Harvard-Ability-Lab link redirects here (checked 2026-09-23)
- **How adaptation, training, and customization contribute to benefits from exoskeleton assistance** — Poggensee, Collins. Science Robotics 6(58):eabf1078, 2021. doi:10.1126/scirobotics.abf1078 · [link](https://doi.org/10.1126/scirobotics.abf1078)
  - *Idea.* Naïve users learned ankle-exoskeleton walking under low-, moderate- or high-variation training. After moderate-variation training, customized assistance cut metabolic rate 39% versus exo off; training supplied about half, customization a quarter. Expertise took about 109 min; optimal peak torque kept rising.
  - *Take from it.* Calibration targets for any claim that simulated stages mirror acclimation: hours-scale expertise, training-type effects, users drawing less exoskeleton power as expertise grows, and slower drift in optimal torque magnitude than other parameters.
  - *Left untested for this programme.* Ankle only, treadmill walking, metabolic objective; no hip, running or sprint conditions. The abstract reports descriptive time courses, not a predictive adaptation model a simulation could be fitted to.
  - *On our server.* Reading only; use its reported timescales as priors when mapping simulated stages onto human sessions.
  - *Code and assets.* none known; paywalled full text not inspected (status as of 2026-09-23)

### Should-read

- **Using dynamic Bayesian optimization to induce desired effects in the presence of motor learning: a simulation study** — Kim, Chishty, Sergi. Computer Methods in Biomechanics and Biomedical Engineering, online 2025-12-03 (bioRxiv 10.1101/2024.08.13.607783). doi:10.1080/10255842.2025.2595150 · [link](https://doi.org/10.1080/10255842.2025.2595150)
  - *Idea.* Simulated HILO in which participant responses follow purely time-dependent drift or state-space motor-learning models (error-based adaptation plus use-dependent learning). Dynamic BO, adding time to the kernel, was never inferior to BO and overtook it once enough iterations separated learning from noise.
  - *Take from it.* Template for putting an explicit, parameterized human-learning model in the loop, so device-update schedules are compared against known adaptation rates rather than an uncalibrated learning agent.
  - *Left untested for this programme.* Low-dimensional input-output responses, not musculoskeletal locomotion; the state-space learners are generic motor-learning models, not fitted to exoskeleton wearers; no deep-RL device policies or sprint objectives.
  - *On our server.* Minutes on CPU; couple its state-space learner to a sprint-time surrogate to screen schedules before GPU runs.
  - *Code and assets.* no code or data link in the bioRxiv v2 full text; journal version paywalled (checked 2026-09-23)
- **Optimizing Exoskeleton Assistance for Faster Self-Selected Walking** — Song, Collins. IEEE Transactions on Neural Systems and Rehabilitation Engineering 29:786-795, 2021. doi:10.1109/TNSRE.2021.3074154 · [link](https://doi.org/10.1109/TNSRE.2021.3074154)
  - *Idea.* HILO of ankle-exoskeleton torque for self-selected speed on a self-paced treadmill: speed-optimized assistance made ten participants walk 42% faster than in normal shoes and faster than energy-optimized torque, with highly variable gaits and cost-of-transport changes from -31% to +78%.
  - *Take from it.* A speed or time objective yields different, highly individual optima than energy objectives; do not assume SMAT's muscle-activation outcome predicts sprint-time-optimal assistance.
  - *Left untested for this programme.* Walking only, tethered ankle exoskeletons; no running, sprinting or hip assistance, and no account of how user adaptation shaped the optimizer's speed estimates.
  - *On our server.* Reading only; its self-paced speed objective is the protocol analogue of simulated time-to-distance objectives.
  - *Code and assets.* unknown; PMC full text not retrievable by script (status as of 2026-09-23)
- **Metabolic cost adaptations during training with a soft exosuit assisting the hip joint** — Panizzolo, Freisinger, Karavas, Eckert-Erdheim, Siviy, Long, Zifchock, LaFiandra, Walsh. Scientific Reports 9:9779, 2019. doi:10.1038/s41598-019-45914-5 · [link](https://doi.org/10.1038/s41598-019-45914-5)
  - *Idea.* Over five sessions in 20 days of loaded walking (20.4 kg) with a hip-assisting soft exosuit, metabolic benefit versus unpowered grew from -6.2% to -10.3%, plateaued by session three (about two 20-minute sessions) and was retained five months later.
  - *Take from it.* Hip-specific adaptation timescale for planning human sessions: benefits grow over the first sessions, so familiarize participants before measuring any simulation-derived controller, and report session number.
  - *Left untested for this programme.* Fixed controller, loaded treadmill walking, metabolic outcome; no optimization during adaptation and no running or sprinting.
  - *On our server.* Reading only (open access); treat its session-level timescale as a prior, not a model.
  - *Code and assets.* none (no code or data statement found in the PMC full text) (checked 2026-09-23)
- **Human-in-the-loop optimization of hip assistance with a soft exosuit during walking** — Ding, Kim, Kuindersma, Walsh. Science Robotics 3(15):eaar5438, 2018. doi:10.1126/scirobotics.aar5438 · [link](https://doi.org/10.1126/scirobotics.aar5438)
  - *Idea.* Bayesian optimization of the peak and offset timing of hip-extension assistance from a textile exosuit found optima in 21.4 ± 1.0 min and cut walking metabolic cost 17.4 ± 3.2% versus no device, revealing participant-specific metabolic landscapes.
  - *Take from it.* Closest hip precedent: two timing parameters, BO under noisy metabolic signals, and evidence that optimal hip timing is individual; its timing parameterization is a comparator for learned sprint assistance.
  - *Left untested for this programme.* Treadmill walking, hip extension only, metabolic objective; no running, sprinting or flexion assistance, and BO assumed the user's response was stationary.
  - *On our server.* Reading only (paywalled); a two-parameter timing landscape is easy to emulate as a simulated-HILO test case.
  - *Code and assets.* none known; paywalled full text not inspected (status as of 2026-09-23)
- **Human-in-the-loop optimization of exoskeleton assistance during walking** — Zhang, Fiers, Witte, Jackson, Poggensee, Atkeson, Collins. Science 356(6344):1280-1284, 2017. doi:10.1126/science.aal5054 · [link](https://doi.org/10.1126/science.aal5054)
  - *Idea.* Landmark exoskeleton HILO: CMA-ES tuned ankle torque-profile parameters from rapid metabolic estimates during walking. Optimized one-ankle assistance cut metabolic energy 24.2 ± 7.4% versus zero torque; the approach also worked bilaterally, across conditions, during running and for muscle-activity objectives.
  - *Take from it.* Reference protocol and effect sizes for later human work; its finding that a good generic pattern, customization and user learning all contributed is the empirical basis for separating those factors in simulation claims.
  - *Left untested for this programme.* Tethered ankle emulator, treadmill, metabolic objective with minutes per evaluation; no hip assistance or sprinting, and user learning during optimization was not modelled.
  - *On our server.* Reading only (paywalled); metabolic HILO protocols do not transfer to maximal sprint trials.
  - *Code and assets.* none known; paywalled full text not inspected (status as of 2026-09-23)
- **Humans Can Continuously Optimize Energetic Cost during Walking** — Selinger, O'Connor, Wong, Donelan. Current Biology 25(18):2452-2456, 2015. doi:10.1016/j.cub.2015.08.016 · [link](https://doi.org/10.1016/j.cub.2015.08.016)
  - *Idea.* Exoskeletons shifted walkers' energetically optimal step frequency; people converged on the new optimum within minutes, for savings under 5%, and after perturbations re-converged within seconds using an updated prediction, showing continuous real-time optimization of energetic cost.
  - *Take from it.* The human partner is itself a fast, noisy energy optimizer; frozen or slowly updated simulated humans misrepresent this, so report which human timescale, if any, each SMAT stage stands for.
  - *Left untested for this programme.* One gait parameter (step frequency) in walking under imposed cost gradients; not whether multi-joint sprint coordination adapts on similar timescales, or how people respond to a controller that itself adapts.
  - *On our server.* Reading only; its timescales (minutes to converge, seconds to re-converge) are candidate priors for a rate-limited simulated human.
  - *Code and assets.* none known; paywalled full text not inspected (status as of 2026-09-23)

### Reference

- **A Dual Control Approach to Solve Exploration Versus Exploitation Trade-Offs in the Design of Personalized Physical Exercise Sessions** 📚 — Jackson, Varagnolo, Knorn. IEEE Control Systems Letters 7:2383-2388, 2023. doi:10.1109/LCSYS.2023.3287138 · [link](https://doi.org/10.1109/LCSYS.2023.3287138)
  - *Idea.* Casts personalized exercise-session design as dual control: inputs trade immediate exercise effect against Fisher-information parameter learning weighted by control relevance. In a simulated muscle-compartment (Kegel) model, more information weight cut estimation error but also reduced same-session exercise effect.
  - *Take from it.* Probing versus exploiting is already formalized; any 'informative assistance' or exploration-bonus claim for the device needs a dual-control comparator and must count probing cost (KB reading-07).
  - *Left untested for this programme.* Simulation only, batch design between sessions; no wearable robot, locomotion or participants; printed recurrences and sensitivity equations need clarification before reimplementation (KB reading-07).
  - *On our server.* CPU-scale; the KB digest documents the equation issues; build an independent dual-control baseline only if an exploration claim is made.
  - *Code and assets.* none (no code provided; KB reading-07)
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/dual-control-primary-reading-07.md`
- **Improving the energy economy of human running with powered and unpowered ankle exoskeleton assistance** — Witte, Fiers, Sheets-Singer, Collins. Science Robotics 5(40):eaay9108, 2020. doi:10.1126/scirobotics.aay9108 · [link](https://doi.org/10.1126/scirobotics.aay9108)
  - *Idea.* HILO of powered and spring-like ankle-exoskeleton torque during treadmill running: optimized powered assistance improved energy economy 24.7% versus zero torque and 14.6% versus normal shoes, while spring-like assistance was ineffective; optima varied but shared high positive work and late peak timing.
  - *Take from it.* The only running HILO found: powered, positive-work assistance helped where spring-like assistance did not, supporting positive-power targets for sprint assistance; its 'up to 10% faster' is an extrapolation, not a measurement.
  - *Left untested for this programme.* Steady treadmill running, ankle only, metabolic objective with long evaluations; no sprinting, acceleration, hip assistance or measured speed gain, and adaptation during optimization was not modelled.
  - *On our server.* Reading only (paywalled); metabolic running HILO is not transferable to maximal sprint trials.
  - *Code and assets.* none known; paywalled full text not inspected (status as of 2026-09-23)

### Already claimed by published work (cite it, compare against it, do not headline it)

- Optimising hip-exoskeleton gain and delay in simulation alone, with an RL neuromechanical human that adapts across assistance settings: Exo-Plore (ICLR 2026, arXiv 2601.22550).
- Simulating HILO on fitted surrogate landscapes to choose optimisers, including a novice-adaptation scenario: Kutulakos & Slade 2024 (bioRxiv). Hip-exoskeleton surrogate version: Mohammadzadeh Gonabadi et al., Front. Robot. AI 2025 (doi 10.3389/frobt.2025.1669600). EMG-surrogate version: Gonabadi et al., J. Sens. Actuator Netw. 2025 (doi 10.3390/jsan14060113). Online simulated metabolic cost inside real hip-exoskeleton HILO: Gordon et al., IEEE T-RO 2022 (doi 10.1109/TRO.2021.3133137).
- Time-aware (dynamic) Bayesian optimisation for non-stationary human responses, in simulation and in hip-exoskeleton walking-speed HILO: Kim, Chishty & Sergi 2025; Kim & Sergi 2026.
- Alternating or threshold-gated policy updates for human-machine co-adaptation, with convergence conditions: Guo et al. (arXiv 2023; KBS 2024) and Su et al. 2025. The same group extended this to dual-agent RL co-adaptation: Li, Han, Liu & Su, arXiv 2603.06163 (2026).
- The machine's adaptation rate or policy selects the equilibrium human-machine co-adaptation reaches: Chasnov et al. 2025. Related claims: an algorithm reaching the human's cost minimum from observed actions (Isa, Ratliff & Burden, arXiv 2501.08626, 2025); mid-range machine learning rates as the sweet spot for two co-adapting learners (Müller et al., J. Neural Eng. 2017, doi 10.1088/1741-2552/aa620b); differential-game pHRI control (Li et al., Nat. Mach. Intell. 2019, doi 10.1038/s42256-018-0010-3).
- Joint multi-agent RL of a musculoskeletal human and a hip exoskeleton in simulation: SMAT (arXiv 2603.07618, 2608.00715), UniExo (arXiv 2609.19690, includes running), and Sun et al., Med. Biol. Eng. Comput. 2026 (MATD3 in OpenSim, doi 10.1007/s11517-026-03634-9).
- HILO with walking speed as the objective: Song & Collins 2021; multi-objective speed and economy in older adults, who also needed longer to adapt (Lakmazaheri et al., JNER 2024, doi 10.1186/s12984-023-01287-5); Kim & Sergi 2026. Hip HILO beyond level walking: stair climbing, where metabolic rate converged after about 18 iterations but most parameters had not converged within 20 (Park et al., IEEE TBME 2025, doi 10.1109/TBME.2025.3536516).
- Fast, real-world and user-driven HILO: outdoor ankle optimisation (Slade et al., Nature 2022, doi 10.1038/s41586-022-05191-1); a portable hip-extension exosuit, from the sprint-exosuit lab, optimised outdoors in 3 min 24 s (Nam et al., Adv. Robot. Res. 2026, online 2025, doi 10.1002/adrr.202400027); preference-based hip-exoskeleton self-tuning in about 11 min (Schäfer et al., npj Biomed. Innov. 2026, doi 10.1038/s44385-026-00085-7).
- Training design and feedback change how fast people adapt: Poggensee & Collins 2021; biofeedback (Lakmazaheri & Collins, IEEE TNSRE 2026, doi 10.1109/TNSRE.2025.3650042); adaptive-gain myoelectric control (Koller et al., JNER 2015, doi 10.1186/s12984-015-0086-5).

### Open questions this programme can attack

- Which equilibrium does SMAT reach? At matched budgets, train fast-device/slow-human, slow-device/fast-human and simultaneous schedules, then cross-play every final human checkpoint against every device checkpoint. Test whether outcomes shift as leader-follower theory predicts, checking the pipeline first on a toy quadratic game (Chasnov-style).
- A rate-limited simulated human: cap per-stage human policy change (KL or step budget) to mimic published adaptation timescales, then test whether a device policy trained against it transfers better to held-out human policies than one trained against a freely learning PPO human. The calibration to real minutes stays indirect and must be stated as such.
- Simulated sprint HILO under realistic budgets: extend the Kutulakos & Slade bench to a sprint-time surrogate from the musculoskeletal sprinter, with 10-20 fatigue-limited evaluations per session, a novice-drift scenario, and BO, dynamic BO and CMA-ES compared. The output is the optimiser a later human study should pre-register.
- Objective mismatch in simulation: in the same simulated sprinter, compare assistance optimised for 200 m time with assistance optimised for muscle activation or a metabolic proxy, and quantify the differences in timing and magnitude before any human work. This is the sprint version of the Song & Collins 2021 question.
- Tabular falsification of the CaMDP conditions: discretise a reduced human-exoskeleton task, check the information and dominance conditions directly, and run alternation, instantaneous-threshold and accumulated-threshold schedules against the PPO results (following KB reading-06).


---

## 10. Sprint biomechanics, running and sprint exosuits

**What this literature tells the programme**

- The simulated speed ceiling belongs to the muscle model, not the controller. In Lambda-Hold (2608.17030), H2190 tops out near 4.7 m/s because fully active psoas/iliacus produce only 0.26/0.33 of isometric force at their fastest shortening, and doubling Vmax (10→20 optimal lengths/s) gives ~6.5 m/s. Removing force–velocity in Miller et al. 2012 adds 15%. That makes swing-phase hip-flexion assistance a direct test of the planned human model's bottleneck, even though Moon assisted extension.
- Parity matters more than usual. Lin & Pandy 2022 show that +10% strength gives +5.9% top speed and +10% Vmax gives +2.4%, while Moon's human effect is only ~3% of 200 m time (0.97 of 32.79 s). A strength or Vmax change applied to the assisted condition alone would swamp any device effect. Keep such changes as symmetric diagnostics only.
- Speed regimes do not line up. Lambda-Hold's 4.7 m/s top speed is below the ~6.1 m/s average 200 m speed of Moon's non-elite runners and far below Dorn et al.'s ~7 m/s shift to a hip-driven stride-frequency strategy. Bolt's sprinter peaks at 12.5±0.5 m/s against 9.65 m/s in the comparison data. Only percentage change against the same model's own unassisted baseline carries over between models, and even that needs a check across plant speeds.
- Hip versus ankle depends on the phase. At steady high speed, hip extensor/knee flexor terminal-swing loads rise most (Schache 2011), and the ideal hip actuator beats ankle/knee at 5 m/s (Uchida 2016: 33±4%). During acceleration, however, the ankle supplies the most positive work (Schache 2019, JEB, 1.55±0.17 J/kg), and freeing knee moments helps most (Haralabidis 2022). Yet Moon's significant gain was in the first 100 m. Report 0–30/30–60/60–100/100–200 m splits.
- Ideal-device studies cannot predict sprint time. Uchida fixes kinematics and GRFs (metabolic savings only), and Haralabidis frees net joint moments with no device limits. The step from 'ideal' to 'realizable' (tension-only, attachment-dependent moment arm, delay, torque-speed-power limits, mass) has not been simulated for sprinting, and Ciaramella's −9.6% vs −4.3% net shows how much wearing the unpowered suit costs.
- Contact and constraint modelling can decide whether sprinting emerges at all. Bolt reports that MuJoCo's solver-based joint limits/contacts gave unstable sprints (lateral foot drift, stride variance), that rigid tendons increased stride-frequency variance, and that uncalibrated passive forces were exploited through hip rotation. Miller finds tendon elasticity worth 26% of top speed. The planned MuJoCo/MyoLeg port therefore needs an unassisted equivalence check against H2190/Hyfydy before any exosuit run.
- No sprint simulation models fatigue. Bolt holds maximal output for 100 m, and Lambda-Hold has no fatigue term. 3CC-r (Looft 2018) is calibrated on isometric ankle/knee/elbow/grip data only (r=15; no hip), and MyoSuite's default uses elbow values. A 200 m model therefore either adds an uncalibrated per-muscle fatigue law or a whole-body energy budget (Mader model, MetaboliSim). That choice determines whether any second-half benefit can appear.
- Non-learned comparators already exist and should be matched on limits: Moon's fixed profile (2/30/45% after max hip flexion, 20–35% BW peak, 0.15 m arm), PositiveAssist's energy gate (>94.8% positive power in running up to 3.5 m/s), and Foggetti et al.'s stride-wise timing optimizer (BioRob 2026, +6.1–17.2% positive work offline). Passive tension-only baselines include Simpson's exotendon (6.4%), Yang's hip-flexion bands (4.7%, 609 g) and Nasiri's inter-hip spring (TNSRE 2018, 8.0±1.5% at 2.5 m/s).

### Must-read

- **Reducing sprint time with exosuit assistance in the real world** 📚 — Moon, Nam, Ryu, Kim, Yun, Yang, Yang, Lee. Science Robotics 8(82): eadf5611, 2023. doi:10.1126/scirobotics.adf5611 · [link](https://doi.org/10.1126/scirobotics.adf5611) · [code](https://doi.org/10.5281/zenodo.8273031)
  - *Idea.* Portable Bowden-cable exosuit assists hip extension with a fixed, IMU-timed admittance force profile during outdoor 200 m sprints. Nine non-elite men ran 0.97±0.41 s (SEM) faster; first 100 m gain significant (0.68 s), second 100 m not (0.30 s); step-frequency change correlated with gain.
  - *Take from it.* Comparator device: force onset/peak/release at 2/30/45% of the cycle after maximum hip flexion, peak 20–35% body weight, assumed 0.15 m moment arm; 32.79→31.82 s group means (≈6.1 m/s average).
  - *Left untested for this programme.* Only suit-on vs no-suit (no unpowered-suit arm), so mass and assistance are confounded; no hip-flexion arm, fatigue or metabolic measure; per-trial wind unreported; two of nine slowed.
  - *On our server.* Supplement suffices to rebuild the force-profile controller as a sim comparator; no raw data or code, so fit is to published means only.
  - *Code and assets.* No controller code or raw data found. Zenodo holds only the supplementary materials (4 DataCite versions, CC BY 4.0); its description lists Tables S1-S4, but the KB's 7-page local copy has S1-S3 (Zenodo files not opened: HTTP 403, 2026-09-23).
  - *Already digested in the KB:* `sail-lab-application-kb/research-program-2026-09-07/sources/reading-batches/core-sprint-pdf-reading-01.md`
- **Simulating Ideal Assistive Devices to Reduce the Metabolic Cost of Running** — Uchida, Seth, Pouya, Dembia, Hicks, Delp. PLOS ONE 11(9): e0163417, 2016. doi:10.1371/journal.pone.0163417 · [link](https://doi.org/10.1371/journal.pone.0163417) · [code](https://simtk.org/home/idealassist_run)
  - *Idea.* CMC simulations of 10 runners at 2 and 5 m/s (OpenSim, 92 muscles) add massless, lossless, unlimited ideal torque actuators at hip, knee and/or ankle while tracking unassisted kinematics and GRFs, then compare predicted muscle metabolic power.
  - *Take from it.* Speed flips the best joint: ideal hip flexion/extension saves 25±2%→33±4% (2→5 m/s) while ankle falls 26±4%→19±4%; peak mean hip torque 3.5 N·m/kg, the unconstrained reference for limited devices.
  - *Left untested for this programme.* Kinematics and GRFs are fixed, so speed or sprint-time changes cannot emerge; no device mass, torque, power or tension limits; nothing above 5 m/s; no acceleration.
  - *On our server.* Reproducible in OpenSim from public data; for sprinting, rerun predictively (not tracking) with the same ideal hip actuator as the upper bound.
  - *Code and assets.* Per Data Availability: simulations/data at simtk.org/home/idealassist_run, metabolics plug-in at github.com/opensim-org/opensim-metabolicsprobes; SimTK did not respond on 2026-09-23 (not re-checked).
- **Limitations to maximum sprinting speed imposed by muscle mechanical properties** — Miller, Umberger, Caldwell. Journal of Biomechanics 45(6): 1092–1097, 2012. doi:10.1016/j.jbiomech.2011.04.040 · [link](https://doi.org/10.1016/j.jbiomech.2011.04.040)
  - *Idea.* Maximum-speed 2D Hill-muscle sprinting simulations were rerun with single muscle properties removed: removing force–velocity raised speed 15%, excitation–activation 8%, force–length 4%; removing series elasticity cut speed 26%; ideal joint torques gave +22%.
  - *Take from it.* Sanity bounds for the Hill-model ceiling: removing force–velocity adds 15% top speed; removing tendon elasticity costs 26%, so rigid-tendon MuJoCo muscles need a check before any assisted-speed claim.
  - *Left untested for this programme.* 2D model with lumped muscles; no acceleration, 200 m or fatigue; properties removed wholesale rather than bounded; no external assistive torque or device limits.
  - *On our server.* Cheap to replicate as ablations in the reimplemented model (force–velocity off, Vmax scaled): diagnostics only, never in the assisted condition alone.
  - *Code and assets.* No code found (abstract and API records only).
  - *Also relevant to:* physiology_grounded_control

### Should-read

- **Design and Overground Testing of a Portable Hip Exosuit for Enhancing Running Efficiency** — Ciaramella, Bagneschi, Tricomi, Missiroli, Zhang, Frisoli, Masia. IEEE Transactions on Medical Robotics and Bionics 7(1): 33–42, 2025. doi:10.1109/TMRB.2024.3503905 · [link](https://doi.org/10.1109/TMRB.2024.3503905)
  - *Idea.* A portable active exosuit with custom linear actuators assists hip extension, synchronized to the wearer's kinematics, and is tested on an athletics track at self-selected endurance-running pace in seven participants.
  - *Take from it.* Realistic overground effect size: metabolic cost of transport −9.6% vs unpowered but only −4.3% net vs no device, so wearing it unpowered costs roughly 5%; kinematics after toe-off unchanged.
  - *Left untested for this programme.* Endurance pace only, no sprint or speed outcome; n=7; no hip-flexion assistance; actuator bandwidth at sprint cadence untested.
  - *On our server.* Use its net-versus-unpowered split to size the simulated device-mass penalty; hardware parameters beyond the abstract need the paywalled paper.
  - *Code and assets.* No code found (abstract and API records only).
- **Modifications to the net knee moments lead to the greatest improvements in accelerative sprinting performance: a predictive simulation study** — Haralabidis, Colyer, Serrancolí, Salo, Cazzola. Scientific Reports 12: 15908, 2022. doi:10.1038/s41598-022-20023-y · [link](https://doi.org/10.1038/s41598-022-20023-y) · [code](https://doi.org/10.6084/m9.figshare.14988051)
  - *Idea.* Direct-collocation (CasADi/IPOPT) 3D model (92 muscles) scaled to an international sprinter tracks, then predicts, the first acceleration steps with net ankle, knee and/or hip moments freed; performance is average horizontal external power.
  - *Take from it.* Ideal-moment upper bounds for early acceleration: knee-free +13.8%, knee+hip-free +21.9%, all-free +22.0% (1401 vs 1149 W); hip-free gains were smaller, bounding what a hip-only device can add early.
  - *Left untested for this programme.* Only the first few acceleration steps; freed net moments carry no device limits (tension, power, delay, mass); no top-speed phase, 200 m, fatigue or human validation.
  - *On our server.* MATLAB/CasADi collocation suits the EPYC CPU; transferring the 'free-moment' idea to RL means adding an ideal hip actuator arm.
  - *Code and assets.* Figshare dataset described as 'Data files, model and videos'; solver code not mentioned in that description (description checked only, 2026-09-23).
- **Predictive Simulations of Human Sprinting: Effects of Muscle–Tendon Properties on Sprint Performance** — Lin, Pandy. Medicine & Science in Sports & Exercise 54(11): 1961–1972, 2022. doi:10.1249/mss.0000000000002978 · [link](https://doi.org/10.1249/mss.0000000000002978)
  - *Idea.* A 3D, 86-muscle predictive dynamic optimization of maximum-speed sprinting, seeded from a jogging solution, varies lower-limb strength, fascicle length, intrinsic maximum shortening velocity and tendon compliance to rank their effect on top speed.
  - *Take from it.* Sensitivity table for parity checks: +10% strength → +5.9% top speed; fascicle length +4.7%; Vmax +2.4%; tendon compliance +0.3%. Any assisted-only change to these would swamp a 2–3% exo effect.
  - *Left untested for this programme.* Maximum-speed gait only: no standing start, 200 m or fatigue; no external assistance; properties changed across lower-limb muscles together, not per group.
  - *On our server.* No code; use the numbers as external checks on the reimplemented model's speed sensitivity (e.g., a +10% Vmax diagnostic run).
  - *Code and assets.* No code found (abstract and API records only).
- **Modification of a three-compartment muscle fatigue model to predict peak torque decline during intermittent tasks** — Looft, Herkert, Frey-Law. Journal of Biomechanics 77: 16–25, 2018. doi:10.1016/j.jbiomech.2018.06.005 · [link](https://doi.org/10.1016/j.jbiomech.2018.06.005) · [code](https://github.com/MyoHub/myosuite/blob/main/myosuite/envs/myo/fatigue.py)
  - *Idea.* Adds a rest-recovery multiplier r to the three-compartment (resting/active/fatigued) controller fatigue model; fitted to 351 intermittent isometric torque-decline points from 63 studies, cutting prediction error from 19–29% to 6–10% torque decline.
  - *Take from it.* Joint parameters: ankle F=0.00589, R=0.00058; knee F=0.0150, R=0.00149; r=15 (no hip data). MyoSuite's default is elbow-based, so lower-limb values must be set explicitly.
  - *Left untested for this programme.* Isometric intermittent tasks only; dynamic contractions excluded; no hip or trunk data; no fibre-type dependence; never validated for sprinting or 20–40 s maximal efforts.
  - *On our server.* Three ODEs per muscle, trivially batched on GPU; the real cost is calibrating against sprint speed-decay data.
  - *Code and assets.* No official code. Third-party: MyoSuite CumulativeFatigue (3CC-r via Cheema et al. CHI 2020 / User-in-the-Box), defaults F=0.00912, R=0.1×0.00094, r=150, plus an MJX variant fatigue_jax.py (checked 2026-09-23).
  - *Also relevant to:* physiology_grounded_control
- **Faster top running speeds are achieved with greater ground forces not more rapid leg movements** — Weyand, Sternlight, Bellizzi, Wright. Journal of Applied Physiology 89(5): 1991–1999, 2000. doi:10.1152/jappl.2000.89.5.1991 · [link](https://doi.org/10.1152/jappl.2000.89.5.1991)
  - *Idea.* Treadmill force-plate measurements in 33 runners (top speeds 6.2–11.1 m/s) and in inclined/declined top-speed running show faster runners apply larger stance-averaged vertical forces (1.26× from 6.2 to 11.1 m/s) while minimum swing time does not vary.
  - *Take from it.* Mechanism readouts for any simulated gain: stance-averaged force/body weight, contact time and swing time. Weyand 2010 adds the contact-time limit: ~0.11 s and ~2.1 BW at top forward speed.
  - *Left untested for this programme.* Mostly correlational (plus an incline/decline contrast); treadmill top speed only; no acceleration or fatigue; no muscle-level cause; no assistance. Conflicts with simulation claims that hip-driven swing sets stride frequency above 7 m/s.
  - *On our server.* Paper-only; the three scalar metrics are computable from any simulated GRF trace.
  - *Code and assets.* Not applicable (experimental study).

### Already claimed by published work (cite it, compare against it, do not headline it)

- Hip-extension exosuit reduces real-world 200 m sprint time: 0.97±0.41 s (SEM), n=9 non-elite men, significant only in the first 100 m. Moon et al., Science Robotics 2023 (10.1126/scirobotics.adf5611).
- Demonstration-free RL of a muscle-driven full 100 m sprint (~10 s, 12.5 m/s peak) on one GPU with an open Warp simulator, plus the finding that MuJoCo solver constraints degrade sprint gaits. Wang et al., arXiv 2609.11083 (SIGGRAPH Asia 2026).
- Minimal-reward RL sprinting from a standing start in a 90-muscle model within ~1 h via equilibrium-point λ holds, with the hip-flexor force–velocity ceiling (4.7→6.5 m/s) identified. Lee, Lee, Ahn, arXiv 2608.17030.
- RL-trained ideal hip/ankle exo torques in an H2190 human cut simulated running metabolic cost 6.95%/13.81% (≤2.2 m/s). Choi et al., arXiv 2604.09431.
- The ideal hip actuator is the most effective single joint at 5 m/s running (33±4% simulated metabolic saving). Uchida et al., PLOS ONE 2016.
- Predictive optimal-control sprint studies: freeing knee/hip net moments raises early-acceleration power 13.8–22% (Haralabidis et al. 2022); top-speed sensitivity to strength, fascicle length, Vmax and tendon compliance (Lin & Pandy 2022; Miller et al. 2012, 2D).
- Energy-gated positive-power hip exoskeleton control that works across walking and running up to 3.5 m/s without retuning. Zhou et al., IEEE/ASME TMECH 2026 (PositiveAssist).
- Soft-suit sprint augmentation programme with a stated goal of a 7 s 100 m for an average (17 s) runner, using pneumatic artificial muscles and a hybrid energy system. DASH, Yonsei HCAIR (Prof. Dongjun Shin), programme page https://hcr.yonsei.ac.kr/research/Human-Robotic-Mobilities/ALC/. The lab's publication list shows related work (a pneumatic jump-enhancement soft suit, Adv Intell Syst 8(2); running aerodynamics and required power, Int J Appl Mech 15(1)) but no sprint-assist result.

### Open questions this programme can attack

- Primary endpoint unoccupied (search result, not proof): no study found simulates an actuator-limited, tension-only hip exosuit (moment arm, delay, torque-speed-power limits, mass) and reports a change in simulated 200 m (or any sprint) time. Run it against the ideal-hip-actuator upper bound and a mass-only (unpowered) arm.
- Flexion versus extension at sprint speed: the model's bottleneck is hip-flexor force–velocity in swing (Lambda-Hold), but the only human sprint evidence assisted extension (Moon). No human or simulation study compares matched-limit flexion, extension and bidirectional assistance for sprint time.
- Phase decomposition: no simulation splits an assisted sprint gain into standing-start acceleration, top-speed and fatigue phases, or checks Moon's first-100 m pattern. Log 10 m splits, contact time, stance-averaged force/BW and swing time (Weyand), and ratio of forces (Morin 2011).
- Fatigue for a 200 m: there are no dynamic-contraction or hip 3CC-r parameters, and no sprint RL paper models fatigue. Calibrate a fatigue or energy-budget layer against published 200 m velocity decay before claiming second-half effects, and report results with and without it.
- Plant-speed transfer: no work tests whether an exo's percentage benefit measured on a 4.7 m/s plant holds on a faster plant. Repeat the best controller on a symmetric Vmax-curriculum (diagnostic) human and on Bolt's open sprinter model.
- Engine sensitivity: Bolt's MuJoCo-constraint failure has not been tested on MyoLeg-style models with explicit device cables. Measure unassisted sprint speed, stride variance and lateral drift across solver settings and ≥5 seeds before the exosuit experiments (Lambda-Hold used 2 seeds; Bolt reported the best of up to 5).
- Environment realism: neither Lambda-Hold nor Bolt mentions aerodynamic drag (full-text search). A 2026 on-site study (D'Angelo et al., Exp Fluids, 10.1007/s00348-026-04204-3) reports drag areas 30–40% below earlier estimates at 8 m/s, so check how sensitive the 200 m time is to drag at the model's speeds.


---

## 11. Physiology-grounded control and sprinting humans

**What this literature tells the programme**

- Three demonstration-free RL results give muscle-driven top speeds. Lambda-Hold reached about 4.7 m/s on H2190 at default strength (two seeds). Bolt reached 12.5 m/s with 136 muscles and doubled lower-body strength. Schumacher et al. reached 5.44 m/s on MyoLeg, best of 20 rollouts. None reports five-seed medians at fixed strength.
- The simulator is a first-order risk. In Bolt's ablation, MuJoCo's constraint solver for contacts and joint limits prevented realistic sprinting, and MyoLeg runs with strong lateral torso oscillation (Schumacher et al.). Validate contacts and limits before blaming the controller.
- Lambda-Hold's gain splits into two parts. Holding alone (excitation-hold) returns about 10x plain SAC; the lambda-space reflex adds more than another 10x (returns are exponential in speed). The direct-excitation human should therefore use the same GRF holds, which matches their excitation-hold ablation.
- Exploration results depend on regime. gSDE and DEP worked at CPU scale (Lambda-Hold, Schumacher et al.) but gave no gain under large-batch GPU FastTD3 (Bolt). Report exploration together with batch size and throughput, not as a universal winner.
- Muscle physiology sets the speed ceiling: force-velocity (Miller 2012; Lambda-Hold's hip flexors fall to 26-33% of isometric force) and hip strength (Yang 2026). Freezing strength, maximum shortening velocity and activation time constants is what makes the 4.0 m/s gate meaningful.
- No sprint RL paper found models fatigue. MyoSuite (v2.4.0 and later) and KINESIS ship 3CC-r, but its default parameters come from elbow isometric data. Calibrate it before making any claim about the second 100 m of a 200 m.
- Holding on gait events is one design choice among several: learned durations (TempoRL), per-dimension act-or-repeat (SDAR, ICLR 2025, arXiv 2502.06919) and state-deviation-triggered repeats (Safe Action Repetition, NeurIPS 2021, arXiv 2111.03941). None has been tested on musculoskeletal gait.
- The equilibrium-point hypothesis is actively contested (Mangalam & Stergiou 2026, Exp Brain Res, doi 10.1007/s00221-026-07242-9, plus a published comment and reply). Present lambda control as a control representation, not as evidence about the nervous system.

### Should-read

- **Running Speed is Maximized by Strengthening the Hip Flexors and Hip Adductors** 🆕 — Yang, Lin, Pandy. Annals of Biomedical Engineering (online 26 May 2026). doi:10.1007/s10439-026-04184-9 · [link](https://doi.org/10.1007/s10439-026-04184-9)
  - *Idea.* Full-body musculoskeletal dynamic optimisation ranks how much each leg muscle's strength drives maximum sprint speed. A 10% hip-strength gain adds 2.59% speed, mainly through step frequency, against 1.02% for the ankle and 0.33% for the knee. Hip flexors are the most sensitive group.
  - *Take from it.* Shows why the no-strength-increase rule matters and where assistance has the most leverage: hip flexion. This agrees with Lambda-Hold's finding that hip-flexor force-velocity limits its top speed.
  - *Left untested for this programme.* Uses optimal control, not a learned controller, and varies strength rather than adding external hip torque. Covers top speed only, not a 200 m race with acceleration and fatigue.
  - *On our server.* No compute. Use as a prior on exosuit torque direction and to sanity-check simulated sensitivities.
  - *Code and assets.* No code (dynamic-optimisation study).
- **MuscleVAE: Model-Based Controllers of Muscle-Actuated Characters** — Feng, Xu, Liu. SIGGRAPH Asia 2023 Conference Papers. arXiv:2312.07340 · doi:10.1145/3610548.3618137 · [link](https://arxiv.org/abs/2312.07340) · [code](https://github.com/wangchek/MuscleVAE_)
  - *Idea.* A full-body Hill-type character carries 3CC-r fatigue in every muscle. The policy sets per-muscle target lengths that PD servos track. A VAE skill latent is trained model-based on about 25 min of motion capture, including running, and motion style shifts as fatigue builds and recovers.
  - *Take from it.* Two precedents. First, a learned length-referent action space (lambda-like; not cited by Lambda-Hold). Second, full-body 3CC-r fatigue in which running weakens, then recovers during walking or standing.
  - *Left untested for this programme.* It imitates motion capture rather than predicting from a minimal reward. Targets are re-set every step with no holds. Fatigue parameters are not calibrated for sprinting, and sprint speed and EMG are not validated.
  - *On our server.* Unoptimised training took about a week on CPU plus an RTX 3090. Borrow the fatigue integration, not the pipeline.
  - *Code and assets.* Released (linked from the project page); GitHub reports no licence; last push 2024-03.
- **Smooth Exploration for Robotic Reinforcement Learning** — Raffin, Kober, Stulp. CoRL 2021 (PMLR 164:1634-1644). arXiv:2005.05719 · [link](https://arxiv.org/abs/2005.05719) · [code](https://github.com/DLR-RM/stable-baselines3)
  - *Idea.* Generalised state-dependent exploration (gSDE) makes action noise a function of policy features, with the noise matrix resampled every n steps. Exploration becomes smooth and temporally consistent, trading performance for smoothness. Tested on PyBullet tasks and three real robots.
  - *Take from it.* This is Lambda-Hold's exploration setting: SAC+gSDE in SB3, resampled every 4 decision steps. Keep it identical for the replication gate and treat sample frequency as a sensitivity parameter.
  - *Left untested for this programme.* No musculoskeletal system was tested. Bolt reports no sprint gain from gSDE. With event-length holds, noise changes per decision rather than per unit time, and that effect is unstudied.
  - *On our server.* Zero cost: one SB3 flag for SAC or PPO.
  - *Code and assets.* Released (MIT) in Stable-Baselines3 via the use_sde and sde_sample_freq options.

### Reference

- **SAR: Generalization of Physiological Agility and Dexterity via Synergistic Action Representation** — Berg, Caggiano, Kumar. Autonomous Robots 48 (2024); presented at RSS 2023. arXiv:2307.03716 · doi:10.1007/s10514-024-10182-4 · [link](https://arxiv.org/abs/2307.03716) · [code](https://github.com/MyoHub/myosuite)
  - *Idea.* Synergies are extracted (PCA, then ICA) from policies trained on simpler tasks and reused as a low-dimensional action representation for harder ones. MyoLeg learns robust locomotion over stairs and hills in 4M steps, where end-to-end RL failed, and generalises zero-shot.
  - *Take from it.* A ready-made MyoLeg synergy action space, and a pipeline for distilling synergies from your own trained runner. It is the MuJoCo counterpart to Park's Hyfydy synergy baseline.
  - *Left untested for this programme.* Terrain locomotion only; no running or sprinting reported. The fixed synergy basis cannot adapt online, and there is no reflex or hold interface. Synergies from slow gaits may miss sprint coordination.
  - *On our server.* Runs in MyoSuite's CPU simulation; SAR adds only a linear map.
  - *Code and assets.* MyoSuite ships a pretrained MyoLeg locomotion SAR (PCA/ICA/normaliser in myosuite/agents/SAR_pretrained) with a tutorial notebook.
- **TempoRL: Learning When to Act** — Biedenkapp, Rajan, Hutter, Lindauer. ICML 2021. arXiv:2106.05262 · [link](https://arxiv.org/abs/2106.05262) · [code](https://github.com/automl/TempoRL)
  - *Idea.* The agent picks an action and also how long to commit to it. A skip-policy learned over skip connections between states repeats the action, which learns up to ten times faster than vanilla Q-learning.
  - *Take from it.* A learned alternative to Lambda-Hold's hand-set GRF trigger: let the policy choose hold length within 0.05-0.15 s. Compare against event-triggered holds on the same step budget.
  - *Left untested for this programme.* Tested on tabular and deep RL benchmarks, not musculoskeletal or contact-rich locomotion. It repeats a frozen action, whereas lambda-holds keep reflexes running. Interaction with SAC entropy tuning is unknown.
  - *On our server.* Adds a small skip-policy head; negligible compute.
  - *Code and assets.* Released (Apache-2.0); last push 2022-03.
- **Once More on the Equilibrium-Point Hypothesis (λ Model) for Motor Control** — Feldman. Journal of Motor Behavior 18(1):17-54, 1986. doi:10.1080/00222895.1986.10735369 · [link](https://doi.org/10.1080/00222895.1986.10735369)
  - *Idea.* The tonic stretch-reflex threshold lambda is the central command. Lambda, the muscle's invariant characteristic and the load together fix an equilibrium point, so one mechanism governs posture and movement. The reflex drives the limb to a load-dependent equilibrium; it does not track a prescribed length.
  - *Take from it.* The theory behind Lambda-Hold's control variable: lambda sets where a muscle starts resisting stretch, not a length target. This matters when interpreting learned lambda sequences or porting them across models.
  - *Left untested for this programme.* Built for single joints and posture, not learning, locomotion or high-speed dynamics. Where lambda commands come from is left open, the 'homunculus' objection raised again in 2026.
  - *On our server.* Theory only. Read the sections on the invariant characteristic and recruitment before fixing lambda bounds.
  - *Code and assets.* Theory paper; no code.

### Already claimed by published work (cite it, compare against it, do not headline it)

- Human-like sprinting from a minimal forward-velocity reward, with lambda thresholds and GRF-event holds in a 90-muscle 3D model (Lambda-Hold, arXiv 2608.17030). Do not headline 'first minimal-reward muscle sprint'.
- Demonstration-free direct-excitation sprinting at elite speed via GPU simulation and FastTD3, with doubled strength (Wang et al., arXiv 2609.11083).
- Maximum-speed running with DEP-RL on MyoLeg (5.44 m/s) and H2190 (6.49 m/s, strengthened) (Schumacher et al., arXiv 2309.02976 appendix).
- Policy-set per-muscle target-length (PD) action space with full-body 3CC-r fatigue (MuscleVAE, SIGGRAPH Asia 2023, arXiv 2312.07340).
- RL residual modulation of reflex gains for muscle-driven walking (arXiv 2609.11733). Synergy action spaces: H2190 (arXiv 2603.10474) and MyoLeg (SAR, arXiv 2307.03716).
- Hip exoskeleton co-adapted with a musculoskeletal human policy across walking, turning, running and backward walking (UniExo, arXiv 2609.19690, 17 Sep 2026). The human is imitation-trained; hardware tested at treadmill speeds.

### Open questions this programme can attack

- No lambda-control or event-held controller has been shown in MuJoCo/MyoLeg. A port with the published reward and five-seed medians would be new evidence in its own right.
- Reflex transmission delays are absent from Lambda-Hold's recruitment law. Their effect on sprint speed and stability, alone or with device torque, is untested.
- Nobody has compared learned or per-muscle hold timing (TempoRL/SDAR-style) with GRF-triggered holds for musculoskeletal running, on both simulation-step and decision-step axes.
- Sprint-calibrated fatigue (3CC-r fitted to about 25 s maximal efforts) inside RL sprinting is untested. The second 100 m is the endpoint where assistance could matter.
- Whether lambda-space holds help or hurt a co-adapting exosuit is unknown: within a hold, reflexes react to device torque without a policy update.
- The sensitivity of MyoLeg sprint speed to MuJoCo contact and joint-limit settings, versus force-based contacts (Bolt's ablation), is unmeasured.


---

## 12. Reproducibility, equivalence testing and honest comparison

**What this literature tells the programme**

- A reproduction of a paper without code is an R1 (description-only) study: when it fails, the cause is hard to locate, so fix fidelity criteria and a positive control before running (Gundersen 2021; Rougier et al. 2017; Luo et al. 2026).
- The Collins-Luo exchange shows how a negative exoskeleton result gets attacked: controller fidelity (fixed torque vs learned policy), gait timing, device mass and whether its penalty was measured separately, and the basis of the plausibility bound. Pre-register a check for each.
- 'Does not reproduce' and 'a simpler controller does the same' are interval claims: TOST or non-inferiority with margins fixed in raw units beforehand. A non-significant difference is inconclusive, not 'same' (Lakens et al. 2018; Mazzolari et al. 2022; Tomek et al. 2026).
- Selection is the main hidden bias: choose configs and checkpoints on tuning seeds, rerun the frozen choice on fresh seeds, and report only that rerun (Patterson et al. 2024; Eimer et al. 2023; Cawley & Talbot 2010).
- Report every seed with bootstrap intervals and robust aggregates; two seed groups of the same algorithm can differ 'significantly' by chance (Henderson et al. 2018; Agarwal et al. 2021).
- Compare arms at equal, declared tuning budgets: conclusions can flip with budget, as Dodge et al. 2019 show and as Patterson et al. 2024's 30-seed SAC-vs-DDPG re-run illustrates.
- Expert teams given identical data still diverge (KneeHub, Nazem et al. 2026): treat between-implementation spread as a floor on reproduction uncertainty and score only on held-out conditions.
- Critics now invoke code-release standards (Heil et al. 2021 gold: one command reproduces everything). Build the paper package from the ledger that way and rerun key results on a second machine with a statistical, not bitwise, tolerance.

### Must-read

- **Hyperparameters in Reinforcement Learning and How To Tune Them** — Eimer, Lindauer, Raileanu. ICML 2023 (PMLR 202:9104-9149). arXiv:2306.01324 · [link](https://proceedings.mlr.press/v202/eimer23a.html) · [code](https://github.com/facebookresearch/how-to-autorl)
  - *Idea.* RL hyperparameters strongly change results, and the best configuration depends on the tuning seed, so tuned incumbents overfit their seeds. HPO tools (DEHB, PBT variants, random search) often beat hand-tuning at lower cost; recommends separate tuning and test seeds and reported search spaces.
  - *Take from it.* Rule: tuning seeds and evaluation seeds are disjoint sets fixed at pre-registration; the runner refuses to report any number computed on a seed that touched tuning or checkpoint selection.
  - *Left untested for this programme.* Single-agent benchmarks (Acrobot, Pendulum, MiniGrid, Brax, Procgen); no co-adapting human and device agents, staged curricula, or equivalence tests between tuned methods.
  - *On our server.* Released sweepers plug into Hydra; random search over a declared space with disjoint seeds is affordable on one GPU.
  - *Code and assets.* released (Hydra sweepers for DEHB and PBT variants); repo archived
- **Equivalence Testing for Psychological Research: A Tutorial** — Lakens, Scheel, Isager. Advances in Methods and Practices in Psychological Science 1(2):259-269, 2018. doi:10.1177/2515245918770963 · [link](https://doi.org/10.1177/2515245918770963) · [code](https://github.com/Lakens/TOSTER)
  - *Idea.* Tutorial on the two one-sided tests (TOST) procedure for rejecting effects as large as a smallest effect size of interest (SESOI). Reviews ways to justify the SESOI, combines equivalence with null-hypothesis tests, and gives worked reporting examples.
  - *Take from it.* Rule: fix the SESOI in raw units (seconds of sprint time, % metabolic cost) before results; verdicts come from the combined TOST and difference-test outcomes; 'not significant' alone never means 'same'.
  - *Left untested for this programme.* Human-sample psychology examples; nothing on random seeds as the replication unit, dependence among runs, or deriving a reproduction margin from an original paper's reported effect.
  - *On our server.* No compute; TOSTER or two one-sided Welch t-tests in Python (90% CI) implement it.
  - *Code and assets.* TOSTER R package by the first author (maintained; last push Sept 2026)
- **The preregistration revolution** — Nosek, Ebersole, DeHaven, Mellor. PNAS 115(11):2600-2606, 2018. doi:10.1073/pnas.1708274114 · [link](https://doi.org/10.1073/pnas.1708274114)
  - *Idea.* Testing predictions on new observations differs from postdiction (explaining data already seen); hindsight bias blurs them. Preregistering research questions and analysis plan before seeing outcomes separates the two; the paper gives strategies for imperfect cases such as preexisting data.
  - *Take from it.* Rule: each queued config carries a timestamped, hashed plan (hypothesis, metric, tolerance, seeds, analysis) frozen before any result; deviations are logged and affected results relabelled exploratory.
  - *Left untested for this programme.* Written for human-subject science; silent on automated agents that generate and queue many hypotheses, and on how many preregistered comparisons a sweep may spend.
  - *On our server.* Pure process: an append-only ledger entry at queue time, checked at report time.
  - *Code and assets.* n/a

### Should-read

- **Beyond “non-significant” results: Why and how to test for practical equivalence** 🆕 — Tomek, Caldwell, Eisner. PNAS 123(33):e2611548123 (published 2026-08-18). doi:10.1073/pnas.2611548123 · [link](https://doi.org/10.1073/pnas.2611548123)
  - *Idea.* Non-significant comparisons (P ≥ 0.05) are routinely misreported as 'no difference'. Explains TOST logic, how it separates practical equivalence from inconclusive evidence, illustrates paired and unpaired comparisons, and introduces a free online equivalence calculator.
  - *Take from it.* Rule: verdicts have three states (equivalent, different, inconclusive), and the runner prints 'inconclusive' when neither test passes; use paired TOST when arms share evaluation seeds.
  - *Left untested for this programme.* Only the abstract was checked; it covers single paired or unpaired comparisons, so multiplicity across sweeps and heavy-tailed seed distributions need other sources.
  - *On our server.* Short read; the calculator can spot-check the runner's TOST implementation.
  - *Code and assets.* free online equivalence-test calculator introduced; URL not checked
- **Deciphering the “Art” in Modeling and Simulation of the Knee Joint: Model Benchmarking** — Nazem, Andreassen, Kim, Moyle, Besier, Halloran, Imhauser, Chokhandre, Schneider, Elmasry, Zaylor, Shelburne, Erdemir, Laz. Journal of Biomechanical Engineering 148(5):051004 (online 2026-02-05, issue May 2026). doi:10.1115/1.4070823 · [link](https://doi.org/10.1115/1.4070823)
  - *Idea.* KneeHub: five expert teams built and calibrated knee models from the same specimen data, then predicted unseen benchmark loadings. Major trends matched, but errors versus experiment (up to 13.5 deg internal-external rotation) and between-team spread were large; modeller decisions matter.
  - *Take from it.* Rule: score the reconstruction only on conditions never used for calibration or tuning (held-out speeds, subjects, tasks) and report between-implementation spread as part of reproduction uncertainty.
  - *Left untested for this programme.* Knee joint mechanics with five teams; not whole-body musculoskeletal RL or exoskeletons, and no statistical criterion (e.g., equivalence margin) for calling a model reproduced.
  - *On our server.* Emulate cheaply: two independent SMAT reimplementations (e.g., two agents working from the same text) give an implementation-spread estimate.
  - *Code and assets.* KneeHub data/model sharing not checked (simtk.org unreachable from this machine)
- **Myths and methodologies: The use of equivalence and non-inferiority tests for interventional studies in exercise physiology and sport science** — Mazzolari, Porcelli, Bishop, Lakens. Experimental Physiology 107(3):201-212, 2022. doi:10.1113/EP090171 · [link](https://doi.org/10.1113/EP090171)
  - *Idea.* Reviews how exercise physiology and sport science test interventions, then walks through designing and analysing equivalence and non-inferiority studies, including margin choice, sample size, analysis and reporting, with worked sport-science examples and recommendations.
  - *Take from it.* Rule: 'a simpler controller does the same' is an equivalence claim and 'SMAT is not worse' a non-inferiority claim; each needs its margin and seed count fixed by a pre-registered power calculation.
  - *Left untested for this programme.* Human-subject trials only; no simulated agents, seeds or sweeps, and no margins for simulated sprint time or co-adaptation metrics.
  - *On our server.* No compute; its margin-justification steps can be pasted into the pre-registration template.
  - *Code and assets.* n/a
- **Reproducibility standards for machine learning in the life sciences** — Heil, Hoffman, Markowetz, Lee, Greene, Hicks. Nature Methods 18(10):1132-1135, 2021. doi:10.1038/s41592-021-01256-7 · [link](https://doi.org/10.1038/s41592-021-01256-7)
  - *Idea.* Proposes graded standards: bronze (data, models and code public), silver (plus one-command dependency install, documented run order, OS and resources, deterministic random components), gold (entire analysis reproducible with one command). Collins et al. cite it against Luo et al.
  - *Take from it.* Rule: target gold. One command rebuilds every reported number and figure from the append-only ledger on a clean second machine, with seeds set, environment pinned and run order recorded.
  - *Left untested for this programme.* Short comment on life-science ML; does not address cross-hardware floating-point nondeterminism in GPU physics, so second-machine checks need a statistical tolerance rather than bitwise equality.
  - *On our server.* Container or lockfile plus a single driver script; the second-machine rerun costs one extra run of each key result.
  - *Code and assets.* n/a
- **The fundamental principles of reproducibility** — Gundersen. Philosophical Transactions of the Royal Society A 379(2197):20200210, 2021. arXiv:2011.10098 · doi:10.1098/rsta.2020.0210 · [link](https://doi.org/10.1098/rsta.2020.0210)
  - *Idea.* Defines reproducibility from the scientific method: four types by what the original team shared (R1 description only, R2 code, R3 data, R4 full experiment) and three degrees (outcome, analysis, interpretation reproducible). The less that is shared, the more a successful reproduction generalises.
  - *Take from it.* Rule: label the SMAT reconstruction an R1 (description-only) study and state the degree each verdict reaches; never claim outcome-reproducible unless numbers match within the pre-set margin.
  - *Left untested for this programme.* Conceptual taxonomy; no statistical test for each degree, and no treatment of partial reproductions or disputes over implementation fidelity such as Collins versus Luo.
  - *On our server.* Zero cost; adopt its vocabulary in verdict templates and the paper package.
  - *Code and assets.* n/a
- **Deep Reinforcement Learning That Matters** — Henderson, Islam, Bachman, Pineau, Precup, Meger. AAAI 2018 (Proceedings of the AAAI Conference on Artificial Intelligence 32(1)). arXiv:1709.06560 · doi:10.1609/aaai.v32i1.11694 · [link](https://doi.org/10.1609/aaai.v32i1.11694) · [code](https://github.com/Breakend/DeepReinforcementLearningThatMatters)
  - *Idea.* Policy-gradient results on MuJoCo swing with random seeds, hyperparameters, network architecture, reward scale, environment and codebase; two seed groups of one algorithm can differ significantly. Calls for significance testing, all-seed reporting and standard protocols; Collins et al. cite it for convergence evidence.
  - *Take from it.* Rule: SMAT and every baseline share codebase, reward scale and network; seed count is fixed before running, and all-seed learning curves with intervals accompany every claim.
  - *Left untested for this programme.* Four algorithms (TRPO, PPO, DDPG, ACKTR) on standard MuJoCo tasks; no musculoskeletal models, human-device coupling, or equivalence tests.
  - *On our server.* Principles only; all-seed plots are free once the ledger stores per-seed curves.
  - *Code and assets.* released (2017 snapshot, unmaintained)
- **On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation** — Cawley, Talbot. Journal of Machine Learning Research 11:2079-2107, 2010. [link](https://jmlr.org/papers/v11/cawley10a.html)
  - *Idea.* Optimising a noisy model-selection criterion overfits it; the resulting degradation can be as large as the differences between learning algorithms, and evaluating on data used for selection gives optimistically biased estimates. Nested protocols, with selection inside each evaluation split, avoid this.
  - *Take from it.* Rule: checkpoints, configs and stopping points are chosen on selection seeds by a pre-declared criterion; reported metrics come only from evaluation seeds never used in any selection step.
  - *Left untested for this programme.* Kernel classifiers with cross-validation on fixed datasets; no RL, no non-stationary co-adaptation, and no guidance on how many candidates a sweep may compare.
  - *On our server.* Costs only the held-out evaluation episodes; enforce with seed-set bookkeeping in the ledger.
  - *Code and assets.* n/a

### Reference

- **Show Your Work: Improved Reporting of Experimental Results** — Dodge, Gururangan, Card, Schwartz, Smith. EMNLP-IJCNLP 2019, pp. 2185-2194. arXiv:1909.03004 · doi:10.18653/v1/D19-1224 · [link](https://doi.org/10.18653/v1/D19-1224) · [code](https://github.com/allenai/show-your-work)
  - *Idea.* Test-set scores alone mislead; report expected validation performance of the best-found model as a function of computation budget (hyperparameter trials or training time). Several published comparisons would reverse with more or less compute; ends with reporting best practices.
  - *Take from it.* Rule: equal-budget comparisons. Log every trial, plot expected best performance against number of trials for SMAT and each baseline, and compare arms at the same declared budget.
  - *Left untested for this programme.* NLP models with validation sets; RL returns are noisy per seed, and the estimator assumes i.i.d. trials, which staged or population-based tuning violates.
  - *On our server.* Computed from the trial log; no extra runs.
  - *Code and assets.* released (2019, unmaintained)
- **Sustainable computational science: the ReScience initiative** — Rougier, Hinsen, Alexandre, Arildsen et al.. PeerJ Computer Science 3:e142, 2017. arXiv:1707.04393 · doi:10.7717/peerj-cs.142 · [link](https://doi.org/10.7717/peerj-cs.142) · [code](https://github.com/ReScience)
  - *Idea.* Introduces ReScience, a GitHub-hosted journal for independent open-source re-implementations of published computational studies from their description. Submissions explain why they replicated or failed; two reviewers test and evaluate the code; editors note authors rarely submit failed replications.
  - *Take from it.* Rule: the paper package is a replication report: original claims, every reimplementation decision filling gaps in the description, all outcomes including failures, and runnable code; partial replications must be justified.
  - *Left untested for this programme.* Publication workflow, not statistics; what counts as 'similar enough to be considered equivalent' is left to each field.
  - *On our server.* ReScience C and MLRC 2026 (TMLR proceedings, NeurIPS track) both accept failed reproductions; plausible venues for the final package.
  - *Code and assets.* journal infrastructure on GitHub (continued as ReScience C)

### Already claimed by published work (cite it, compare against it, do not headline it)

- Collins et al. 2026 (preprint) already report a failed N=10 hardware replication of Luo et al. 2024's walking torque profile plus an energy-ratio implausibility argument; cite it, do not headline 'simulation-learned exoskeleton gains fail to replicate' as new.
- Luo et al. 2026 already argue that energy ratios above 4 occur in prior devices and that fixed-torque replications do not test learned policies.
- Henderson et al. 2018, Colas et al. 2018, Agarwal et al. 2021 and Patterson et al. 2024 already establish that few-seed deep-RL comparisons are unreliable and how reporting should change.
- Eimer et al. 2023 already show that RL hyperparameters overfit the tuning seeds and that tuning and test seeds must be separated.
- Patterson et al. 2024 already re-ran a published RL comparison (SAC vs DDPG, 30 seeds) and reached different conclusions from the original.
- KneeHub (Andreassen et al. 2023; Nazem et al. 2026) already quantified multi-team divergence when modelling the same knee data.

### Open questions this programme can attack

- No independent, pre-registered reproduction of a musculoskeletal-RL human-exoskeleton co-adaptation method (SMAT or similar) was found; a TOST-based SMAT reproduction with positive and negative controls would be new.
- No plausibility bound exists for simulated sprint-time gains analogous to the walking energy-ratio argument; deriving one (device work vs time saved) is open and cheap in simulation.
- No field consensus on equivalence margins for simulated metabolic cost or sprint time; the programme must justify its own (e.g., from the original effect size or the simulator's seed-to-seed noise floor).
- No accepted criterion for declaring an RL reproduction failed when the original reports few seeds or no variance; small-telescopes-style rules (Simonsohn 2015) have not been tested on RL.
- RL evaluation guides do not address multiplicity control for an unattended agent running many pre-registered tests (alpha spending across a queue).
- Second-machine reproduction of GPU physics plus RL has no standard tolerance; the programme must pre-set one (e.g., TOST between machines on the key metric).


---

## Appendix: items that could not be verified, and verification notes

**smat_uniexo_line**

- Luo et al. 2026 reply's statement that 'executable code, raw experimental data, and simulation files' were released: no URL in the preprint, no new IntelligentRobotLearning repository (last push 2025-06-03), and the Nature code statement still points to the pseudocode repo (checked 2026-09-23).
- Luo reply's 'Zhou et al. (2025), ~20% during running': the cited ROBIO 2025 paper (10.1109/ROBIO66223.2025.11377519) abstract reports walking reductions of 14.1/12.5/15.7% at 1.0/1.25/1.5 m/s in 3 participants; the running figure could not be checked (paywalled). Not included in papers.
- Luo reply's 'Barati et al. 22.5% maximum': the RA-L abstract gives only mean reductions (15.2% LSTM-PPO, 11.0% MLP-PPO); full text paywalled.
- SMAT IROS 2026 acceptance and SMAT-ext 'IEEE, under review' come from the authors (arXiv comment on 2608.00715, homepage bibliography); not yet in IEEE Xplore (IROS runs 27 Sep-1 Oct 2026).
- SMAT-ext 'Ctrl-B' (a learning controller with a muscle-metabolic-energy reward, tested in the same session at matched ~12 Nm): results deliberately withheld for a future study.
- Seed metadata corrections: both dispute preprints carry openRxiv DOI prefix 10.64898, not 10.1101 (10.64898/2026.04.01.715109 posted 2026-04-06; 10.64898/2026.06.16.731058 posted 2026-06-17). SMAT IROS author order is Yuan, Androwis, Zhou; Jakob Wolf is added on 2608.00715 and 2609.19690.
- GitHub name collision: lucifer1642/uniexo is an unrelated Next.js app; no UniExo code repository exists (checked 2026-09-23).
- IntelligentRobotLearning/Zero_shot_learning_for_human_robot_interaction (DART C++ plus PyTorch teacher/student, CoP/COM/torque rewards, no skeleton, muscle or motion assets, last push 2024-04-23) is not linked from any paper checked; which publication it supports is unconfirmed (it does not match the Nature 2024 pseudocode).

**frontier_sweep_2026**

- 'Predictive Timing Optimization of Hip Exoskeleton Assistance in Running' (Foggetti, Moncelli, Shafi, Trigili, Crea; BioRob 2026, 10.1109/BioRob66782.2026.11681147): title and venue confirmed via Crossref, but no abstract in Crossref or OpenAlex and IEEE Xplore blocked automated access. Content not assessed; possibly relevant to O3.
- 'Using Game Theory to Model Human-Exoskeleton Co-Adaptation' (Siavashani, Arami, McPhee; BioRob 2026, 10.1109/BioRob66782.2026.11681787): title confirmed via Crossref; abstract inaccessible; content not assessed.
- 'A Co-Simulation Platform for Closed-Loop Evaluation of Human-Exoskeleton Control Strategies' (Shakourisalim et al.; BioRob 2026, 10.1109/BioRob66782.2026.11681699): title confirmed via Crossref; abstract inaccessible; possibly relevant to O2.
- 'A Comparison of Four Methods for Predictive Musculoskeletal Simulations of Human Walking' (Denayer, De Pauw, Verstraten; BioRob 2026, 10.1109/BioRob66782.2026.11681138): title confirmed via Crossref; abstract inaccessible; possibly relevant to simulation-reproducibility audits.
- 'Continual Reinforcement Learning for Walking Control in a Musculoskeletal Simulation of Hemiparesis' (Jones, Young, Uhlrich, Pilarski, Dalrymple; BioRob 2026, 10.1109/BioRob66782.2026.11681004): title confirmed via Crossref; abstract inaccessible.
- 'Finite-Time Robust Control for Bowden Cable-Driven Exoskeletons With Time-Varying Cable Configurations' (IEEE TCST 2026, 10.1109/TCST.2026.3713361): title seen in a Crossref search; the DOI record request failed and OpenAlex has no abstract. Possibly relevant to cable-actuator limits.
- bioRxiv 10.64898/2026.03.30.715312 ('Can predictive simulations provide insights for personalizing assistive wearable device design?') is marked WITHDRAWN in v2 (2026-08-06); do not cite.
- A web-search summary of the Luo reply mentions 'Zhou et al. (2025, ~20% during running)' for learning-in-simulation; not verified and outside the window.
- Semantic Scholar returned HTTP 429 on every attempt, so its index was not searched. Coverage relies on arXiv, Crossref, OpenAlex and bioRxiv; ICRA/IROS 2026 proceedings were not yet in Crossref.

**musculoskeletal_sims_rl**

- MyoChallenge 2023 written report (search results show OpenReview forum 3A84lx1JFh, 'MyoChallenge 2023: Towards Human-Level Dexterity and Agility'): the OpenReview API and page returned a verification challenge; only the NeurIPS 2023 competition page (neurips.cc/virtual/2023/competition/66584) was seen, so a report's authors and venue are unconfirmed. Not listed in papers.
- Hyfydy (Geijtenbeek): no paper or preprint found; it is closed, licensed simulation software (hyfydy.com) documented only through the sconegym and depRL READMEs, so it is covered under the SCONE entry rather than listed as a paper.

**gpu_batched_physics**

- MuJoCo Warp technical report or paper: none found (arXiv title search 'MuJoCo' AND 'Warp' returned 0; web search shows it is cited as a GitHub project).
- Dedicated MJX paper: none found; MJX is documented only (MuJoCo Playground builds on it).
- Newton physics engine paper: none found; only the repository (v1.6.0, 2026-09-10), Isaac Lab paper section 7.1 and the Kamino solver paper (arXiv 2603.16536).
- NVIDIA Warp archival paper: none found; it is commonly cited as a 2022 GTC talk (Macklin), which was not verified.
- 'MyoSuite 3.0 -- A multimodal platform for efficient and scalable musculoskeletal motor control' (arXiv 2026): cited in the ms3 README with placeholder DOI and URL; not on arXiv as of 2026-09-23.
- UniExo code: paper says it will be made publicly available; no repository found.
- GPUSimBench benchmark code or project website: announced in the paper; no link found.
- MuJoCoUni (arXiv 2605.24922) package 'mujoco-uni': not found on PyPI or by GitHub search (paper itself verified; not selected).
- That GitHub user Fitz-Yuan is a UniExo author: the profile has no name; the fork itself is verified identical to upstream.

**marl_shared_critic_partners**

- No seed failed verification: all 11 seeds resolved on the arXiv API on 2026-09-23 with matching titles. The MAPPO arXiv title has a comma ('Cooperative, Multi-Agent') that the NeurIPS/Crossref title (doi 10.52202/068431-1787) lacks.
- Seeds verified but not selected (16-entry cap): MADDPG (1706.02275, NeurIPS 2017; CTDE origin, off-policy, covered by MAPPO and Lyu), COMA (1705.08926, AAAI 2018, doi 10.1609/aaai.v32i1.11794; counterfactual per-agent baseline, a possible exo-credit diagnostic) and Luck et al. (1911.06832, CoRL 2019; morphology-controller co-adaptation, tangential to Phase 1).
- Assistax first appeared 2025-07-29 (v1). v2 (2026-06-02) and v3 (2026-07-21) are the RLC 2026 versions, so published_after_2026_04 is false.
- Sun et al. (MBEC 2026): title, authors and date verified on Crossref and the Springer page, and the abstract was read. The full text is paywalled and was not read, and no code statement was seen.
- Wu et al. (NeurIPS 2022): verified on the NeurIPS proceedings page and in the PDF (method and evaluation sections read). No arXiv version and no code link were found.
- An et al., DAMMRL, IEEE TNNLS 2026 (doi 10.1109/tnnls.2026.3685832): title and authors from Crossref, abstract from OpenAlex. The IEEE page was blocked, so the method details are unverified. Not selected.
- UniExo (2609.19690): the shared critic with one PPO update, the frozen-human predictor stage and the absence of held-out-partner evaluation were confirmed in the arXiv HTML. The code is 'to be made publicly available' and no repository was found. Not selected here because the adjacent-SOTA cluster covers it.
- WebSearch summaries dated AssistMimic (2603.11346) to April 2026 and Assistax to July 2026. The arXiv records show 2026-03-11 (CVPR 2026) and 2025-07-29 respectively, and the arXiv dates were used.
- Semantic Scholar citations of 2603.07618 returned HTTP 429 twice. Citations of 2608.00715 surfaced only UniExo.
- FCP, Nekoei et al., ACPO and Wolski et al.: no official code link was found in the papers or on GitHub (2026-09-23).

**motion_imitation_rewards**

- The Development of Joint Kinematics, Kinetics and Electromyography Activity over 50 m Sprints in Experienced Sprinters (MDPI, 2026; surfaced by WebSearch): publisher page returned HTTP 403 and Europe PMC had no record, so data availability is unknown; not listed.
- Arnold et al. 2013, 'Simulated muscle fiber lengths and velocities during walking and running' (SimTK, per the awesome-biomechanics list): lead only, project page not opened.
- Link between AddBiomechanics source 'Carter et al. 2023' (50 subjects, 21.6 h) and the Bath runners dataset (10.15125/BATH-01341; 50 runners, CC BY 4.0, ~28.9 GB, speeds relative to each runner's easy pace; verified via DataCite): plausible but not confirmed.
- Contents of Dorn 2012 RunningDataModels.zip (GRF present? full strides?): SimTK download page timed out twice; project page, licence, size and speeds were verified.
- Licence of Zenodo 6457662: DataCite lists Creative Commons Attribution 3.0 Netherlands, but the WebFetch summary of the record page named no licence and the Zenodo API returned 403; treat as CC BY 3.0 NL pending a direct check.

**sim_to_real_exo_control**

- {'item': 'Luo et al. 2026 claim that executable code, raw experimental data and simulation files were released', 'reason': 'No destination found: IntelligentRobotLearning GitHub org has no repo newer than 2025-06-03, no relevant Zenodo record; the KB audit found the bioRxiv Data/Code tab links only the critique.'}
- {'item': "'Zhou et al. 2025, ~20% metabolic reduction during running' (cited in Luo 2026 as independent evidence)", 'reason': "The only Zhou 2025 reference is ROBIO 2025 (10.1109/ROBIO66223.2025.11377519), whose abstract reports treadmill walking at 1.0-1.5 m/s, n=3, 12.5-15.7%; the 'follow-up paper' is not referenced."}
- {'item': 'Barati 2026 per-subject energy ratios (4.95, 4.63, 4.52, 4.35), 17.3 W mean positive power and 9.8 Nm mean peak torque', 'reason': 'Quoted in Luo 2026; RA-L full text paywalled and these values are not in the abstract.'}
- {'item': 'Lim 2019 DOFC metabolic effect size', 'reason': 'TRO full text paywalled; abstract gives none; Luo 2026 cites both ~19.8% and 21% at 10.9 Nm.'}
- {'item': 'Exact equations for MDOFC harmonics (Yoon 2026), velocity-modulated spring coefficients (Zhang 2026) and Powell Eq. 1', 'reason': 'Equations are images or the IEEE PDF was blocked; only prose descriptions were read.'}

**hilo_coadaptation_theory**

- No seed was unverifiable: all 13 named seeds resolved to arXiv, Crossref or bioRxiv records whose titles matched (2026-09-23). The notes below are verification notes, not failures.
- Seed correction, Kim et al. 2017: the paper is PLOS ONE 12(9):e0184054 (doi 10.1371/journal.pone.0184054), not J NeuroEng Rehabil. Its title, 'Human-in-the-loop Bayesian optimization of wearable device parameters', was confirmed. It compares BO with gradient descent on step frequency in unaided walking, not hip-exosuit parameters. Verified but not selected; Ding 2018 covers hip HILO.
- Seed correction, Kim & Sergi 2026: the DOI is 10.64898/2026.06.10.731447 (bioRxiv's 2026 prefix). The 10.1101 form returns 'no posts found' from the bioRxiv API and 404 from Crossref.
- Guo CaMDP: the arXiv 2305.02058 precursor was verified. The final Knowledge-Based Systems 291:111572 (2024) record, 'Cooperative Markov Decision Process model for human-machine co-adaptation in robot-assisted rehabilitation' (doi 10.1016/j.knosys.2024.111572), was confirmed through Crossref. Its full text is closed and was not read, and equivalence with the precursor is not established.
- Verified but not selected because of the 16-entry cap, and cited in occupied_claims instead: Slade et al. 2022 Nature 610:277-282 (doi 10.1038/s41586-022-05191-1) and Li et al. 2019 Nat. Mach. Intell. 1:36-43 (doi 10.1038/s42256-018-0010-3).
- No 2024-2026 HILO or co-adaptation study of running or sprinting with a hip device was found (WebSearch plus OpenAlex filtered to 2024 onward, 2026-09-23). This is a search result, not proof of absence.
- Slade et al. 2024: nature.com redirected to a login page, so the entry rests on the verified abstract only. Chasnov et al. 2025: Code Ocean capsule 6746258 returned HTTP 403 to a script; its existence is taken from the paper's Data availability statement.
- Process note: 9 WebSearch calls were made against a budget of 8. Every identifier in this file was confirmed by API (arXiv, Crossref, bioRxiv, PubMed, Semantic Scholar, GitHub), not taken from search snippets.

**sprint_biomech_exosuits**

- Seed URL hcr.yonsei.ac.kr/team/alchemist/dash_2024.html: HTTP 404 and no Wayback Machine capture (checked 2026-09-23). The DASH programme itself was verified at https://hcr.yonsei.ac.kr/research/Human-Robotic-Mobilities/ALC/ (page title 'DASH | Human-Centered AI Robotics Lab'). It is listed under occupied_claims rather than papers because it reports no data.
- Seed 'Haugen et al. 2019 sprint running review (Sports Med)': no 2019 Haugen record in Sports Medicine was found. Two 2019 Haugen reviews were verified instead, 'Sprint running: from fundamental mechanics to practice—a review' (Eur J Appl Physiol 119:1273–1287, 10.1007/s00421-019-04139-0) and 'The Training and Development of Elite Sprint Performance…' (Sports Medicine - Open 5:44, 10.1186/s40798-019-0221-0). Neither was selected.
- Seed 'Schache et al. 2011 hip muscle contributions': the only matching 2011 record is 'Effect of Running Speed on Lower Limb Joint Kinetics' (MSSE 43(7):1260–1271, 10.1249/mss.0b013e3182084929), which reports joint kinetics, not muscle contributions. Muscle-level contributions are in Dorn et al. 2012 (selected). Verified, not selected.
- Seed 'MyoSuite fatigue model': no standalone MyoSuite fatigue paper was found. The implementation (myosuite/envs/myo/fatigue.py, CumulativeFatigue, 3CC-r adapted from Cheema et al. CHI 2020, 10.1145/3313831.3376701) was verified in code and is recorded under Looft et al. 2018.
- Moon et al. supplement Table S4: the Zenodo description lists Tables S1–S4, but the KB's local supplement has S1–S3. Zenodo file access returned HTTP 403 (rate limit), so the content of any Table S4 is unverified.
- Kim et al. 2019 exosuit hardware parameters (mass, peak force, actuator specs) could not be read (paywalled full text). Only the abstract numbers (−9.3% walking at 1.5 m/s, −4.0% running at 2.5 m/s) were verified, and none of the hardware figures were used.

**physiology_grounded_control**

- Excluded, WITHDRAWN: Kobayashi, bioRxiv 10.64898/2026.05.01.722167 (ablation of an equilibrium-point controller in a 34-muscle arm). Withdrawn 2026-05-18 for a flaw in its lambda recipe (no gravity compensation); the author asks that it not be cited.
- Caveat, not a failed seed: Schumacher et al.'s maximum-running speeds come from the arXiv v2 appendix (Table III). Whether the iScience 2025 version keeps that appendix was not checked.
- Could not retrieve: citing papers for Lambda-Hold. Semantic Scholar and OpenAlex both reported 0 citations on 2026-09-23, and the S2 citations endpoint was rate-limited. A follow-up published after indexing could be missed.

**reproducibility_methods**

- Seed 'any 2023-2026 reproducibility study in musculoskeletal RL': none found via Crossref, OpenAlex and three web searches; the nearest are Collins et al. 2026 (exoskeleton control) and KneeHub 2026 (knee modelling). Absence is not proven.
- Independent learning-in-simulation exoskeleton results cited by Luo et al. 2026 (Barati et al. 2026 RA-L; Zhou et al. 2025; Park et al. 2026; others) were not verified; they are related methods, not replications.
- Luo et al. 2026 state that Collins et al. was submitted to Nature as a Matters Arising in December 2025 and was under review when posted; this comes from one party and was not independently confirmed.
- Tomek et al. 2026: only the Crossref record and abstract were seen; the calculator URL and full text were not checked.
- Tool limits: Semantic Scholar returned HTTP 429 and DBLP and proceedings.mlsys.org were unreachable by curl; the MLSys 2021 listing for Bouthillier et al. was confirmed through WebFetch instead.

