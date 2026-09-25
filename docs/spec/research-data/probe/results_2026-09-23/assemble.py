"""Assemble gpu_probe_2026-09-23.json and .log from $PROBE/results (system python3, stdlib only)."""
import json
import os
import subprocess
from pathlib import Path

PROBE = Path(os.environ["PROBE"])
R = PROBE / "results"
J = lambda f: json.loads((R / f).read_text())  # noqa: E731
L = lambda f: [json.loads(x) for x in (R / f).read_text().splitlines() if x.strip()]  # noqa: E731
T_TOTAL = 547e6

compose = J("compose_report.json")
stats = J("model_stats.json")
rss = L("cpu_rss.jsonl")
single = {r["model"]: r for r in L("cpu_single.jsonl")}
single_nm = {r["model"]: r for r in L("cpu_single_nomulticcd.jsonl")}
scale = J("scale_human_plus_hippo.json")
w_sup0 = J("warp_support_stock_only.json")
w_sup = J("warp_support.json")
w_main = J("warp_main.json")
w_p2 = J("warp_parity2.json")
flag_eff = J("cpu_flag_effect.json")
det = J("warp_determinism.json")
ts_log = (R / "testspeed_hippo_8192.log").read_text()


def ts_val(key):
    for line in ts_log.splitlines():
        if line.startswith(key):
            return line.split(":", 1)[1].strip()
    return None


gpu_checks = []
for i in range(1, 7):
    p = R / f"gpu_check_{i}.txt"
    if p.exists():
        gpu_checks.append(p.read_text().strip().splitlines())

# ---------------- model stats
model_stats = {}
for name in ("human", "human_plus_hippo"):
    s = dict(stats["models"][name])
    c = compose["models"][name]
    s["compose"] = dict(
        pipeline=("myoassist_utils.compose.compose_env_model('myolegs26', 'Hippo_L1', terrain=None) (flat default ground, feet seated)"
                  if name == "human_plus_hippo" else
                  "same MyoAssist _compose_env_model pipeline with assist_sim.load_msk swapped in-process for load_combined (no device)"),
        export="self-contained XML + copied mesh assets; verified: identical fingerprint and bitwise-identical 300-step rollout vs compose string",
        xml_sha256=c["xml_sha256"], n_asset_files=c["export"]["n_asset_files"], asset_mb=round(c["export"]["asset_bytes"] / 2**20, 1),
        compose_s=c["compose_s"])
    model_stats[name] = s

# ---------------- cpu native
rss_tab = {}
for r in rss:
    rss_tab.setdefault(r["model"], {})[r["loaded_from"]] = dict(
        rss_mb_after_1000_steps=r["after_1000_steps"]["VmRSS"], pss_mb=r["after_1000_steps"]["Pss"],
        uss_mb=r["after_1000_steps"]["USS"], rss_mb_after_import_only=r["after_import"]["VmRSS"],
        rss_mb_after_model_load=r["after_mjmodel"]["VmRSS"], rss_mb_after_malloc_trim=r["after_malloc_trim"]["VmRSS"],
        mjmodel_buffer_mb=r["mjmodel_nbytes_mb"], mjdata_buffer_mb=r["mjdata_nbytes_mb"])
cpu_native = dict(
    mujoco="3.14.0 (fresh venv)", python="3.12.3",
    protocol=("mj_step, 1 thread (OMP etc.=1), nice 10; start qpos0 (seated), smooth random excitation "
              "u<-u+0.3*(U(lo,hi)-u) once per 20 ms control step (muscles [0,1], Exo_R/Exo_L [-1,1]), zero-order hold "
              "over substeps=round(0.02/0.002)=10; reset to qpos0 every 50 control steps (1 s; random excitation makes "
              "the model fall in ~0.9-1.0 s). Stock model flags (MuJoCo 3.14 default: MULTICCD on)."),
    single_thread_steps_per_s={k: single[k]["steps_per_s"] for k in single},
    control_transitions_per_s_single={k: single[k]["control_transitions_per_s"] for k in single},
    single_thread_with_multiccd_disabled=dict(
        steps_per_s={k: single_nm[k]["steps_per_s"] for k in single_nm},
        control_transitions_per_s={k: single_nm[k]["control_transitions_per_s"] for k in single_nm},
        note="same 1-flag change the Warp runs need; used for the apples-to-apples GPU/CPU ratio"),
    timing_window_s={k: single[k]["elapsed_s"] for k in single},
    mean_contacts_at_control_steps={k: single[k]["mean_ncon_at_control_steps"] for k in single},
    rss_mb_per_env=rss_tab,
    rss_note=("one fresh process = interpreter + numpy + mujoco + 1 MjModel + 1 MjData. Loading from XML leaves ~400 MB "
              "extra resident for human_plus_hippo (the 8 Hippo meshes have 251k vertices / 502k faces; malloc_trim does "
              "not release it); loading a precompiled MJB (mj_saveModel) avoids it. Real RL workers add gym/myosuite/torch on top."),
    scaling=[{k: v for k, v in s.items() if k not in ("worker_errors",)} for s in scale],
    scaling_note=("human_plus_hippo, N concurrent single-threaded processes, each loads the MJB (to keep 32 procs at ~5 GB "
                  "instead of ~18 GB), 30 s synchronized window, nice 10; machine: AMD EPYC 9535 64C/128T, 1 NUMA node; "
                  "background load avg ~1.2-1.4 before the runs."),
)

# ---------------- warp
tp = w_main["throughput"]
per_nworld = {}
for name, runs in tp.items():
    per_nworld[name] = [
        {k: r.get(k) for k in ("nworld", "steps_per_s", "control_transitions_per_s", "sync_each_ctrl_step_steps_per_s",
                               "sync_each_ctrl_step_control_transitions_per_s", "timed_control_steps", "timed_s",
                               "gpu_mem_mb_process_steady", "data_array_bytes_mb", "put_data_s", "graph_capture_s",
                               "stats_ncon_per_world_mean", "stats_nefc_mean", "stats_nefc_max", "stats_solver_iter_mean",
                               "stats_solver_iter_max", "overflow_flags", "nonfinite_worlds", "realtime_factor_per_world",
                               "skipped", "error")
         if k in r}
        for r in runs]
stock_err = {n: w_main["put_model"][n]["stock"].get("error") for n in ("human_plus_hippo", "human")}
stock_warn = {n: w_main["put_model"][n]["stock"].get("warnings") for n in ("human_plus_hippo", "human")}
stock_err_first_attempt = {n: w_sup0["put_model"][n].get("error") for n in ("human_plus_hippo", "human")}
assert all(stock_err_first_attempt[n] and "MULTICCD" in stock_err_first_attempt[n] for n in stock_err_first_attempt)
wa = {n: {k: v for k, v in w_main["put_model"][n]["workaround_disable_multiccd"].items() if k != "error"}
      for n in ("human_plus_hippo", "human")}
fs = w_sup["first_step"]
hip_tp = {r["nworld"]: r for r in tp["human_plus_hippo"] if "steps_per_s" in r}
warp = dict(
    supported=False,
    supported_with_workaround=True,
    workaround=("mjm.opt.disableflags |= mjDSBL_MULTICCD (MJCF: <option><flag multiccd=\"disable\"/></option>). "
                "Named in the error text itself. Only changes how many contacts mesh-mesh / box-mesh pairs produce "
                "(1 instead of several); foot-plane contacts are unaffected. Applied to BOTH the Warp model and the CPU "
                "reference in parity. Alternative from the same error text: zero the 1 mm geom margins (23 of 31 colliding "
                "geoms), which would also change foot-ground contact activation, so it was not used."),
    errors=stock_err,
    stock_warnings=stock_warn,
    unsupported_features_found=[
        "mesh-mesh (and box-mesh) collision pairs with non-zero geom margin while MULTICCD is enabled "
        "(MuJoCo 3.14 enables MULTICCD by default; model geoms carry margin=0.001)",
        "CAPSULE-MESH pairs have no multicontact support under MULTICCD (warning only: at most 1 contact per pair)",
    ],
    everything_else_loaded=("with the flag: 26 muscles (mjDYN_MUSCLE/mjGAIN_MUSCLE, tendon transmission), 26 spatial tendons "
                            "with 96 site wraps, 28 mjEQ_JOINT polynomial couplings, 28 slide + 12 hinge + 1 free joint, "
                            "25 explicit mesh-mesh pairs, 12 sensors, Euler/Newton/pyramidal: all accepted by put_model"),
    put_model_with_workaround=wa,
    compile_s=dict(
        cold_first_step_jit_s=fs["human_plus_hippo"].get("first_step_s_incl_jit"),
        second_model_first_step_s=fs["human"].get("first_step_s_incl_jit"),
        note=("cold = empty Warp kernel cache (WARP_CACHE_PATH inside the probe dir); human reused the same kernels. "
              "A later process with warm cache reached its first parity step within ~3 s. The mjwarp-testspeed CLI run "
              f"re-JITed ({ts_val('Total JIT time')}) for its own configuration."),
        graph_capture_s_per_nworld={r["nworld"]: r.get("graph_capture_s") for r in tp["human_plus_hippo"] if "nworld" in r},
    ),
    per_nworld=per_nworld,
    method=("same protocol as CPU (qpos0 start, smooth random excitation per 20 ms control step generated on-GPU, reset "
            "via mjw.reset_data every 50 control steps); one CUDA graph = 10 x mjw.step; timed 100 control steps "
            "(1000 physics steps/world) without host sync inside the loop; a second variant syncs the host after every "
            "control step (RL-loop-like). nconmax=48/world, njmax=160/world (CPU max observed nefc=106); no overflow "
            "flags, no non-finite worlds. Monitor saw no other GPU process during this sweep."),
    gpu_mem_mb=dict(
        process_peak=w_main["gpu_mem_mb_process_peak"],
        process_steady_by_nworld_human_plus_hippo={n: r["gpu_mem_mb_process_steady"] for n, r in hip_tp.items()},
        data_arrays_mb_by_nworld_human_plus_hippo={n: r["data_array_bytes_mb"] for n, r in hip_tp.items()},
        note="process total from nvidia-smi (CUDA context + Warp mempool + graphs); human runs followed hippo runs in the same process, so their process numbers include retained pool memory",
    ),
    testspeed_crosscheck=dict(
        cmd=("mjwarp-testspeed human_plus_hippo_nomulticcd.xml --nworld=8192 --nstep=500 --nconmax=48 --njmax=160 "
             "--keyframe=-1 --measure_alloc --memory"),
        total_steps_per_s=ts_val("Total steps per second"), time_per_step=ts_val("Total time per step"),
        jit=ts_val("Total JIT time"), converged_worlds=ts_val("Total converged worlds"),
        caveats=("1 step per graph launch + host sync per step, zero control (passive collapse), and the other aurnab "
                 "GPU job (93% util, ~1.9 GiB) was active at the check just before it; treat as a conservative lower figure"),
    ),
    device=w_main["device"],
)

# ---------------- parity
p_h = w_main["parity"]["human_plus_hippo"]
p_hu = w_main["parity"]["human"]
p2c = w_p2["parity_contacts_disabled"]
parity = dict(
    summary=(
        "Yes, they diverge chaotically once contacts are involved, and there is also a systematic contact difference. "
        "(1) Systematic: at the identical seated start the contact sets already differ (CPU 10 vs Warp 6 contacts), so "
        "Warp-vs-CPU qpos differs by 8.8e-4 after 1 step and 8e-2 after 10 steps, far ahead of any round-off growth. "
        "(2) Chaotic: with contacts, tiny differences grow ~8 orders of magnitude in ~75 steps (0.15 s): two Warp worlds "
        "given bit-identical inputs start 5e-10 apart (MJWarp is not bitwise deterministic) and reach 1e-2 by step 75; CPU "
        "MuJoCo (bitwise deterministic run-to-run) moves 4e-3 by step 100 from a 1e-7 qpos perturbation. After ~100 steps "
        "Warp-vs-CPU (5e-2 to 1.2e-1), Warp-vs-Warp (1e-2 to 3e-2) and CPU-vs-perturbed-CPU (1e-3 to 5e-3) are within about "
        "an order of magnitude. (3) Without contacts there is no chaotic growth: Warp tracks CPU to 1.9e-4 over 400 steps "
        "(float32 drift) and Warp worlds agree to ~2e-6; muscle activations/tendon lengths/muscle forces match to float32 "
        "precision. Aggregate statistics (contacts/world, constraint rows, Newton iterations) agree closely. First look, not "
        "a verdict: trajectory-level parity is not attainable in this contact-rich regime; distribution-level parity looks plausible "
        "but untested."),
    setup=dict(model="human_plus_hippo (and human)", flags="MULTICCD disabled on both", nworld=p_h["nworld"],
               nsteps=p_h["nsteps"], dt=p_h["dt"], initial_state=p_h["initial_state"],
               control="400-step trace, smooth random excitation changed every 10 steps (50 Hz), float32-rounded, identical on both"),
    human_plus_hippo={k: p_h[k] for k in ("at_step", "first_step_qpos_diff_above", "qpos_maxdiff_series_every10",
                                          "ncon_series_every10", "ncon_first_mismatch_step", "ncon_mismatch_fraction",
                                          "nefc_max", "ncon_max", "warp_cross_world_max_abs_diff", "warp_overflow_flags")},
    human={k: p_hu[k] for k in ("at_step", "first_step_qpos_diff_above", "ncon_first_mismatch_step",
                                "ncon_mismatch_fraction", "warp_cross_world_max_abs_diff")},
    control_initial_contacts=w_p2["initial_contacts"],
    control_contacts_disabled_human_plus_hippo={k: p2c[k] for k in ("at_step", "first_step_qpos_diff_above",
                                                                   "qpos_maxdiff_series_every10")} if "at_step" in p2c else p2c,
    control_cpu_effect_of_multiccd_flag=flag_eff,
    control_determinism=det,
    aggregate_stats_comparison=dict(
        cpu_random_protocol=dict(ncon_mean=stats["models"]["human_plus_hippo"]["character_random"]["ncon_mean"],
                                 nefc_mean=stats["models"]["human_plus_hippo"]["character_random"]["nefc_mean"],
                                 solver_iter_mean=stats["models"]["human_plus_hippo"]["character_random"]["solver_iter_mean"]),
        warp_8192_worlds=dict(ncon_mean=hip_tp[8192]["stats_ncon_per_world_mean"], nefc_mean=hip_tp[8192]["stats_nefc_mean"],
                              solver_iter_mean=hip_tp[8192]["stats_solver_iter_mean"]),
    ),
    interpretation_notes=[
        "At the seated initial pose CPU MuJoCo 3.14 returns 4 contacts per toes-plane pair (2 at -2.33 mm, 2 at +1.53 mm; "
        "both geoms have margin 1.0 mm) while MJWarp returns only the 2 penetrating ones; calcn-plane: 1 each on both. "
        "Constraint rows at step 1: CPU 68 vs Warp 52.",
        "Contact-free: activation diff ~1e-8, tendon length diff <=6e-6 m, muscle force diff <=0.15 N (forces up to 3.4 kN) over 400 steps.",
        "MJWarp is NOT bitwise deterministic: identical worlds (and two separate nworld=1 runs) differ from step 1 at ~1e-10; "
        "with contacts their contact counts differ in 57% of steps and qpos differs by ~1e-2 after 75 steps; the parity run's "
        "warp_cross_world_max_abs_diff (max over qpos/qvel/act/forces/tendon lengths and all 400 steps) is in muscle-force newtons. "
        "CPU MuJoCo repeated runs are bitwise identical.",
    ],
)

# ---------------- estimates (clearly extrapolated)
s32 = next(s for s in scale if s.get("n_procs") == 32)
per_proc_32 = s32["per_proc_control_transitions_per_s"]["mean"]
cpu48 = 48 * per_proc_32
g8192 = hip_tp[8192]["control_transitions_per_s"]
g4096 = hip_tp[4096]["control_transitions_per_s"]
ts_ctrl = int(ts_val("Total steps per second").replace(",", "")) / 10
rss_mjb = rss_tab["human_plus_hippo"]["mjb"]["rss_mb_after_1000_steps"]
rss_xml = rss_tab["human_plus_hippo"]["xml"]["rss_mb_after_1000_steps"]
estimates = dict(
    label="ESTIMATES - extrapolated from the measurements above; physics stepping only",
    pipeline_control_transitions=int(T_TOTAL),
    cpu_48_threads=dict(
        hours=round(T_TOTAL / cpu48 / 3600, 2),
        assumption=(f"48 single-threaded processes each keep the measured 32-process rate ({per_proc_32:.0f} transitions/s/proc, "
                    f"-12.5% vs 1 proc) -> {cpu48:,.0f}/s. Not measured beyond 32 processes."),
        hours_at_measured_32_procs=round(T_TOTAL / s32["aggregate_control_transitions_per_s"] / 3600, 2),
        ram=(f"48 x {rss_mjb:.0f} MB (MJB-loaded) = {48 * rss_mjb / 1024:.1f} GB fits 12 GB; 48 x {rss_xml:.0f} MB (XML-loaded) = "
             f"{48 * rss_xml / 1024:.1f} GB does not (only ~{int(12 * 1024 // rss_xml)} XML-loaded envs fit) -> load the MJB or decimate the Hippo meshes"),
    ),
    gpu_rtx5090=dict(
        hours=round(T_TOTAL / g8192 / 3600, 2),
        basis=f"nworld=8192 measured {g8192:,}/s (human_plus_hippo, MULTICCD disabled, GPU otherwise idle)",
        hours_nworld_4096=round(T_TOTAL / g4096 / 3600, 2),
        hours_testspeed_basis=round(T_TOTAL / ts_ctrl / 3600, 2),
        requires="the 1-flag MULTICCD workaround; accept the contact-level parity gap vs CPU MuJoCo",
    ),
    speedup=dict(gpu8192_vs_1_cpu_thread_same_flags=round(g8192 / single_nm["human_plus_hippo"]["control_transitions_per_s"], 1),
                 gpu8192_vs_32_cpu_procs_measured=round(g8192 / s32["aggregate_control_transitions_per_s"], 2),
                 gpu8192_vs_48_cpu_procs_estimated=round(g8192 / cpu48, 2)),
    excludes=("policy inference, observation/reward code, env wrappers (myosuite/gym), learner updates, host-device "
              "transfers to the learner, and GPU/CPU sharing with other jobs"),
    timestep_caveat=("uses the model XML timestep 0.002 s (10 substeps per 50 Hz transition). MyoAssist's RL env overrides "
                     "opt.timestep = 1/physics_sim_framerate (1000 Hz in code comments, 1200 Hz in the sprint's PPO smoke config): "
                     "20-24 substeps per transition, i.e. roughly 2-2.4x the hours above if cost per physics step is unchanged"),
)

out = dict(
    checked_on="2026-09-23",
    run_window_kst="17:52-18:25 (Asia/Seoul)",
    host=dict(hostname="sail-gpu01", cpu="AMD EPYC 9535 64-Core, 2 threads/core (128 logical), 1 NUMA node",
              ram_gb=30.8, gpu="NVIDIA GeForce RTX 5090 32 GB (sm_120)", driver="595.84 (CUDA 13.2)"),
    gpu_rule_check=dict(
        rule="before any GPU work: no process owned by a non-aurnab account may hold > 1024 MiB",
        checks_raw=gpu_checks,
        result="OK at every check; only aurnab-owned processes were ever on the GPU (ugrp-cl-autoresearch clforge training jobs, bursty, ~1.9-2.3 GiB, up to 93% util)",
        gpu_parts_ran=True,
        gpu_wall_s=dict(support_stock_attempt=w_sup0.get("gpu_wall_s"), support_with_workaround_incl_cold_jit=w_sup.get("gpu_wall_s"),
                        main_parity_and_sweep=w_main.get("gpu_wall_s"), parity_controls=w_p2.get("gpu_wall_s"),
                        testspeed_crosscheck_wall=42.1, determinism_controls=det.get("gpu_wall_s"),
                        total_approx=round(sum(x for x in (w_sup0.get("gpu_wall_s"), w_sup.get("gpu_wall_s"), w_main.get("gpu_wall_s"),
                                                           w_p2.get("gpu_wall_s"), 42.1, det.get("gpu_wall_s")) if x), 1),
                        budget=600),
        own_gpu_mem_peak_mb=max(w_main.get("gpu_mem_mb_process_peak", 0), w_sup.get("gpu_mem_mb_process_peak", 0)),
        other_gpu_processes_seen_by_monitor=dict(support=w_sup.get("other_gpu_processes_seen"), main=w_main.get("other_gpu_processes_seen")),
    ),
    versions=dict(
        compose_env=dict(venv="/home/aurnab/projects/sail-sprint-20260905/.venv (read-only use)", python=compose["compose_env"]["python"],
                         mujoco=compose["compose_env"]["mujoco"], assist_sim=compose["compose_env"]["assist_sim"],
                         myo_sim=compose["compose_env"]["myo_sim"], MyoAssist="1.0.0 editable, git b1baf69da59dc6728515d0977cbc8fbf00b9225a",
                         myoassist_terrains="1.0.0"),
        probe_env=dict(python="3.12.3 (/usr/bin/python3.12 via uv 0.12.7)", packages=[" ".join(x.split()) for x in (R / "pip_list.txt").read_text().splitlines()[3:]]),
        warp_runtime=dict(warp=w_main["device"]["warp"], mujoco_warp=w_main["device"]["mujoco_warp"], mujoco=w_main["device"]["mujoco"],
                          warp_cuda_toolkit=w_main["device"].get("toolkit_version"), cuda_driver=w_main["device"].get("driver_version")),
        note="mujoco-warp 3.14.0 requires mujoco>=3.12.0 and warp-lang>=1.15; latest mujoco 3.14.0 (released 2026-09-22) was used, no pin needed",
    ),
    model_stats=model_stats,
    cpu_native=cpu_native,
    warp=warp,
    parity=parity,
    disk_before_after=dict(before=(R / "disk_before.txt").read_text().strip().splitlines()[-1], probe_peak_size="849M",
                           after=None),
    cleanup_confirmed=None,
    notes=[
        "Stock models do NOT load in mujoco-warp 3.14.0 (exact error in warp.errors); a single option flag (MULTICCD off) makes them load and run.",
        "Throughput: human_plus_hippo reaches 2.35M physics steps/s = 235k control transitions/s at nworld=8192 (3.6 GB GPU); the Hippo device costs ~5-8% vs the bare human on GPU (4.5% at nworld=8192) and ~2-3% on CPU.",
        "Parity: trajectory-level agreement is not attainable with contacts (chaotic growth from round-off; MJWarp is not bitwise deterministic even run-to-run; plus a different contact set from step 1). Contact-free dynamics (muscles, spatial tendons, joint couplings) match to float32 precision. See parity.summary.",
        "CPU: ~20.4-21.0k steps/s per thread (~2.0-2.1k transitions/s); 32 processes give 57.9k transitions/s (87% per-process efficiency).",
        "Memory: human_plus_hippo loaded from XML costs ~560 MB RSS per process (93 MB MjModel, mostly the 8 high-res Hippo meshes, plus ~400 MB retained from compilation); loading a precompiled MJB brings it to ~153 MB.",
        "Composed keyframes are not seated: human_plus_hippo key 'stand' has root z=1.000 while the MyoAssist-seated qpos0 has z=0.913, so resetting to key 0 (what myoassist_leg_base does) starts the model ~8.7 cm above the ground. All runs here start from qpos0.",
        "The composed myolegs26 human has nkey=0; MyoAssist's leg env asserts nkey>0, so the bare human cannot be used there as-is (compose + Hippo adds 5 keyframes).",
        "No <option> element in the composed XML: Euler, Newton (100 it, ls 50, tol 1e-8), pyramidal cone, dt=0.002 s.",
        "Random excitation makes the model fall in ~0.9-1.0 s; workload per step ~6.3-6.7 contacts, ~66 constraint rows, ~1.8 Newton iterations (CPU and Warp agree).",
        "Nothing was written outside the probe dir: ~/.cache, ~/.nv, ~/.local/share and ~ top level unchanged (CUDA_CACHE_PATH, WARP_CACHE_PATH, XDG_CACHE_HOME, UV_CACHE_DIR, TMPDIR, PYTHONPYCACHEPREFIX all pointed inside it; PYTHONDONTWRITEBYTECODE=1 for the sprint venv). "
        "One .pyc in the sprint venv (dm_control/_render/__pycache__/glfw_renderer.cpython-312.pyc) was rewritten at 18:02:03 by another user of that venv; the probe's only use of it ended at 17:57:34 and a check right after showed zero changes; the probe never imports dm_control. "
        "/tmp/pytest-of-aurnab belongs to the other project's pytest run.",
        "mjwarp-testspeed --clear_warp_cache would rmtree ~/.nv/ComputeCache (shared); it was not used.",
    ],
    estimates=estimates,
)
(R / "gpu_probe_2026-09-23.json").write_text(json.dumps(out, indent=2, default=str))

# raw log: concatenate the logs in order
parts = ["compose.log", "stats.log", "cpu_rss.jsonl", "cpu_single.jsonl", "scale.log", "gpu_check_1.txt", "warp_support.log",
         "gpu_check_2.txt", "warp_support2.log", "gpu_background_before_main.csv", "gpu_check_3.txt", "warp_main.log",
         "gpu_check_4.txt", "warp_parity2.log", "gpu_check_5.txt", "testspeed_hippo_8192.log", "cpu_flag_effect.log",
         "cpu_single_nomulticcd.jsonl", "gpu_check_6.txt", "warp_determinism.log", "pip_list.txt", "disk_before.txt"]
with open(R / "gpu_probe_2026-09-23.log", "w") as f:
    f.write("# SMAT sprint GPU feasibility probe, sail-gpu01, 2026-09-23 (KST). Raw logs, in run order.\n")
    for p in parts:
        f.write(f"\n===== {p} =====\n")
        f.write((R / p).read_text())
print("sizes", (R / "gpu_probe_2026-09-23.json").stat().st_size, (R / "gpu_probe_2026-09-23.log").stat().st_size)
print("cross_world", p_h["warp_cross_world_max_abs_diff"], p_hu["warp_cross_world_max_abs_diff"], "overflow", p_h["warp_overflow_flags"])
print("estimates", json.dumps(estimates, indent=1))
