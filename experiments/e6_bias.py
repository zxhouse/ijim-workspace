"""E6  Measurement bias: favourite (HiPPO), novelty and instrumentation bias."""
from common import *  # noqa

RATIOS = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)


def main():
    jobs = []
    combos = [("hippo", 500), ("hippo", 2000), ("hippo", 8000), ("novelty", 2000), ("instrument", 2000),
              ("instrument_audit", 2000)]
    for kind0, n in combos:
        kind = "instrument" if kind0 == "instrument_audit" else kind0
        audit = 10 if kind0 == "instrument_audit" else 0
        for r in RATIOS:
            for cls, insts, seeds in (("ref", [0], 120), ("svc", range(N_SVC), 4), ("rug", range(N_RUG), 4)):
                for i in insts:
                    sig = get_sigma(cls, i, n)
                    kw = dict(policy="ledger", n_sess=n, bias_kind=kind, bias=r * sig, sigma=sig,
                              checkpoints=(400,), audit=audit)
                    for s in range(seeds):
                        jobs.append((cls, i, dict(kw), s, dict(kind=kind0, n=n, ratio=r, b=r * sig)))
    rows = parallel(jobs)
    save("e6_bias.json", rows)


if __name__ == "__main__":
    main()
