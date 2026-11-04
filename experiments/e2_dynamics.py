"""E2  Dynamics of the loop: shipped vs found vs believed, and distance to the limit."""
from common import *  # noqa

CP = tuple(range(25, 401, 25))
CP_LONG = (100, 200, 400, 800, 1200, 1600, 2400, 3200)


def main():
    jobs = []
    for pol in ("loop", "ledger"):
        for s in range(300):
            jobs.append(("ref", 0, dict(policy=pol, checkpoints=CP), s, dict(pol=pol, run="short")))
        for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
            for i in range(n_inst):
                for s in range(8):
                    jobs.append((cls, i, dict(policy=pol, checkpoints=CP), s, dict(pol=pol, run="short")))
    for s in range(100):
        jobs.append(("ref", 0, dict(policy="loop", budget=3200, checkpoints=CP_LONG), 10_000 + s, dict(pol="loop", run="long")))
    for cls in ("svc", "rug"):
        for i in range(10):
            for s in range(6):
                jobs.append((cls, i, dict(policy="loop", budget=3200, checkpoints=CP_LONG), 10_000 + s, dict(pol="loop", run="long")))
    rows = parallel(jobs)
    save("e2_dynamics.json", rows)


if __name__ == "__main__":
    main()
