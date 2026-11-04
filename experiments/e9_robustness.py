"""E9  Robustness meta-experiment over randomly drawn scenarios."""
from common import *  # noqa

POLS = ("abtest", "oneshot", "loop", "ledger")


def scenarios(n=120, seed=42):
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        fam = str(rng.choice(["svc", "rug"]))
        nf = int(rng.choice([10, 12, 14]))
        out.append(dict(
            sid=k, fam=fam, inst=int(rng.integers(0, N_SVC if fam == "svc" else N_RUG)),
            nf=nf, n_sess=int(np.exp(rng.uniform(np.log(400), np.log(8000)))),
            budget=int(rng.choice([100, 200, 400, 800])),
            rho=float(rng.uniform(0.2, 0.8)), V=int(rng.integers(2, 16)),
            radius=int(rng.choice([1, 2, 3]))))
    return out


def main():
    jobs = []
    for sc in scenarios():
        n_extra = 2 if sc["nf"] == 14 else 0
        drop = ("CHAT", "AUTOC") if sc["nf"] == 10 else ()
        for pol in POLS:
            kw = dict(policy=pol, n_sess=sc["n_sess"], budget=sc["budget"], rho=sc["rho"],
                      ideas=sc["V"], radius=sc["radius"], checkpoints=(sc["budget"],),
                      _n_extra=n_extra, _drop=list(drop))
            for s in range(12):
                jobs.append((sc["fam"], sc["inst"], dict(kw), s, dict(pol=pol, **{k: v for k, v in sc.items() if k != "inst"})))
    rows = parallel(jobs, chunksize=2)
    save("e9_robustness.json", rows)


if __name__ == "__main__":
    main()
