"""E11  Audit experiments.

(a) decomposition of the ledger's advantage along the design principles:
    A/B -> +pooling (DP1 evidence) -> +retention of all variants (DP1) ->
    +re-tests of the favourite (DP4) -> +re-tests of three leaders -> +rotation
    -> +ship on a lower bound (DP5);
(b) misspecified test noise: beliefs assume sigma_factor x the true sigma;
(c) realistic start: the production configuration with free history instead
    of five random configurations.
"""
from common import *  # noqa
from multiprocessing import Pool


def job(args):
    part, cls, i, kw, seed, tag = args
    L = get_landscape(cls, i)
    sig = get_sigma(cls, i, 2000)
    cfg = Config(sigma=sig, rho=RHO0, checkpoints=(50, 100, 200, 400), **kw)
    log, E = run(L, cfg, seed)
    out = []
    for r in log:
        r = dict(r, part=part, cls=cls, inst=i, seed=seed, **tag)
        r["shipped_pct"] = 100 * r["shipped"] / r["ustar"]
        r["found_pct"] = 100 * r["found"] / r["ustar"]
        r["belief_pct"] = 100 * r["belief"] / r["ustar"]
        out.append(r)
    return out


def units():
    yield from (("ref", 0, s) for s in range(150))
    for cls, n in (("svc", N_SVC), ("rug", N_RUG)):
        for i in range(n):
            for s in range(5):
                yield cls, i, s


LADDER = [
    ("L0 A/B, one test per arm", dict(policy="abtest")),
    ("L1 + pool champion evidence", dict(policy="abtest", ab_pool=True)),
    ("L2 + retain all variants", dict(policy="abtest", ab_pool=True, ab_retain=True)),
    ("L3 + re-test favourite 4x/round", dict(policy="loop", leaders=1, rotate=False)),
    ("L4 + re-test three leaders", dict(policy="loop", leaders=3, rotate=False)),
    ("L5 + rotating re-test (loop)", dict(policy="loop")),
    ("L6 + ship on lower bound", dict(policy="loop", ship="lcb")),
    ("L7 + three builds per round (ledger)", dict(policy="ledger")),
    ("launch-and-learn", dict(policy="oneshot")),
]


def main():
    jobs = []
    for name, kw in LADDER:
        for cls, i, s in units():
            jobs.append(("ladder", cls, i, dict(kw), s, dict(pol=name)))
    for f in (0.5, 1.0, 1.3, 2.0):
        for pol in ("loop", "ledger", "thompson", "oneshot"):
            for cls, i, s in units():
                jobs.append(("sigma", cls, i, dict(policy=pol, sigma_factor=f), s, dict(pol=pol, factor=f)))
    for pol, kw in (("abtest_pooled", dict(policy="abtest", ab_pool=True)), ("oneshot", dict(policy="oneshot")),
                    ("loop", dict(policy="loop")), ("ledger", dict(policy="ledger")), ("thompson", dict(policy="thompson"))):
        for st in ("random", "statusquo"):
            for cls, i, s in units():
                jobs.append(("start", cls, i, dict(kw, start=st), s, dict(pol=pol, start=st)))
    t = time.time()
    with Pool(os.cpu_count()) as P:
        res = P.map(job, jobs, chunksize=4)
    print(f"{len(jobs)} runs in {time.time()-t:.0f}s")
    save("e11_audit.json", [r for rr in res for r in rr])


if __name__ == "__main__":
    main()
