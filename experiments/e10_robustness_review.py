"""E10  Robustness checks requested in review round 1.

(a) stronger champion-challenger baselines (pooled champion evidence, looser rule);
(b) sensitivity of the ledger to kappa in its ship rule;
(c) model misspecification: true utilities perturbed by an error of the size
    measured in E1 (s.d. 0.044) and twice that.
"""
from common import *  # noqa
from multiprocessing import Pool


def job(args):
    part, cls, i, kw, seed, tag = args
    L = get_landscape(cls, i)
    sd = kw.pop("_perturb", 0.0)
    L.perturb(sd, seed=9000 + i)
    try:
        sig = L.sigma(2000)
        cfg = Config(sigma=sig, rho=RHO0, checkpoints=(400,), **kw)
        log, E = run(L, cfg, seed)
    finally:
        L.perturb(0.0)
    r = dict(log[-1], part=part, cls=cls, inst=i, seed=seed, **tag)
    r["shipped_pct"] = 100 * r["shipped"] / r["ustar"]
    r["found_pct"] = 100 * r["found"] / r["ustar"]
    r["belief_pct"] = 100 * r["belief"] / r["ustar"]
    return r


def units():
    yield from (("ref", 0, s) for s in range(150))
    for cls, n in (("svc", N_SVC), ("rug", N_RUG)):
        for i in range(n):
            for s in range(5):
                yield cls, i, s


def main():
    jobs = []
    ab = {"A/B (5%, no pooling)": dict(policy="abtest"),
          "A/B pooled (5%)": dict(policy="abtest", ab_pool=True),
          "A/B ship-higher": dict(policy="abtest", alpha_z=0.0),
          "A/B pooled ship-higher": dict(policy="abtest", ab_pool=True, alpha_z=0.0),
          "ledger": dict(policy="ledger")}
    for name, kw in ab.items():
        for cls, i, s in units():
            jobs.append(("ab", cls, i, dict(kw), s, dict(pol=name)))
    for k in (0.0, 0.5, 1.0, 1.5, 2.0):
        for cls, i, s in units():
            jobs.append(("kappa", cls, i, dict(policy="ledger", lcb_k=k), s, dict(pol=f"kappa={k}", kappa=k)))
    for sd in (0.0, 0.044, 0.088):
        for pol in ("abtest", "oneshot", "loop", "ledger"):
            for cls, i, s in units():
                jobs.append(("perturb", cls, i, dict(policy=pol, _perturb=sd), s, dict(pol=pol, sd=sd)))
    t = time.time()
    with Pool(os.cpu_count()) as P:
        rows = P.map(job, jobs, chunksize=4)
    print(f"{len(jobs)} runs in {time.time()-t:.0f}s")
    save("e10_review.json", rows)


if __name__ == "__main__":
    main()
