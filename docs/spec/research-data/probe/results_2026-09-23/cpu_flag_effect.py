"""CPU only: physics effect of the Warp workaround (mjDSBL_MULTICCD) on native MuJoCo, same 400-step trace,
plus the margins that decide which plane-mesh contacts exist at the initial state."""
import json

import mujoco as mj
import numpy as np

from common import MODELS, PROBE, SmoothCtrl, ctrl_bounds, init_state, substeps

out = {}
for name in ("human_plus_hippo", "human"):
    ms = mj.MjModel.from_xml_path(MODELS[name])
    mf = mj.MjModel.from_xml_path(MODELS[name])
    mf.opt.disableflags |= int(mj.mjtDisableBit.mjDSBL_MULTICCD)
    lo, hi, _ = ctrl_bounds(ms, mj)
    gen = SmoothCtrl(lo, hi, 123)
    ns = substeps(ms)
    ds, df = mj.MjData(ms), mj.MjData(mf)
    init_state(ms, ds, mj)
    init_state(mf, df, mj)
    rec = {}
    ncon_s, ncon_f = [], []
    for t in range(400):
        if t % ns == 0:
            u = gen.next().astype(np.float32).astype(np.float64)
        ds.ctrl[:] = u
        df.ctrl[:] = u
        mj.mj_step(ms, ds)
        mj.mj_step(mf, df)
        ncon_s.append(ds.ncon)
        ncon_f.append(df.ncon)
        if t + 1 in (1, 10, 100, 400):
            rec[str(t + 1)] = dict(qpos_max=float(f"{np.max(np.abs(ds.qpos - df.qpos)):.3e}"),
                                   qvel_max=float(f"{np.max(np.abs(ds.qvel - df.qvel)):.3e}"),
                                   ncon_stock_vs_flag=[int(ds.ncon), int(df.ncon)])
    out[name] = dict(at_step=rec, ncon_differs_fraction=round(float(np.mean(np.array(ncon_s) != np.array(ncon_f))), 3))
    if name == "human_plus_hippo":
        t = ms.geom("terrain").id
        out["margins"] = dict(terrain_geom_margin=float(ms.geom_margin[t]), terrain_geom_gap=float(ms.geom_gap[t]),
                              toes_r_margin=float(ms.geom_margin[ms.geom("toes_r_geom_1").id]),
                              calcn_r_margin=float(ms.geom_margin[ms.geom("calcn_r_geom_1").id]))
    print(name, json.dumps(out[name]), flush=True)
print(json.dumps(out.get("margins")))
(PROBE / "results" / "cpu_flag_effect.json").write_text(json.dumps(out, indent=2))
