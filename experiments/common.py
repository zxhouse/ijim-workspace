"""Shared infrastructure for the experiments: landscapes, parallel runs, stats."""
from __future__ import annotations

import json
import os
import sys
import time
from functools import lru_cache
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "testbed"))

from looplab.params import Params, random_params  # noqa: E402
from looplab.landscape import Landscape  # noqa: E402
from looplab.policies import Config, run  # noqa: E402

RES = os.path.join(ROOT, "experiments", "results")
FIG = os.path.join(ROOT, "paper", "figures")
os.makedirs(RES, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

N_SVC = 30   # smooth service family
N_RUG = 20   # rugged family
RHO0 = 0.5   # baseline validity of pre-screening
NSESS0 = 2000


def landscape_spec(cls: str, i: int) -> dict:
    if cls == "ref":
        return {}
    if cls == "svc":
        return dict(seed=1000 + i, rugged=0.0)  # i >= 100: tuning instances
    if cls == "rug":
        K = (2, 4, 6, 4, 6)[i % 5]
        tau = (1.0, 1.0, 1.0, 1.5, 1.5)[i % 5]
        return dict(seed=2000 + i, K=K, tau=tau)
    raise ValueError(cls)


@lru_cache(maxsize=64)
def get_landscape(cls: str, i: int = 0, n_extra: int = 0, drop: tuple = ()) -> Landscape:
    if cls == "ref":
        assert n_extra == 0 and not drop
        return Landscape(Params(), "REF")
    spec = landscape_spec(cls, i)
    rng = np.random.default_rng(spec["seed"])
    p = random_params(rng, rugged=spec.get("rugged", 0.0), K=spec.get("K", 0),
                      tau=spec.get("tau", 0.0), tails=spec.get("tails", 0.0), n_extra=n_extra, drop=drop)
    return Landscape(p, f"{cls.upper()}{i}")


@lru_cache(maxsize=256)
def get_sigma(cls: str, i: int, n_sess: int, n_extra: int = 0, drop: tuple = ()) -> float:
    return get_landscape(cls, i, n_extra, drop).sigma(n_sess)


def classes():
    return [("ref", [0]), ("svc", list(range(N_SVC))), ("rug", list(range(N_RUG)))]


def _job(args):
    cls, i, cfg_kw, seed, tag = args
    L = get_landscape(cls, i, cfg_kw.pop("_n_extra", 0), tuple(cfg_kw.pop("_drop", ())))
    n = cfg_kw.get("n_sess", NSESS0)
    cfg_kw.setdefault("rho", RHO0)
    if "sigma" not in cfg_kw:
        cfg_kw["sigma"] = L.sigma(n)
    cfg = Config(**cfg_kw)
    log, E = run(L, cfg, seed)
    out = []
    for r in log:
        r = dict(r)
        r.update(cls=cls, inst=i, seed=seed, **tag)
        r["shipped_pct"] = 100 * r["shipped"] / r["ustar"]
        r["found_pct"] = 100 * r["found"] / r["ustar"]
        r["belief_pct"] = 100 * r["belief"] / r["ustar"]
        out.append(r)
    return out


def parallel(jobs, procs=None, chunksize=4):
    t = time.time()
    procs = procs or os.cpu_count()
    with Pool(procs) as P:
        res = P.map(_job, jobs, chunksize=chunksize)
    rows = [r for rr in res for r in rr]
    print(f"  {len(jobs)} runs in {time.time()-t:.0f}s", flush=True)
    return rows


def save(name, obj):
    with open(os.path.join(RES, name), "w") as f:
        json.dump(obj, f, indent=1, default=float)


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


def ci95(a):
    a = np.asarray(a, float)
    if len(a) < 2:
        return float(np.mean(a)), 0.0
    return float(a.mean()), float(1.96 * a.std(ddof=1) / np.sqrt(len(a)))


def t_ci(a):
    from scipy import stats
    a = np.asarray(a, float)
    m = a.mean(); se = a.std(ddof=1) / np.sqrt(len(a))
    return float(m), float(stats.t.ppf(0.975, len(a) - 1) * se)


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    m = len(p); run_max = 0
    for k, idx in enumerate(order):
        run_max = max(run_max, (m - k) * p[idx])
        adj[idx] = min(run_max, 1.0)
    return adj


def summarise(rows, by, value="shipped_pct", unit_keys=("cls", "inst")):
    """Mean and CI of `value` per group; for families, CI across instances."""
    import collections
    g = collections.defaultdict(list)
    for r in rows:
        g[tuple(r[k] for k in by)].append(r)
    out = {}
    for k, rr in g.items():
        cls = rr[0]["cls"]
        if cls == "ref":
            m, h = t_ci([r[value] for r in rr])
        else:
            inst = collections.defaultdict(list)
            for r in rr:
                inst[r["inst"]].append(r[value])
            m, h = t_ci([np.mean(v) for v in inst.values()])
        out[k] = (m, h, len(rr))
    return out


def paired(rows, key, a, b, value="shipped_pct", filt=None):
    """Paired difference a-b. Ref: across seeds; families: across instances."""
    import collections
    from scipy import stats
    filt = filt or (lambda r: True)
    d = collections.defaultdict(dict)
    for r in rows:
        if not filt(r):
            continue
        if r[key] in (a, b):
            unit = (r["inst"], r["seed"]) if r["cls"] == "ref" else (r["inst"], r["seed"])
            d[unit][r[key]] = r[value]
    by_inst = collections.defaultdict(list)
    for (inst, seed), v in d.items():
        if a in v and b in v:
            by_inst[inst].append(v[a] - v[b])
    if len(by_inst) == 1:
        diffs = np.array(list(by_inst.values())[0])
    else:
        diffs = np.array([np.mean(v) for v in by_inst.values()])
    m, h = t_ci(diffs)
    try:
        w = stats.wilcoxon(diffs).pvalue if np.any(diffs != 0) else 1.0
    except ValueError:
        w = 1.0
    dz = float(diffs.mean() / diffs.std(ddof=1)) if diffs.std(ddof=1) > 0 else 0.0
    return dict(mean=m, half=h, p=float(w), dz=dz, n=len(diffs))
