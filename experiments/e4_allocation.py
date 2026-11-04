"""E4  New configurations vs re-tests, at three test sizes under one traffic budget."""
from common import *  # noqa

TRAFFIC = 800_000
KNEW = (0.5, 1, 2, 3, 4, 5)
NS = (500, 2000, 8000)


def main():
    jobs = []
    for n in NS:
        budget = TRAFFIC // n
        cps = (budget,)
        for k in KNEW:
            kw = dict(policy="loop", n_sess=n, budget=budget, k_new=k, rotate=False, checkpoints=cps)
            for s in range(150):
                jobs.append(("ref", 0, dict(kw), s, dict(k_new=k, n=n)))
            for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
                for i in range(n_inst):
                    for s in range(5):
                        jobs.append((cls, i, dict(kw), s, dict(k_new=k, n=n)))
    rows = parallel(jobs, chunksize=2)
    save("e4_allocation.json", rows)


if __name__ == "__main__":
    main()
