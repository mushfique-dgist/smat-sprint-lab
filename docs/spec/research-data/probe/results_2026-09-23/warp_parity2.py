"""Parity controls for human_plus_hippo (MULTICCD disabled on both sides):
  1) contact-by-contact comparison at the initial state (mj_forward vs mjw.forward)
  2) contact-disabled parity (mjDSBL_CONTACT on both): isolates muscle/tendon/equality/joint dynamics
"""
import json
import os
import sys
import time
import traceback
from collections import defaultdict

T0 = time.time()
import mujoco as mj  # noqa: E402
import numpy as np  # noqa: E402
import warp as wp  # noqa: E402

wp.config.kernel_cache_dir = os.environ["WARP_CACHE_PATH"]
wp.config.log_level = wp.LOG_WARNING
import mujoco_warp as mjw  # noqa: E402

sys.argv = [sys.argv[0], "main"]  # warp_probe module-level code expects a mode; we only import helpers below
from common import MODELS, PROBE, init_state  # noqa: E402

NCONMAX, NJMAX = 48, 160
out = {}


def load(flags):
    mjm = mj.MjModel.from_xml_path(MODELS["human_plus_hippo"])
    for f in flags:
        mjm.opt.disableflags |= int(f)
    return mjm


def contacts_cpu(mjm):
    d = mj.MjData(mjm)
    init_state(mjm, d, mj)
    g = defaultdict(list)
    for i in range(d.ncon):
        c = d.contact[i]
        g[f"{mjm.geom(c.geom[0]).name}|{mjm.geom(c.geom[1]).name}"].append(round(float(c.dist), 5))
    return int(d.ncon), {k: sorted(v) for k, v in sorted(g.items())}


def contacts_gpu(mjm, m):
    mjd = mj.MjData(mjm)
    init_state(mjm, mjd, mj)
    d = mjw.put_data(mjm, mjd, nworld=1, nconmax=NCONMAX, njmax=NJMAX)
    mjw.forward(m, d)
    n = int(d.nacon.numpy()[0])
    geom = d.contact.geom.numpy()[:n]
    dist = d.contact.dist.numpy()[:n]
    g = defaultdict(list)
    for (a, b), di in zip(geom, dist):
        g[f"{mjm.geom(int(a)).name}|{mjm.geom(int(b)).name}"].append(round(float(di), 5))
    return n, {k: sorted(v) for k, v in sorted(g.items())}


try:
    wp.init()
    mjm = load([mj.mjtDisableBit.mjDSBL_MULTICCD])
    m = mjw.put_model(mjm)
    n_cpu, c_cpu = contacts_cpu(mjm)
    n_gpu, c_gpu = contacts_gpu(mjm, m)
    out["initial_contacts"] = dict(cpu_ncon=n_cpu, warp_ncon=n_gpu, cpu_by_pair_dist=c_cpu, warp_by_pair_dist=c_gpu,
                                   geom_margin_of_contact_geoms=sorted({float(mjm.geom_margin[mjm.geom(k.split("|")[1]).id]) for k in c_cpu}))
    print("initial contacts cpu", n_cpu, json.dumps(c_cpu), flush=True)
    print("initial contacts warp", n_gpu, json.dumps(c_gpu), flush=True)
except Exception as e:  # noqa: BLE001
    out["initial_contacts"] = dict(error="".join(traceback.format_exception(type(e), e, e.__traceback__)))
    print(out["initial_contacts"]["error"], flush=True)

# contact-disabled parity, reusing the exact parity routine from warp_probe (imported lazily to avoid its main)
try:
    import importlib.util

    spec = importlib.util.spec_from_file_location("wprobe_helpers", str(PROBE / "warp_probe_helpers.py"))
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    mjm_nc = load([mj.mjtDisableBit.mjDSBL_MULTICCD, mj.mjtDisableBit.mjDSBL_CONTACT])
    m_nc = mjw.put_model(mjm_nc)
    r = H.parity("human_plus_hippo_contacts_disabled", mjm_nc, m_nc)
    out["parity_contacts_disabled"] = r
    print("parity contacts disabled", json.dumps(r["at_step"]), flush=True)
    print("first_above", json.dumps(r["first_step_qpos_diff_above"]), flush=True)
except Exception as e:  # noqa: BLE001
    out["parity_contacts_disabled"] = dict(error="".join(traceback.format_exception(type(e), e, e.__traceback__)))
    print(out["parity_contacts_disabled"]["error"], flush=True)

out["gpu_wall_s"] = round(time.time() - T0, 1)
(PROBE / "results" / "warp_parity2.json").write_text(json.dumps(out, indent=2, default=str))
print("done gpu_wall_s", out["gpu_wall_s"])
