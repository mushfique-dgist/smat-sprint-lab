"""Native CPU MuJoCo benchmark (fresh venv).

  single <model> <seconds>              single-thread steps/s under the benchmark protocol
  rss <model>                           memory of one MjModel+MjData in this fresh process
  worker <model> <t_start> <dur> <out>  one scaling worker: wait for t_start, run dur seconds
"""
import json
import os
import sys
import time

MEM0 = None
if len(sys.argv) > 1 and sys.argv[1] == "rss":
    from common import proc_mem

    MEM0 = proc_mem()  # before importing mujoco/numpy-heavy stuff (common imports numpy)

import mujoco as mj
import numpy as np

from common import EPISODE_CTRL_STEPS, MODELS, SmoothCtrl, ctrl_bounds, init_state, proc_mem, substeps


def run(m, d, seconds, seed=0, t_start=None):
    lo, hi, _ = ctrl_bounds(m, mj)
    ns = substeps(m)
    ctrl = SmoothCtrl(lo, hi, seed)
    init_state(m, d, mj)
    for _ in range(100):  # warm-up
        d.ctrl[:] = ctrl.next()
        mj.mj_step(m, d)
    init_state(m, d, mj)
    ctrl.reset()
    if t_start is not None:
        while time.time() < t_start:
            time.sleep(0.005)
    steps = 0
    k = 0
    ncon_sum = 0
    t0 = time.perf_counter()
    t_end = t0 + seconds
    while True:
        d.ctrl[:] = ctrl.next()
        for _ in range(ns):
            mj.mj_step(m, d)
        steps += ns
        ncon_sum += d.ncon
        k += 1
        if k % EPISODE_CTRL_STEPS == 0:
            init_state(m, d, mj)
            ctrl.reset()
        if time.perf_counter() >= t_end:
            break
    el = time.perf_counter() - t0
    return dict(
        physics_steps=steps, control_steps=k, elapsed_s=round(el, 4), substeps=ns,
        steps_per_s=round(steps / el, 1), control_transitions_per_s=round(k / el, 2),
        realtime_factor=round(steps * m.opt.timestep / el, 3), mean_ncon_at_control_steps=round(ncon_sum / k, 3),
        warnings={mj.mjtWarning(i).name: int(w.number) for i, w in enumerate(d.warning) if w.number},
    )


mode = sys.argv[1]
if mode == "single":
    name, sec = sys.argv[2], float(sys.argv[3])
    m = mj.MjModel.from_xml_path(MODELS[name])
    if os.environ.get("DISABLE_MULTICCD") == "1":  # same 1-flag change the Warp runs need
        m.opt.disableflags |= int(mj.mjtDisableBit.mjDSBL_MULTICCD)
    d = mj.MjData(m)
    r = run(m, d, sec)
    r.update(model=name, mem=proc_mem(), threads=os.environ.get("OMP_NUM_THREADS"),
             disableflags=int(m.opt.disableflags))
    print(json.dumps(r))
elif mode == "save_mjb":
    name = sys.argv[2]
    m = mj.MjModel.from_xml_path(MODELS[name])
    mj.mj_saveModel(m, sys.argv[3], None)
    print(json.dumps(dict(model=name, mjb=sys.argv[3], mjb_bytes=os.path.getsize(sys.argv[3]))))
elif mode == "rss":
    import ctypes

    name = sys.argv[2]
    mjb = sys.argv[3] if len(sys.argv) > 3 else None
    mem_import = proc_mem()
    m = mj.MjModel.from_binary_path(mjb) if mjb else mj.MjModel.from_xml_path(MODELS[name])
    mem_model = proc_mem()
    ctypes.CDLL("libc.so.6").malloc_trim(0)
    mem_trim = proc_mem()
    d = mj.MjData(m)
    mem_data = proc_mem()
    lo, hi, _ = ctrl_bounds(m, mj)
    ctrl = SmoothCtrl(lo, hi, 0)
    init_state(m, d, mj)
    for i in range(1000):
        if i % substeps(m) == 0:
            d.ctrl[:] = ctrl.next()
        mj.mj_step(m, d)
    mem_step = proc_mem()
    print(json.dumps(dict(
        model=name, loaded_from="mjb" if mjb else "xml", before_mujoco_import=MEM0, after_import=mem_import,
        after_mjmodel=mem_model, after_malloc_trim=mem_trim, after_mjdata=mem_data, after_1000_steps=mem_step,
        mjmodel_plus_mjdata_rss_delta_mb=round(mem_step["VmRSS"] - mem_import["VmRSS"], 2),
        mjdata_nbytes_mb=round(d.nbuffer / 2**20, 3) if hasattr(d, "nbuffer") else None,
        mjmodel_nbytes_mb=round(m.nbuffer / 2**20, 3) if hasattr(m, "nbuffer") else None,
    )))
elif mode == "worker":
    name, t_start, dur, out = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
    mjb = sys.argv[6] if len(sys.argv) > 6 else None
    m = mj.MjModel.from_binary_path(mjb) if mjb else mj.MjModel.from_xml_path(MODELS[name])
    d = mj.MjData(m)
    late = time.time() - t_start
    r = run(m, d, dur, seed=os.getpid(), t_start=t_start)
    r.update(model=name, loaded_from="mjb" if mjb else "xml", pid=os.getpid(), mem=proc_mem(),
             ready_after_t_start_s=round(late, 3) if late > 0 else 0.0)
    with open(out, "w") as f:
        json.dump(r, f)
