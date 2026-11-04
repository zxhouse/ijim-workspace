"""Discrete-event emulation of the testbed topology (high-fidelity level).

Every session arrives at the edge, every page request crosses the access
network, the edge (CDN when enabled), the web-application firewall, the
load balancer and the application-server pool, and makes database, ML
inference and external-API calls as its configuration requires.  Queues are
explicit SimPy resources, so waiting times, tails and time-outs emerge from
the simulation instead of being computed from formulas.

The emulator is used to validate the analytic model and the statistical test
sampler of :mod:`looplab.landscape` (experiment E1); the policy experiments
use the faster sampler.
"""
from __future__ import annotations

import numpy as np
import simpy

from .landscape import Landscape, _lognorm_sigma


def run_experiment(L: Landscape, x: int, n_sess: int, seed: int,
                   warm_s: float = 45.0, think: float = 5.0,
                   return_trace: bool = False) -> dict:
    """Run an online experiment of n_sess sessions on configuration x.

    Sessions keep arriving for warm_s seconds before and after the measured
    window, so the measured sessions see a system in steady state (the
    service is under its full production load during the experiment).
    """
    p, ev = L.p, L.ev
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    waf = simpy.Resource(env, capacity=2)
    app = simpy.Resource(env, capacity=int(ev["c_app"][x]))
    db = simpy.Resource(env, capacity=p.c_db)
    ml = simpy.Resource(env, capacity=p.c_ml)

    keys = {f.key: i for i, f in enumerate(p.features)}
    cdn = bool(x >> keys["CDN"] & 1) if "CDN" in keys else False
    s_app = float(ev["s_app"][x]); calls = float(ev["calls"][x])
    ml_s = float(ev["ml_s"][x]); pages = float(ev["pages"][x])
    ext = sum(f.ext_delay for i, f in enumerate(p.features) if x >> i & 1)
    bytes_ = float(ev["bytes"][x])
    net = {}
    for seg, rtt, bw in (("m", p.rtt_m, p.bw_m), ("d", p.rtt_d, p.bw_d)):
        rtt_eff = rtt * (1 - 0.65 * cdn) + 0.65 * cdn * p.rtt_edge
        net[seg] = p.k_rtt * rtt_eff + bytes_ * 8 / (bw * (1 + 0.3 * cdn))
    sig_net = float(_lognorm_sigma(0.5))
    base = {"m": p.base_conv_m * np.exp(_loglift(L, x, "m")),
            "d": p.base_conv_d * np.exp(_loglift(L, x, "d"))}

    page_times, sess_rec = [], []
    warmup = int(p.lam_s * warm_s)
    total = warmup + n_sess + warmup

    def page(seg):
        t0 = env.now
        nt = net[seg] * np.exp(rng.normal(-sig_net ** 2 / 2, sig_net))
        yield env.timeout(nt * 0.5)                      # request leg
        with waf.request() as r:
            yield r
            yield env.timeout(rng.exponential(0.0004))
        with app.request() as r:                         # load balancer -> pool
            got = yield r | env.timeout(p.timeout)
            if r not in got:
                return None
            yield env.timeout(rng.exponential(s_app))
            for _ in range(rng.poisson(calls)):
                with db.request() as rd:
                    yield rd
                    yield env.timeout(rng.exponential(p.s_db))
            if ml_s > 0:
                with ml.request() as rm:
                    yield rm
                    yield env.timeout(rng.exponential(ml_s))
        if ext > 0:
            yield env.timeout(rng.exponential(ext))
        yield env.timeout(nt * 0.5)                      # response leg
        dt = env.now - t0
        return dt if dt <= p.timeout else None

    def session(i, seg):
        k = 1 + rng.poisson(max(pages - 1, 0.0))
        times, failed = [], False
        for j in range(k):
            dt = yield env.process(page(seg))
            if dt is None:
                failed = True
                break
            times.append(dt)
            if j < k - 1:
                yield env.timeout(rng.exponential(think))
        if warmup <= i < warmup + n_sess:
            if failed:
                conv = 0
            else:
                tm = float(np.mean(times))
                pr = base[seg] * np.exp(-p.kappa * max(tm - p.t0, 0.0))
                conv = int(rng.random() < min(pr, 1.0))
            page_times.extend(times)
            sess_rec.append((seg, conv, failed, len(times)))

    def source():
        for i in range(total):
            seg = "m" if rng.random() < p.mobile_share else "d"
            env.process(session(i, seg))
            yield env.timeout(rng.exponential(1.0 / p.lam_s))

    env.process(source())
    env.run()
    rec = np.array([(s == "m", c, f, k) for s, c, f, k in sess_rec], float)
    pt = np.array(page_times) if page_times else np.array([p.timeout])
    conv_hat = rec[:, 1].mean()
    p95_hat = float(np.quantile(pt, 0.95))
    n_pages = rec[:, 3].sum() + rec[:, 2].sum()
    err_hat = rec[:, 2].sum() / max(n_pages, 1)
    cost_hat = ev["cost"][x] * (1 + rng.normal(0, 0.01))
    ud = L._ud(conv_hat)
    uf = L._uf(np.array([p95_hat]), np.array([err_hat]), ev["complexity"][x:x + 1])[0]
    uv = L._uv(L._profit(np.array([conv_hat]), np.array([x]), cost_hat))[0]
    out = dict(conv=conv_hat, p95=p95_hat, err=err_hat, ud=float(ud), uf=float(uf),
               uv=float(uv), U=float(np.dot([ud, uf, uv], L.w)),
               mean_page=float(pt.mean()), n=len(rec))
    if return_trace:
        out["page_times"] = pt
    return out


def _loglift(L: Landscape, x: int, seg: str) -> float:
    """Log-lift of conversion (main effects and interactions) of config x."""
    p = L.p
    X = np.array([[x >> i & 1 for i in range(L.n)]], float)
    F = p.features
    key = {f.key: i for i, f in enumerate(F)}
    lift = sum((f.lift_m if seg == "m" else f.lift_d) for i, f in enumerate(F) if x >> i & 1)
    for (a, b), v in p.interactions.items():
        if a in key and b in key and (x >> key[a] & 1) and (x >> key[b] & 1):
            lift += v
    if p.rand_inter is not None:
        xi = X[0]
        lift += float(xi @ p.rand_inter @ xi)
        for (i, j, k), v in p.rand_triples:
            lift += v * xi[i] * xi[j] * xi[k]
    if p.nk is not None:
        K, tau, nbrs, tables = p.nk
        f = 0.0
        for i in range(L.n):
            code = (x >> i) & 1
            for b, j in enumerate(nbrs[i]):
                code |= ((x >> int(j)) & 1) << (b + 1)
            f += tables[i][code]
        lift += tau * (f / L.n - 0.5)
    return float(lift)
