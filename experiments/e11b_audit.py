"""E11b  Audit follow-ups: pool-based screening for A/B, online sigma, ledger build rate x start."""
from common import *  # noqa
from multiprocessing import Pool
from e11_audit import job, units


def main():
    jobs = []
    conds = [("ladder", "L2b + screen from the idea pool", dict(policy="abtest", ab_pool=True, ab_retain=True, ab_poolpick=True)),
             ("sigma", "ledger learned sigma", dict(policy="ledger", sigma_learn=True)),
             ("sigma", "loop learned sigma", dict(policy="loop", sigma_learn=True))]
    for part, name, kw in conds:
        for cls, i, s in units():
            jobs.append((part, cls, i, dict(kw), s, dict(pol=name, factor="learned", start="random")))
    for k in (1, 2, 3):
        for st in ("random", "statusquo"):
            for cls, i, s in units():
                jobs.append(("knew", cls, i, dict(policy="ledger", k_new=k, rotate=False, start=st), s, dict(pol=f"ledger k_new={k}", start=st, k_new=k)))
    t = time.time()
    with Pool(os.cpu_count()) as P:
        res = P.map(job, jobs, chunksize=4)
    print(f"{len(jobs)} runs in {time.time()-t:.0f}s")
    save("e11b_audit.json", [r for rr in res for r in rr])


if __name__ == "__main__":
    main()
