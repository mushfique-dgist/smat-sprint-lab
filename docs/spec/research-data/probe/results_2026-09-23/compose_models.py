"""Compose myolegs26 (human) and myolegs26 + Hippo_L1 (human_plus_hippo) with MyoAssist's
own compose pipeline (flat default ground, feet seated in light contact), then export each as a
self-contained XML + copied assets under $PROBE/model/.

Runs inside the EXISTING sprint venv, read-only: PYTHONDONTWRITEBYTECODE=1, cwd and TMPDIR in $PROBE,
no compose cache.  The human-only model reuses compose._compose_env_model with assist_sim.load_msk
swapped in for load_combined *in this process only* (no file is modified), so both models get the
identical terrain merge + seating.
"""
import hashlib
import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.pop("MYOASSIST_CACHE_DIR", None)

import mujoco as mj
import numpy as np

PROBE = Path(os.environ["PROBE"])
OUT = PROBE / "model"
OUT.mkdir(parents=True, exist_ok=True)

import assist_sim
import myo_sim
import myoassist_utils.compose as C
from assist_sim import load_msk

MSK = "myolegs26"
DEVICE = "Hippo_L1"


def compose(device_key):
    if device_key is None:
        orig = C.load_combined

        def _msk_only(msk, dev, export_xml=None, planar_root=False):
            return load_msk(msk, export_xml=export_xml)

        C.load_combined = _msk_only
        try:
            return C._compose_env_model(MSK, None)
        finally:
            C.load_combined = orig
    return C.compose_env_model(MSK, device_key, terrain=None, cache_dir=None)


def make_self_contained(xml_str, name):
    root = ET.fromstring(xml_str)
    asset_dir = OUT / f"{name}_assets"
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True)
    src_to_rel = {}
    used = set()
    n_attr = 0
    for el in root.iter():
        for attr, val in list(el.attrib.items()):
            if not attr.startswith("file") or not val:
                continue
            src = Path(val)
            if not src.is_absolute():
                raise RuntimeError(f"non-absolute asset path after compose: {attr}={val}")
            if not src.exists():
                raise RuntimeError(f"missing asset: {src}")
            key = str(src.resolve())
            if key not in src_to_rel:
                base = src.name
                cand, k = base, 1
                while cand in used:
                    cand = f"{k}_{base}"
                    k += 1
                used.add(cand)
                shutil.copy2(src, asset_dir / cand)
                src_to_rel[key] = f"{name}_assets/{cand}"
            el.set(attr, src_to_rel[key])
            n_attr += 1
    stripped = []
    for comp in root.iter("compiler"):
        for a in ("meshdir", "texturedir", "assetdir"):
            if a in comp.attrib:
                stripped.append((a, comp.attrib.pop(a)))
    ET.indent(root, space="  ")
    out_xml = OUT / f"{name}.xml"
    out_xml.write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
    nbytes = sum(p.stat().st_size for p in asset_dir.iterdir())
    return out_xml, dict(n_file_attrs=n_attr, n_asset_files=len(src_to_rel), asset_bytes=nbytes, stripped_compiler_dirs=stripped)


def fingerprint(m):
    return dict(
        nq=m.nq, nv=m.nv, nu=m.nu, na=m.na, nbody=m.nbody, njnt=m.njnt, ngeom=m.ngeom, nmesh=m.nmesh,
        nmeshvert=int(m.nmeshvert), ntendon=m.ntendon, nwrap=m.nwrap, neq=m.neq, nkey=m.nkey,
        timestep=float(m.opt.timestep), total_mass=float(np.sum(m.body_mass)),
    )


def equal_sim(m1, m2, nstep=300, seed=0):
    """Same ctrl trace on both models; return max |qpos diff| (should be exactly 0)."""
    rng = np.random.default_rng(seed)
    d1, d2 = mj.MjData(m1), mj.MjData(m2)
    if m1.nkey:
        mj.mj_resetDataKeyframe(m1, d1, 0)
        mj.mj_resetDataKeyframe(m2, d2, 0)
    lo, hi = m1.actuator_ctrlrange[:, 0], m1.actuator_ctrlrange[:, 1]
    mx = 0.0
    for i in range(nstep):
        if i % 20 == 0:
            u = lo + (hi - lo) * rng.random(m1.nu)
        d1.ctrl[:] = u
        d2.ctrl[:] = u
        mj.mj_step(m1, d1)
        mj.mj_step(m2, d2)
        mx = max(mx, float(np.max(np.abs(d1.qpos - d2.qpos))))
    return mx


report = dict(
    compose_env=dict(
        python=sys.version.split()[0], mujoco=mj.__version__,
        assist_sim=getattr(assist_sim, "__version__", "?"), myo_sim=getattr(myo_sim, "__version__", "?"),
        compose_module=C.__file__,
    ),
    models={},
)
for name, dev in (("human", None), ("human_plus_hippo", DEVICE)):
    t0 = time.time()
    xml_str = compose(dev)
    t_comp = time.time() - t0
    m_src = mj.MjModel.from_xml_string(xml_str)
    out_xml, info = make_self_contained(xml_str, name)
    m_out = mj.MjModel.from_xml_path(str(out_xml))
    fp_src, fp_out = fingerprint(m_src), fingerprint(m_out)
    same_fp = fp_src == fp_out
    mass_diff = float(np.max(np.abs(m_src.body_mass - m_out.body_mass))) if m_src.nbody == m_out.nbody else None
    sim_diff = equal_sim(m_src, m_out)
    report["models"][name] = dict(
        msk=MSK, device=dev, compose_s=round(t_comp, 3), xml=str(out_xml),
        xml_sha256=hashlib.sha256(out_xml.read_bytes()).hexdigest(), export=info,
        fingerprint=fp_out, fingerprint_matches_compose_string=same_fp, max_body_mass_diff=mass_diff,
        max_qpos_diff_300_steps_vs_compose_string=sim_diff,
        body_names_hippo=[m_out.body(i).name for i in range(m_out.nbody) if m_out.body(i).name.startswith("hippo")],
    )
    print(name, json.dumps(report["models"][name], default=str), flush=True)

(PROBE / "results" / "compose_report.json").write_text(json.dumps(report, indent=2, default=str))
print("OK compose done")
