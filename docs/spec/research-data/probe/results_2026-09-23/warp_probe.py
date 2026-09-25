"""MuJoCo Warp probe (fresh venv).

  warp_probe.py support   put_model for both models (+ full error text), first-step JIT (cold compile) at nworld=1
  warp_probe.py main      parity vs CPU MuJoCo (float64) + throughput sweep over nworld

Guards: GPU wall-time budget (GPU_BUDGET_S env), projected GPU memory < MEM_LIMIT_MB for this process,
stop starting new GPU work if a non-aurnab process shows up holding > 1024 MiB.
"""
import gc
import json
import os
import subprocess
import sys
import threading
import time
import traceback

T_START = time.time()
import mujoco as mj  # noqa: E402
import numpy as np  # noqa: E402
import warp as wp  # noqa: E402

wp.config.kernel_cache_dir = os.environ["WARP_CACHE_PATH"]  # explicit, in addition to the env var
wp.config.log_level = wp.LOG_WARNING
import mujoco_warp as mjw  # noqa: E402

from common import ALPHA, EPISODE_CTRL_STEPS, MODELS, PROBE, SmoothCtrl, ctrl_bounds, init_state, substeps  # noqa: E402

MODE = sys.argv[1]
BUDGET_S = float(os.environ.get("GPU_BUDGET_S", "300"))
MEM_LIMIT_MB = 7500
NCONMAX = int(os.environ.get("NCONMAX", "48"))
NJMAX = int(os.environ.get("NJMAX", "160"))
NWORLDS = [int(x) for x in os.environ.get("NWORLDS", "256,1024,4096,8192").split(",")]
PID = os.getpid()
LOG = []


def log(*a):
    s = f"[{time.time() - T_START:7.1f}s] " + " ".join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


def budget_left():
    return BUDGET_S - (time.time() - T_START)


def owner(pid):
    try:
        return subprocess.run(["ps", "-o", "user=", "-p", str(pid)], capture_output=True, text=True, timeout=5).stdout.strip() or "exited"
    except Exception:  # noqa: BLE001
        return "?"


def smi_query():
    r = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True, timeout=10)
    rows = []
    for line in r.stdout.strip().splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) == 2 and parts[0].isdigit():
            rows.append((int(parts[0]), int(parts[1]) if parts[1].isdigit() else 0))
    return rows


def my_gpu_mem_mb():
    return next((mem for p, mem in smi_query() if p == PID), 0)


class GpuMon(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.peak = 0
        self.last = 0
        self.others = {}
        self.util = []
        self.halt = False
        self.halt_reason = None
        self.stop_flag = False

    def run(self):
        while not self.stop_flag:
            try:
                for p, mem in smi_query():
                    if p == PID:
                        self.last = mem
                        self.peak = max(self.peak, mem)
                        if mem > MEM_LIMIT_MB:
                            self.halt, self.halt_reason = True, f"own GPU memory {mem} MiB > {MEM_LIMIT_MB}"
                    else:
                        if p not in self.others:
                            self.others[p] = dict(user=owner(p), max_mib=mem)
                        self.others[p]["max_mib"] = max(self.others[p]["max_mib"], mem)
                        o = self.others[p]
                        if o["user"] not in ("aurnab", "exited", "?") and o["max_mib"] > 1024:
                            self.halt, self.halt_reason = True, f"non-aurnab pid {p} ({o['user']}) holds {o['max_mib']} MiB"
                u = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                                   capture_output=True, text=True, timeout=10).stdout.strip()
                if u.isdigit():
                    self.util.append(int(u))
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.5)


def arr_bytes(obj, seen=None):
    """Sum capacities of all wp.arrays reachable from a (nested) MJWarp dataclass."""
    seen = seen if seen is not None else set()
    tot = 0
    for v in vars(obj).values():
        if isinstance(v, wp.array):
            if id(v) not in seen:
                seen.add(id(v))
                tot += int(v.capacity or 0)
        elif hasattr(v, "__dataclass_fields__"):
            tot += arr_bytes(v, seen)
    return tot


def pair_types(m):
    n = len(mjw.GeomType)
    out = {}
    for trid, count in enumerate(np.asarray(m.geom_pair_type_count).tolist()):
        if count == 0:
            continue
        i = int((2 * n + 1 - np.sqrt((2 * n + 1) ** 2 - 8 * trid)) / 2)
        j = trid - i * (2 * n - i - 1) // 2
        out[f"{mjw.GeomType(i).name}-{mjw.GeomType(j).name}"] = int(count)
    return out


def overflow_names(mask):
    from mujoco_warp._src.types import OverflowType

    return [f.name for f in OverflowType if f.value and not (f.value & (f.value - 1)) and (mask & f.value)]


def device_info():
    dev = wp.get_device("cuda:0")
    info = dict(name=dev.name, arch=getattr(dev, "arch", None), total_mem_mb=round(dev.total_memory / 2**20),
                warp=wp.__version__, mujoco_warp=mjw.__version__, mujoco=mj.__version__,
                kernel_cache_dir=str(wp.config.kernel_cache_dir))
    for attr in ("toolkit_version", "driver_version"):
        for ctx in ("wp.context.runtime", "wp._src.context.runtime"):
            try:
                info[attr] = str(getattr(eval(ctx), attr))  # noqa: S307
                break
            except Exception:  # noqa: BLE001
                continue
    try:
        wp.set_mempool_release_threshold(dev, 0)
        info["mempool_release_threshold"] = 0
    except Exception as e:  # noqa: BLE001
        info["mempool_release_threshold_error"] = repr(e)
    return info


def try_put(mjm):
    import warnings

    rec = {}
    t0 = time.time()
    with warnings.catch_warnings(record=True) as wlist:
        warnings.simplefilter("always")
        try:
            m = mjw.put_model(mjm)
            wp.synchronize()
            rec.update(supported=True, put_model_s=round(time.time() - t0, 3), geom_pair_type_count=pair_types(m),
                       is_sparse=bool(getattr(m, "is_sparse", False)))
            for k in ("broadphase", "broadphase_filter", "graph_conditional", "run_collision_detection"):
                try:
                    rec[k] = str(getattr(m.opt, k))
                except Exception:  # noqa: BLE001
                    pass
            rec["_m"] = m
        except Exception as e:  # noqa: BLE001
            rec.update(supported=False, put_model_s=round(time.time() - t0, 3),
                       error="".join(traceback.format_exception(type(e), e, e.__traceback__)))
    rec["warnings"] = [f"{w.category.__name__}: {w.message}" for w in wlist]
    return rec


def load_models():
    """Stock model first (record exact error); then, if MJW_WORKAROUND=disable_multiccd, retry with
    opt.disableflags |= mjDSBL_MULTICCD (the fix named in the error). The flag is on the MjModel, so the
    CPU reference runs in parity use it too."""
    res, ok = {}, {}
    wa = os.environ.get("MJW_WORKAROUND", "")
    for name in ("human_plus_hippo", "human"):
        mjm = mj.MjModel.from_xml_path(MODELS[name])
        rec = {"stock": try_put(mjm)}
        m = rec["stock"].pop("_m", None)
        used = "stock" if m is not None else None
        if m is None and wa == "disable_multiccd":
            mjm.opt.disableflags |= int(mj.mjtDisableBit.mjDSBL_MULTICCD)
            rec["workaround_disable_multiccd"] = try_put(mjm)
            m = rec["workaround_disable_multiccd"].pop("_m", None)
            used = "workaround_disable_multiccd" if m is not None else None
        rec["used_for_runs"] = used
        if m is not None:
            ok[name] = (mjm, m)
        res[name] = rec
        for k, v in rec.items():
            if isinstance(v, dict):
                log("put_model", name, k, json.dumps({a: b for a, b in v.items() if a != "error"}), v.get("error", "")[-1500:])
    return res, ok


# ---------------------------------------------------------------- support mode
def support_mode(mon):
    out = dict(device=device_info())
    out["put_model"], ok = load_models()
    out["first_step"] = {}
    for name, (mjm, m) in ok.items():
        rec = {}
        try:
            mjd = mj.MjData(mjm)
            init_state(mjm, mjd, mj)
            d = mjw.put_data(mjm, mjd, nworld=1, nconmax=NCONMAX, njmax=NJMAX)
            t0 = time.time()
            mjw.step(m, d)
            wp.synchronize()
            rec["first_step_s_incl_jit"] = round(time.time() - t0, 2)
            t0 = time.time()
            mjw.step(m, d)
            wp.synchronize()
            rec["second_step_s"] = round(time.time() - t0, 4)
            t0 = time.time()
            mjw.reset_data(m, d)
            wp.synchronize()
            rec["reset_data_first_call_s"] = round(time.time() - t0, 2)
            q = d.qpos.numpy()
            rec["finite_after_step"] = bool(np.all(np.isfinite(q)))
            del d
        except Exception as e:  # noqa: BLE001
            rec["error"] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        out["first_step"][name] = rec
        log("first_step", name, json.dumps({k: v for k, v in rec.items() if k != "error"}), rec.get("error", "")[-3000:])
    return out


# ---------------------------------------------------------------- parity
def parity(name, mjm, m, nsteps=400, nworld=4, seed=123):
    lo, hi, muscle = ctrl_bounds(mjm, mj)
    ns = substeps(mjm)
    gen = SmoothCtrl(lo, hi, seed)
    U = np.zeros((nsteps, mjm.nu))
    for t in range(nsteps):
        if t % ns == 0:
            u = gen.next().copy()
        U[t] = u
    U32 = U.astype(np.float32)
    keys = ("qpos", "qvel", "act", "actuator_force", "ten_length")

    def cpu_run(perturb=0.0):
        d = mj.MjData(mjm)
        init_state(mjm, d, mj)
        if perturb:
            d.qpos[:] += perturb * np.random.default_rng(7).standard_normal(mjm.nq)
        rec = {k: np.zeros((nsteps, getattr(d, k).size)) for k in keys}
        rec["ncon"] = np.zeros(nsteps, int)
        rec["nefc"] = np.zeros(nsteps, int)
        for t in range(nsteps):
            d.ctrl[:] = U32[t].astype(np.float64)
            mj.mj_step(mjm, d)
            for k in keys:
                rec[k][t] = getattr(d, k)
            rec["ncon"][t] = d.ncon
            rec["nefc"][t] = d.nefc
        return rec

    cpu = cpu_run()
    cpu_p = cpu_run(perturb=1e-7)

    mjd = mj.MjData(mjm)
    init_state(mjm, mjd, mj)
    d = mjw.put_data(mjm, mjd, nworld=nworld, nconmax=NCONMAX, njmax=NJMAX)
    gpu = {k: np.zeros((nsteps, getattr(mjd, k).size)) for k in keys}
    gpu["ncon"] = np.zeros(nsteps, int)
    gpu["nefc"] = np.zeros(nsteps, int)
    cross_world = 0.0
    ov_all = 0
    t0 = time.time()
    for t in range(nsteps):
        d.ctrl.assign(np.tile(U32[t], (nworld, 1)))
        mjw.step(m, d)
        vals = {k: getattr(d, k).numpy() for k in keys}
        for k in keys:
            gpu[k][t] = vals[k][0]
            if nworld > 1:
                cross_world = max(cross_world, float(np.max(np.abs(vals[k][1:] - vals[k][0:1]))))
        nacon = int(d.nacon.numpy()[0])
        wid = d.contact.worldid.numpy()[:nacon]
        gpu["ncon"][t] = int(np.sum(wid == 0))
        gpu["nefc"][t] = int(d.nefc.numpy()[0])
        ov_all |= int(np.bitwise_or.reduce(d.overflow.numpy()))
    gpu_loop_s = time.time() - t0
    del d
    gc.collect()

    def diffs(a, b, t):
        r = {}
        for k in keys:
            dd = np.abs(a[k][t] - b[k][t])
            r[k] = dict(max=float(f"{dd.max():.3e}"), mean=float(f"{dd.mean():.3e}"))
        fm = np.abs(a["actuator_force"][t][muscle] - b["actuator_force"][t][muscle])
        r["muscle_force"] = dict(max=float(f"{fm.max():.3e}"), mean=float(f"{fm.mean():.3e}"),
                                 cpu_abs_max=float(f"{np.abs(b['actuator_force'][t][muscle]).max():.3e}"))
        if (~muscle).any():
            fe = np.abs(a["actuator_force"][t][~muscle] - b["actuator_force"][t][~muscle])
            r["exo_force"] = dict(max=float(f"{fe.max():.3e}"), mean=float(f"{fe.mean():.3e}"))
        r["ncon"] = [int(a["ncon"][t]), int(b["ncon"][t])]
        r["nefc"] = [int(a["nefc"][t]), int(b["nefc"][t])]
        return r

    at = {}
    for s in (1, 10, 100, 400):
        if s <= nsteps:
            at[str(s)] = dict(warp_f32_vs_cpu_f64=diffs(gpu, cpu, s - 1), cpu_perturbed_1e7_vs_cpu=diffs(cpu_p, cpu, s - 1))
    qd_g = np.max(np.abs(gpu["qpos"] - cpu["qpos"]), axis=1)
    qd_p = np.max(np.abs(cpu_p["qpos"] - cpu["qpos"]), axis=1)

    def first_above(series, thr):
        idx = np.nonzero(series > thr)[0]
        return int(idx[0] + 1) if idx.size else None

    ncon_mismatch = np.nonzero(gpu["ncon"] != cpu["ncon"])[0]
    res = dict(
        model=name, nworld=nworld, nsteps=nsteps, dt=float(mjm.opt.timestep), control_substeps=ns,
        initial_state="qpos0 (MyoAssist-seated), qvel=0, act=0; same float32-rounded ctrl trace on both",
        nconmax=NCONMAX, njmax=NJMAX, gpu_loop_s_with_readback=round(gpu_loop_s, 2),
        warp_cross_world_max_abs_diff=cross_world, warp_overflow_flags=overflow_names(ov_all),
        at_step=at,
        first_step_qpos_diff_above={
            "warp_vs_cpu": {str(t): first_above(qd_g, t) for t in (1e-6, 1e-4, 1e-2)},
            "cpu_perturbed_vs_cpu": {str(t): first_above(qd_p, t) for t in (1e-6, 1e-4, 1e-2)},
        },
        qpos_maxdiff_series_every10={
            "warp_vs_cpu": [float(f"{x:.2e}") for x in qd_g[9::10]],
            "cpu_perturbed_vs_cpu": [float(f"{x:.2e}") for x in qd_p[9::10]],
        },
        ncon_series_every10={"cpu": cpu["ncon"][9::10].tolist(), "warp": gpu["ncon"][9::10].tolist()},
        ncon_first_mismatch_step=int(ncon_mismatch[0] + 1) if ncon_mismatch.size else None,
        ncon_mismatch_fraction=round(float(ncon_mismatch.size / nsteps), 3),
        nefc_max={"cpu": int(cpu["nefc"].max()), "warp": int(gpu["nefc"].max())},
        ncon_max={"cpu": int(cpu["ncon"].max()), "warp": int(gpu["ncon"].max())},
    )
    return res


# ---------------------------------------------------------------- throughput
@wp.kernel
def smooth_ctrl_kernel(seed: int, alpha: float, lo: wp.array(dtype=float), hi: wp.array(dtype=float),
                       ctrl: wp.array2d(dtype=float)):
    w, a = wp.tid()
    st = wp.rand_init(seed, w * ctrl.shape[1] + a)
    r = lo[a] + (hi[a] - lo[a]) * wp.randf(st)
    ctrl[w, a] = ctrl[w, a] + alpha * (r - ctrl[w, a])


def throughput(name, mjm, m, nw):
    lo, hi, _ = ctrl_bounds(mjm, mj)
    lo_d = wp.array(lo.astype(np.float32), dtype=float)
    hi_d = wp.array(hi.astype(np.float32), dtype=float)
    ns = substeps(mjm)
    mjd = mj.MjData(mjm)
    init_state(mjm, mjd, mj)
    rec = dict(model=name, nworld=nw, substeps=ns, nconmax=NCONMAX, njmax=NJMAX)
    t0 = time.time()
    d = mjw.put_data(mjm, mjd, nworld=nw, nconmax=NCONMAX, njmax=NJMAX)
    wp.synchronize()
    rec["put_data_s"] = round(time.time() - t0, 3)
    rec["data_array_bytes_mb"] = round(arr_bytes(d) / 2**20, 1)
    t0 = time.time()
    with wp.ScopedCapture() as cap:
        for _ in range(ns):
            mjw.step(m, d)
    graph = cap.graph
    rec["graph_capture_s"] = round(time.time() - t0, 3)

    def ctrl_step(k):
        wp.launch(smooth_ctrl_kernel, dim=(nw, mjm.nu), inputs=[k, ALPHA, lo_d, hi_d, d.ctrl])
        wp.capture_launch(graph)

    # warm-up incl. one reset; also estimate per-control-step time
    mjw.reset_data(m, d)
    wp.synchronize()
    t0 = time.perf_counter()
    for k in range(10):
        ctrl_step(10_000 + k)
    wp.synchronize()
    t_ctrl = (time.perf_counter() - t0) / 10
    mjw.reset_data(m, d)
    wp.synchronize()
    n_ctrl = 100 if t_ctrl * 100 < 15 else 50
    # timed: no host sync inside the loop (pure GPU pipeline), resets every EPISODE_CTRL_STEPS control steps
    t0 = time.perf_counter()
    for k in range(n_ctrl):
        ctrl_step(k)
        if (k + 1) % EPISODE_CTRL_STEPS == 0:
            mjw.reset_data(m, d)
    wp.synchronize()
    el = time.perf_counter() - t0
    steps = n_ctrl * ns * nw
    rec.update(timed_control_steps=n_ctrl, timed_s=round(el, 3), steps_per_s=round(steps / el),
               control_transitions_per_s=round(n_ctrl * nw / el), realtime_factor_per_world=round(n_ctrl * ns * mjm.opt.timestep / el, 3))
    rec["gpu_mem_mb_process_steady"] = my_gpu_mem_mb()
    # stats pass (untimed): one episode, sample every 5 control steps
    mjw.reset_data(m, d)
    ncon_s, nefc_mean, nefc_max, it_mean, it_max, ov = [], [], [], [], [], 0
    for k in range(EPISODE_CTRL_STEPS):
        ctrl_step(50_000 + k)
        if k % 5 == 4:
            ncon_s.append(int(d.nacon.numpy()[0]) / nw)
            ne = d.nefc.numpy()
            it = d.solver_niter.numpy()
            nefc_mean.append(float(ne.mean()))
            nefc_max.append(int(ne.max()))
            it_mean.append(float(it.mean()))
            it_max.append(int(it.max()))
            ov |= int(np.bitwise_or.reduce(d.overflow.numpy()))
    q = d.qpos.numpy()
    rec.update(stats_ncon_per_world_mean=round(float(np.mean(ncon_s)), 3), stats_nefc_mean=round(float(np.mean(nefc_mean)), 2),
               stats_nefc_max=int(max(nefc_max)), stats_solver_iter_mean=round(float(np.mean(it_mean)), 2),
               stats_solver_iter_max=int(max(it_max)), overflow_flags=overflow_names(ov),
               nonfinite_worlds=int(np.sum(~np.all(np.isfinite(q), axis=1))))
    # RL-loop-like variant: host sync after every control step
    mjw.reset_data(m, d)
    wp.synchronize()
    n2 = 50
    t0 = time.perf_counter()
    for k in range(n2):
        ctrl_step(90_000 + k)
        wp.synchronize()
    el2 = time.perf_counter() - t0
    rec.update(sync_each_ctrl_step_steps_per_s=round(n2 * ns * nw / el2),
               sync_each_ctrl_step_control_transitions_per_s=round(n2 * nw / el2))
    rec["gpu_mem_mb_process_peak_so_far"] = max(mon.peak, rec["gpu_mem_mb_process_steady"])
    del graph, cap, d
    gc.collect()
    wp.synchronize()
    return rec


def main_mode(mon):
    out = dict(device=device_info())
    out["put_model"], ok = load_models()
    base_mem = my_gpu_mem_mb()
    out["gpu_mem_mb_after_put_model"] = base_mem
    out["parity"] = {}
    for name in ("human_plus_hippo", "human"):
        if name not in ok or budget_left() < 60 or mon.halt:
            continue
        try:
            t0 = time.time()
            out["parity"][name] = parity(name, *ok[name])
            log("parity", name, f"{time.time() - t0:.1f}s", json.dumps(out["parity"][name]["at_step"]))
        except Exception as e:  # noqa: BLE001
            out["parity"][name] = dict(error="".join(traceback.format_exception(type(e), e, e.__traceback__)))
            log("parity ERROR", name, out["parity"][name]["error"][-3000:])
    out["throughput"] = {}
    for name in ("human_plus_hippo", "human"):
        if name not in ok:
            continue
        mjm, m = ok[name]
        runs = []
        last = None  # (nworld, steady process MiB, data-array MiB)
        for nw in NWORLDS:
            if mon.halt:
                runs.append(dict(nworld=nw, skipped=f"halt: {mon.halt_reason}"))
                break
            if budget_left() < 45:
                runs.append(dict(nworld=nw, skipped=f"GPU time budget ({budget_left():.0f}s left)"))
                continue
            if last is not None:
                lnw, lmem, ldata = last
                proj = lmem + 1.3 * (ldata / lnw) * (nw - lnw) + 200
                if proj > MEM_LIMIT_MB:
                    runs.append(dict(nworld=nw, skipped=f"projected GPU memory {proj:.0f} MiB > {MEM_LIMIT_MB}"))
                    continue
            try:
                t0 = time.time()
                r = throughput(name, mjm, m, nw)
                r["wall_s"] = round(time.time() - t0, 1)
                runs.append(r)
                last = (nw, r["gpu_mem_mb_process_steady"], r["data_array_bytes_mb"])
                log("throughput", json.dumps(r))
            except Exception as e:  # noqa: BLE001
                err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                runs.append(dict(nworld=nw, error=err))
                log("throughput ERROR", name, nw, err[-3000:])
                break
        out["throughput"][name] = runs
    return out


import signal  # noqa: E402

signal.signal(signal.SIGTERM, lambda *a: sys.exit(143))  # hard timeout -> still write partial results
mon = GpuMon()
mon.start()
result = dict(mode=MODE, pid=PID, budget_s=BUDGET_S)
try:
    wp.init()
    result.update(support_mode(mon) if MODE == "support" else main_mode(mon))
except Exception as e:  # noqa: BLE001
    result["fatal_error"] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    log("FATAL", result["fatal_error"][-3000:])
finally:
    mon.stop_flag = True
    result["gpu_wall_s"] = round(time.time() - T_START, 1)
    result["gpu_mem_mb_process_peak"] = mon.peak
    result["gpu_util_samples"] = dict(n=len(mon.util), mean=round(float(np.mean(mon.util)), 1) if mon.util else None,
                                      max=max(mon.util) if mon.util else None)
    result["other_gpu_processes_seen"] = {str(k): v for k, v in mon.others.items()}
    result["halted"] = mon.halt_reason
    result["log"] = LOG
    (PROBE / "results" / f"warp_{MODE}.json").write_text(json.dumps(result, indent=2, default=str))
    log("done", MODE, "gpu_wall_s", result["gpu_wall_s"], "peak_mem_mb", mon.peak)
