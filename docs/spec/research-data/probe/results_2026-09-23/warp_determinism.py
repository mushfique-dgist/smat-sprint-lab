"""Determinism controls (human_plus_hippo, MULTICCD disabled), same 400-step trace as parity:
  A) 4 identical worlds with contacts: per-step cross-world divergence
  B,C) two separate nworld=1 runs: run-to-run reproducibility
  D) 4 identical worlds with contacts disabled
  E) CPU MuJoCo run twice: bitwise reproducibility reference
"""
import json
import os
import time

T0 = time.time()
import mujoco as mj  # noqa: E402
import numpy as np  # noqa: E402
import warp as wp  # noqa: E402

wp.config.kernel_cache_dir = os.environ["WARP_CACHE_PATH"]
wp.config.log_level = wp.LOG_WARNING
import mujoco_warp as mjw  # noqa: E402

from common import MODELS, PROBE, SmoothCtrl, ctrl_bounds, init_state, substeps  # noqa: E402

NSTEP, NCONMAX, NJMAX = 400, 48, 160


def load(contacts=True):
    mjm = mj.MjModel.from_xml_path(MODELS["human_plus_hippo"])
    mjm.opt.disableflags |= int(mj.mjtDisableBit.mjDSBL_MULTICCD)
    if not contacts:
        mjm.opt.disableflags |= int(mj.mjtDisableBit.mjDSBL_CONTACT)
    return mjm


mjm_c = load(True)
lo, hi, _ = ctrl_bounds(mjm_c, mj)
gen = SmoothCtrl(lo, hi, 123)  # identical trace to parity()
ns = substeps(mjm_c)
U = np.zeros((NSTEP, mjm_c.nu))
for t in range(NSTEP):
    if t % ns == 0:
        u = gen.next().copy()
    U[t] = u
U32 = U.astype(np.float32)


def run_gpu(mjm, m, nworld):
    mjd = mj.MjData(mjm)
    init_state(mjm, mjd, mj)
    d = mjw.put_data(mjm, mjd, nworld=nworld, nconmax=NCONMAX, njmax=NJMAX)
    q = np.zeros((NSTEP, nworld, mjm.nq))
    f = np.zeros((NSTEP, nworld, mjm.nu))
    nc = np.zeros((NSTEP, nworld), int)
    for t in range(NSTEP):
        d.ctrl.assign(np.tile(U32[t], (nworld, 1)))
        mjw.step(m, d)
        q[t] = d.qpos.numpy()
        f[t] = d.actuator_force.numpy()
        n = int(d.nacon.numpy()[0])
        nc[t] = np.bincount(d.contact.worldid.numpy()[:n], minlength=nworld)[:nworld]
    del d
    return q, f, nc


def run_cpu(mjm):
    d = mj.MjData(mjm)
    init_state(mjm, d, mj)
    q = np.zeros((NSTEP, mjm.nq))
    for t in range(NSTEP):
        d.ctrl[:] = U32[t].astype(np.float64)
        mj.mj_step(mjm, d)
        q[t] = d.qpos
    return q


def first_above(series, thr):
    idx = np.nonzero(series > thr)[0]
    return int(idx[0] + 1) if idx.size else None


def summarize(series_q, series_f, label):
    return dict(
        label=label,
        first_step_qpos_diff_above={str(t): first_above(series_q, t) for t in (0.0, 1e-6, 1e-4, 1e-2)},
        qpos_maxdiff_at={str(s): float(f"{series_q[s - 1]:.3e}") for s in (1, 10, 100, 400)},
        force_maxdiff_at={str(s): float(f"{series_f[s - 1]:.3e}") for s in (1, 10, 100, 400)},
        qpos_maxdiff_every10=[float(f"{x:.2e}") for x in series_q[9::10]],
    )


out = {}
wp.init()
m_c = mjw.put_model(mjm_c)
qa, fa, nca = run_gpu(mjm_c, m_c, 4)
cw_q = np.max(np.abs(qa[:, 1:, :] - qa[:, :1, :]), axis=(1, 2))
cw_f = np.max(np.abs(fa[:, 1:, :] - fa[:, :1, :]), axis=(1, 2))
ncon_differs = np.nonzero(np.any(nca != nca[:, :1], axis=1))[0]
out["A_identical_worlds_with_contacts"] = summarize(cw_q, cw_f, "4 identical worlds, max over worlds 1..3 of |world_k - world_0|")
out["A_identical_worlds_with_contacts"]["first_step_worlds_ncon_differ"] = int(ncon_differs[0] + 1) if ncon_differs.size else None
out["A_identical_worlds_with_contacts"]["fraction_steps_ncon_differ"] = round(float(ncon_differs.size / NSTEP), 3)

qb, fb, _ = run_gpu(mjm_c, m_c, 1)
qc, fc, _ = run_gpu(mjm_c, m_c, 1)
rr_q = np.max(np.abs(qb[:, 0] - qc[:, 0]), axis=1)
rr_f = np.max(np.abs(fb[:, 0] - fc[:, 0]), axis=1)
out["BC_run_to_run_nworld1_with_contacts"] = summarize(rr_q, rr_f, "two separate nworld=1 runs, same inputs")

mjm_n = load(False)
m_n = mjw.put_model(mjm_n)
qd, fd, _ = run_gpu(mjm_n, m_n, 4)
cw_qn = np.max(np.abs(qd[:, 1:, :] - qd[:, :1, :]), axis=(1, 2))
cw_fn = np.max(np.abs(fd[:, 1:, :] - fd[:, :1, :]), axis=(1, 2))
out["D_identical_worlds_contacts_disabled"] = summarize(cw_qn, cw_fn, "4 identical worlds, contacts disabled")

q1, q2 = run_cpu(mjm_c), run_cpu(mjm_c)
out["E_cpu_run_to_run_max_abs_qpos_diff"] = float(np.max(np.abs(q1 - q2)))
out["gpu_wall_s"] = round(time.time() - T0, 1)
(PROBE / "results" / "warp_determinism.json").write_text(json.dumps(out, indent=2))
for k, v in out.items():
    print(k, json.dumps(v) if isinstance(v, dict) else v, flush=True)
