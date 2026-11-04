"""E5  Generative-AI ideation: screening validity x idea volume x homogenisation."""
from common import *  # noqa

RHOS = (0.0, 0.25, 0.5, 0.75, 0.9)
VOLS = (1, 5, 20)
HOMS = (0.0, 0.5, 0.9)


def main():
    jobs = []
    for rho in RHOS:
        for V in VOLS:
            for h in HOMS:
                kw = dict(policy="ledger", rho=rho, ideas=V, homog=h, checkpoints=(100, 400))
                tag = dict(rho=rho, V=V, h=h)
                for s in range(60):
                    jobs.append(("ref", 0, dict(kw), s, tag))
                for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
                    for i in range(n_inst):
                        for s in range(3):
                            jobs.append((cls, i, dict(kw), s, tag))
    rows = parallel(jobs)
    save("e5_genai.json", rows)


if __name__ == "__main__":
    main()
