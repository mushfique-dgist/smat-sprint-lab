"""Model statistics + CPU workload characterization (no timing). Fresh venv, CPU only."""
import json
import sys
from collections import Counter

import mujoco as mj
import numpy as np

from common import MODELS, PROBE, EPISODE_CTRL_STEPS, SmoothCtrl, ctrl_bounds, init_state, substeps


def ename(enum, v):
    try:
        return enum(int(v)).name
    except Exception:
        return str(int(v))


def body_filtered(m, b1, b2):
    """Approximation of MuJoCo's body-level contact filter (same weld body, or weld parent/child)."""
    w1, w2 = m.body_weldid[b1], m.body_weldid[b2]
    if w1 == w2:
        return True
    filterparent = not (m.opt.disableflags & mj.mjtDisableBit.mjDSBL_FILTERPARENT)
    if filterparent and w1 != 0 and w2 != 0:
        p1 = m.body_weldid[m.body_parentid[w1]]
        p2 = m.body_weldid[m.body_parentid[w2]]
        if w1 == p2 or w2 == p1:
            return True
    return False


def model_stats(name, path):
    m = mj.MjModel.from_xml_path(path)
    d = mj.MjData(m)
    lo, hi, muscle = ctrl_bounds(m, mj)
    wrap_types = Counter(ename(mj.mjtWrap, t) for t in m.wrap_type)
    fixed = spatial = 0
    wrap_geoms = set()
    for t in range(m.ntendon):
        adr, num = m.tendon_adr[t], m.tendon_num[t]
        ty = m.wrap_type[adr : adr + num]
        if np.all(ty == mj.mjtWrap.mjWRAP_JOINT):
            fixed += 1
        else:
            spatial += 1
    for w in range(m.nwrap):
        if m.wrap_type[w] in (mj.mjtWrap.mjWRAP_SPHERE, mj.mjtWrap.mjWRAP_CYLINDER):
            wrap_geoms.add(int(m.wrap_objid[w]))
    coll = [g for g in range(m.ngeom) if m.geom_contype[g] or m.geom_conaffinity[g]]
    cand = Counter()
    for i in range(len(coll)):
        for j in range(i + 1, len(coll)):
            g1, g2 = coll[i], coll[j]
            if not ((m.geom_contype[g1] & m.geom_conaffinity[g2]) or (m.geom_contype[g2] & m.geom_conaffinity[g1])):
                continue
            if body_filtered(m, m.geom_bodyid[g1], m.geom_bodyid[g2]):
                continue
            t = sorted([ename(mj.mjtGeom, m.geom_type[g1]), ename(mj.mjtGeom, m.geom_type[g2])])
            cand["-".join(t)] += 1
    dev_bodies = [i for i in range(m.nbody) if m.body(i).name.startswith("Hippo_L1_")]
    dev_mass = float(np.sum(m.body_mass[dev_bodies])) if dev_bodies else 0.0
    total_mass = float(np.sum(m.body_mass))
    coll_geoms = []
    for g in coll:
        coll_geoms.append(
            dict(
                name=m.geom(g).name, body=m.body(m.geom_bodyid[g]).name, type=ename(mj.mjtGeom, m.geom_type[g]),
                contype=int(m.geom_contype[g]), conaffinity=int(m.geom_conaffinity[g]), condim=int(m.geom_condim[g]),
                size=[round(float(x), 4) for x in m.geom_size[g]],
            )
        )
    mesh_coll = [
        dict(name=m.geom(g).name, nvert=int(m.mesh_vertnum[m.geom_dataid[g]]))
        for g in coll
        if m.geom_type[g] == mj.mjtGeom.mjGEOM_MESH
    ]
    s = dict(
        xml=path,
        nq=m.nq, nv=m.nv, nu=m.nu, na=m.na, nbody=m.nbody, njnt=m.njnt, ngeom=m.ngeom, nsite=m.nsite,
        nmesh=m.nmesh, nmeshvert=int(m.nmeshvert), nmeshface=int(m.nmeshface), nkey=m.nkey, nsensor=m.nsensor,
        n_muscles=int(muscle.sum()),
        n_nonmuscle_actuators=int((~muscle).sum()),
        nonmuscle_actuators=[
            dict(name=m.actuator(i).name, dyn=ename(mj.mjtDyn, m.actuator_dyntype[i]), gain=ename(mj.mjtGain, m.actuator_gaintype[i]),
                 gainprm0=float(m.actuator_gainprm[i, 0]), ctrlrange=m.actuator_ctrlrange[i].tolist(),
                 joint=m.joint(m.actuator_trnid[i, 0]).name if m.actuator_trntype[i] == mj.mjtTrn.mjTRN_JOINT else None)
            for i in range(m.nu) if not muscle[i]
        ],
        actuator_dyntypes=dict(Counter(ename(mj.mjtDyn, t) for t in m.actuator_dyntype)),
        actuator_gaintypes=dict(Counter(ename(mj.mjtGain, t) for t in m.actuator_gaintype)),
        actuator_trntypes=dict(Counter(ename(mj.mjtTrn, t) for t in m.actuator_trntype)),
        ntendon=m.ntendon, n_tendons_fixed=fixed, n_tendons_spatial=spatial, nwrap=m.nwrap,
        wrap_types=dict(wrap_types), n_wrap_geoms=len(wrap_geoms),
        wrap_geom_types=dict(Counter(ename(mj.mjtGeom, m.geom_type[g]) for g in wrap_geoms)),
        neq=m.neq, eq_types=dict(Counter(ename(mj.mjtEq, t) for t in m.eq_type)),
        joint_types=dict(Counter(ename(mj.mjtJoint, t) for t in m.jnt_type)),
        n_limited_joints=int(m.jnt_limited.sum()), n_limited_tendons=int(m.tendon_limited.sum()),
        geom_types=dict(Counter(ename(mj.mjtGeom, t) for t in m.geom_type)),
        n_colliding_geoms=len(coll),
        colliding_geom_types=dict(Counter(ename(mj.mjtGeom, m.geom_type[g]) for g in coll)),
        colliding_geoms=coll_geoms,
        colliding_mesh_geoms=mesh_coll,
        candidate_collision_pairs_approx=dict(cand),
        npair=m.npair, nexclude=m.nexclude,
        timestep=float(m.opt.timestep), substeps_at_50Hz=substeps(m),
        integrator=ename(mj.mjtIntegrator, m.opt.integrator), solver=ename(mj.mjtSolver, m.opt.solver),
        cone=ename(mj.mjtCone, m.opt.cone), jacobian=ename(mj.mjtJacobian, m.opt.jacobian),
        iterations=int(m.opt.iterations), ls_iterations=int(m.opt.ls_iterations), tolerance=float(m.opt.tolerance),
        noslip_iterations=int(m.opt.noslip_iterations), ccd_iterations=int(m.opt.ccd_iterations),
        disableflags=int(m.opt.disableflags), enableflags=int(m.opt.enableflags),
        gravity=m.opt.gravity.tolist(),
        total_mass_kg=round(total_mass, 4), device_mass_kg=round(dev_mass, 4), human_mass_kg=round(total_mass - dev_mass, 4),
        device_bodies=[m.body(i).name for i in dev_bodies],
        muscle_ctrlrange_unique=np.unique(m.actuator_ctrlrange[muscle], axis=0).tolist() if muscle.any() else [],
        keyframe_names=[m.key(i).name for i in range(m.nkey)],
    )
    return m, d, s


def contact_snapshot(m, d):
    mj.mj_forward(m, d)
    pel = m.body("pelvis").id
    dist = [float(d.contact.dist[i]) for i in range(d.ncon)]
    return dict(root_pos=d.qpos[:3].round(4).tolist(), pelvis_z=round(float(d.xpos[pel, 2]), 4), ncon=int(d.ncon),
                min_contact_dist=round(min(dist), 5) if dist else None, nefc=int(d.nefc))


def rollout_character(m, d, mode, n_episodes, seed=0):
    """Benchmark protocol without timing: qpos0 start, reset every EPISODE_CTRL_STEPS control steps."""
    lo, hi, muscle = ctrl_bounds(m, mj)
    ns = substeps(m)
    ctrl = SmoothCtrl(lo, hi, seed)
    pel = m.body("pelvis").id
    ncon, nefc, niter, pz = [], [], [], []
    pair_types = Counter()
    fall_t = []
    warn0 = [int(w.number) for w in d.warning]
    for ep in range(n_episodes):
        init_state(m, d, mj)
        ctrl.reset()
        z0 = float(d.xpos[pel, 2])
        fell = None
        for k in range(EPISODE_CTRL_STEPS):
            d.ctrl[:] = 0.0 if mode == "passive" else ctrl.next()
            for _ in range(ns):
                mj.mj_step(m, d)
                ncon.append(d.ncon)
                nefc.append(d.nefc)
                niter.append(int(d.solver_niter[0]))
                for i in range(d.ncon):
                    c = d.contact[i]
                    b1 = m.body(m.geom_bodyid[c.geom[0]]).name
                    b2 = m.body(m.geom_bodyid[c.geom[1]]).name
                    pair_types[f"{ename(mj.mjtGeom, m.geom_type[c.geom[0]])}:{b1} | {ename(mj.mjtGeom, m.geom_type[c.geom[1]])}:{b2}"] += 1
            z = float(d.xpos[pel, 2])
            pz.append(z)
            if fell is None and z < 0.6 * z0:
                fell = (k + 1) * ns * m.opt.timestep
        fall_t.append(fell)
    warn1 = [int(w.number) for w in d.warning]
    ncon, nefc, niter = np.array(ncon), np.array(nefc), np.array(niter)
    return dict(
        mode=mode, episodes=n_episodes, episode_s=EPISODE_CTRL_STEPS * ns * m.opt.timestep,
        ncon_mean=round(float(ncon.mean()), 3), ncon_max=int(ncon.max()), ncon_p95=float(np.percentile(ncon, 95)),
        nefc_mean=round(float(nefc.mean()), 2), nefc_max=int(nefc.max()), nefc_p95=float(np.percentile(nefc, 95)),
        solver_iter_mean=round(float(niter.mean()), 2), solver_iter_max=int(niter.max()),
        frac_steps_at_iter_limit=round(float(np.mean(niter >= m.opt.iterations)), 4),
        pelvis_z_min=round(float(np.min(pz)), 3), pelvis_z_end_last_episode=round(pz[-1], 3),
        time_to_pelvis_below_60pct_s=fall_t,
        top_contact_pairs=dict(pair_types.most_common(12)),
        mujoco_warnings_during=[
            dict(kind=ename(mj.mjtWarning, i), count=warn1[i] - warn0[i]) for i in range(len(warn1)) if warn1[i] - warn0[i] > 0
        ],
    )


out = dict(mujoco=mj.__version__, models={})
for name, path in MODELS.items():
    m, d, s = model_stats(name, path)
    init_state(m, d, mj)
    s["initial_state_qpos0"] = contact_snapshot(m, d)
    if m.nkey:
        mj.mj_resetDataKeyframe(m, d, 0)
        s["initial_state_key0"] = contact_snapshot(m, d)
        s["key0_minus_qpos0_root_z"] = round(float(m.key_qpos[0][2] - m.qpos0[2]), 5)
    s["character_passive"] = rollout_character(m, d, "passive", 1)
    s["character_random"] = rollout_character(m, d, "random", 4)
    out["models"][name] = s
    print(name, json.dumps({k: v for k, v in s.items() if k not in ("colliding_geoms",)}, default=str), flush=True)

(PROBE / "results" / "model_stats.json").write_text(json.dumps(out, indent=2, default=str))
print("OK stats done")
