"""Shared helpers for the probe (fresh venv: mujoco 3.14 / mujoco-warp 3.14)."""
import os
from pathlib import Path

import numpy as np

PROBE = Path(os.environ.get("PROBE", "/home/aurnab/.cache/smatsprint-probe-2026-09-23"))
MODELS = {
    "human": str(PROBE / "model" / "human.xml"),
    "human_plus_hippo": str(PROBE / "model" / "human_plus_hippo.xml"),
}
CONTROL_DT = 0.02  # 50 Hz control
EPISODE_CTRL_STEPS = 50  # reset every 1 s of sim time (random excitations make the model fall)
ALPHA = 0.3  # exponential smoothing of the random excitation targets per control step


def substeps(m):
    return int(round(CONTROL_DT / m.opt.timestep))


def ctrl_bounds(m, mj):
    """Muscles -> [0,1]; others -> ctrlrange if limited else [-1,1] (exo: [-1,1])."""
    muscle = (m.actuator_gaintype == mj.mjtGain.mjGAIN_MUSCLE) | (m.actuator_dyntype == mj.mjtDyn.mjDYN_MUSCLE)
    lo = np.where(muscle, 0.0, -1.0)
    hi = np.where(muscle, 1.0, 1.0)
    lim = m.actuator_ctrllimited.astype(bool) & ~muscle
    lo = np.where(lim, m.actuator_ctrlrange[:, 0], lo)
    hi = np.where(lim, m.actuator_ctrlrange[:, 1], hi)
    return lo.astype(np.float64), hi.astype(np.float64), muscle


class SmoothCtrl:
    """Smooth random excitations: u <- u + ALPHA * (U(lo,hi) - u), once per control step."""

    def __init__(self, lo, hi, seed, nworld=None):
        self.lo, self.hi = lo, hi
        self.rng = np.random.default_rng(seed)
        shape = (lo.size,) if nworld is None else (nworld, lo.size)
        self.shape = shape
        self.u = np.clip(np.zeros(shape), lo, hi)

    def reset(self):
        self.u = np.clip(np.zeros(self.shape), self.lo, self.hi)

    def next(self):
        r = self.lo + (self.hi - self.lo) * self.rng.random(self.shape)
        self.u = self.u + ALPHA * (r - self.u)
        return self.u


def init_state(m, d, mj):
    """Initial state used everywhere: qpos0 (the MyoAssist-seated neutral pose), zero vel/act."""
    mj.mj_resetData(m, d)
    mj.mj_forward(m, d)


def proc_mem():
    """RSS / PSS / USS (MB) of this process from /proc."""
    out = {}
    with open("/proc/self/status") as f:
        for line in f:
            k = line.split(":")[0]
            if k in ("VmRSS", "RssAnon", "RssFile", "RssShmem", "VmHWM"):
                out[k] = int(line.split()[1]) / 1024.0
    try:
        with open("/proc/self/smaps_rollup") as f:
            priv = 0
            for line in f:
                k = line.split(":")[0]
                if k == "Pss":
                    out["Pss"] = int(line.split()[1]) / 1024.0
                if k in ("Private_Clean", "Private_Dirty"):
                    priv += int(line.split()[1])
            out["USS"] = priv / 1024.0
    except OSError:
        pass
    return {k: round(v, 2) for k, v in out.items()}
