"""CPU scaling: N concurrent single-threaded worker processes (inherits nice 10), 30 s each.

usage: scale_cpu.py <model> <dur_s> <N1> [<N2> ...]      (N <= 32, each worker lives < 60 s)
"""
import json
import os
import subprocess
import sys
import time

from common import PROBE

name, dur = sys.argv[1], float(sys.argv[2])
Ns = [int(x) for x in sys.argv[3:]]
assert max(Ns) <= 32 and dur <= 40
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
           NUMEXPR_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
py = sys.executable
here = os.path.dirname(os.path.abspath(__file__))
results = []


def loadavg():
    with open("/proc/loadavg") as f:
        return f.read().split()[:3]


def mem_available_mb():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable"):
                return int(line.split()[1]) // 1024


mjb = str(PROBE / "tmp" / f"{name}.mjb")  # precompiled model: ~150 MB/proc instead of ~560 MB (XML compile)
for N in Ns:
    outdir = PROBE / "tmp" / f"scale_{name}_{N}"
    outdir.mkdir(parents=True, exist_ok=True)
    la0, ma0 = loadavg(), mem_available_mb()
    if ma0 < N * 250 + 8000:  # keep >= 8 GB headroom for everyone else on the box
        r = dict(model=name, n_procs=N, skipped=f"MemAvailable {ma0} MB too low for {N} workers + 8 GB headroom")
        results.append(r)
        print(json.dumps(r), flush=True)
        continue
    t_start = time.time() + 5.0
    procs = []
    t_launch = time.time()
    for i in range(N):
        out = outdir / f"w{i}.json"
        procs.append(subprocess.Popen([py, os.path.join(here, "bench_cpu.py"), "worker", name, str(t_start), str(dur), str(out), mjb],
                                      env=env, cwd=str(PROBE / "work")))
    time.sleep(5.0 + dur / 2)
    ma_mid = mem_available_mb()
    rc = [p.wait(timeout=60) for p in procs]
    wall = time.time() - t_launch
    ws = []
    for i in range(N):
        try:
            ws.append(json.loads((outdir / f"w{i}.json").read_text()))
        except Exception as e:  # noqa: BLE001
            ws.append(dict(error=repr(e)))
    ok = [w for w in ws if "steps_per_s" in w]
    agg_steps = sum(w["steps_per_s"] for w in ok)
    agg_ctrl = sum(w["control_transitions_per_s"] for w in ok)
    rss = [w["mem"]["VmRSS"] for w in ok]
    pss = [w["mem"].get("Pss") for w in ok if w["mem"].get("Pss") is not None]
    uss = [w["mem"].get("USS") for w in ok if w["mem"].get("USS") is not None]
    r = dict(
        model=name, n_procs=N, duration_s=dur, loaded_from="mjb", returncodes=sorted(set(rc)), n_ok=len(ok),
        max_ready_after_t_start_s=max((w.get("ready_after_t_start_s", 0.0) for w in ok), default=None),
        aggregate_steps_per_s=round(agg_steps, 1), aggregate_control_transitions_per_s=round(agg_ctrl, 1),
        per_proc_control_transitions_per_s=dict(
            mean=round(agg_ctrl / max(len(ok), 1), 2),
            min=round(min(w["control_transitions_per_s"] for w in ok), 2) if ok else None,
            max=round(max(w["control_transitions_per_s"] for w in ok), 2) if ok else None,
        ),
        per_proc_rss_mb=dict(mean=round(sum(rss) / len(rss), 1), max=max(rss)) if rss else None,
        per_proc_pss_mb=dict(mean=round(sum(pss) / len(pss), 1), max=max(pss)) if pss else None,
        per_proc_uss_mb=dict(mean=round(sum(uss) / len(uss), 1), max=max(uss)) if uss else None,
        loadavg_before=la0, loadavg_after=loadavg(), mem_available_mb_before=ma0, mem_available_mb_mid=ma_mid,
        wall_incl_launch_s=round(wall, 2), worker_errors=[w for w in ws if "error" in w][:3],
    )
    results.append(r)
    print(json.dumps(r), flush=True)
    time.sleep(3.0)

(PROBE / "results" / f"scale_{name}.json").write_text(json.dumps(results, indent=2))
