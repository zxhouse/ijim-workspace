"""E3  Experimentation-governance policies under one testing budget."""
from common import *  # noqa

POLICIES = ("random", "abtest", "oneshot", "loop", "ledger", "thompson")


def main():
    jobs = []
    for n in (500, 2000):
        for pol in POLICIES:
            for s in range(300 if n == 2000 else 150):
                jobs.append(("ref", 0, dict(policy=pol, n_sess=n), s, dict(pol=pol, n=n)))
            for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
                for i in range(n_inst):
                    for s in range(10 if n == 2000 else 5):
                        jobs.append((cls, i, dict(policy=pol, n_sess=n), s, dict(pol=pol, n=n)))
    rows = parallel(jobs)
    save("e3_policies.json", rows)


if __name__ == "__main__":
    main()
