"""E1  Testbed validation: discrete-event emulation vs analytic model and sampler.

(a) agreement of criteria and utility on stratified configurations,
(b) calibration of test noise as a function of test size,
(c) structure of the landscapes (optima, spread, noise ratio).
"""
from common import *  # noqa
from multiprocessing import Pool
from looplab.des import run_experiment


def des_job(args):
    x, n, seed = args
    L = get_landscape("ref", 0)
    r = run_experiment(L, int(x), int(n), int(seed))
    return dict(x=int(x), n=int(n), seed=int(seed), **{k: r[k] for k in ("conv", "p95", "err", "ud", "uf", "uv", "U", "mean_page")})


def main():
    L = get_landscape("ref", 0)
    ev = L.ev
    rng = np.random.default_rng(11)
    rho = ev["rho_max"]
    stable = np.flatnonzero(rho < 0.85)
    near = np.flatnonzero((rho >= 0.85) & (rho < 0.97))
    over = np.flatnonzero(rho >= 0.97)
    pick = np.concatenate([rng.choice(stable, 90, replace=False), rng.choice(near, 30, replace=False),
                           rng.choice(over, 20, replace=False), [L.opt]])
    jobs = [(x, 6000, 50000 + k) for k, x in enumerate(pick)]
    # noise calibration: six configurations spanning the utility range
    order = np.argsort(L.U)
    calib = [int(order[int(q * (L.N - 1))]) for q in (0.5, 0.7, 0.85, 0.95, 0.99)] + [L.opt]
    calib = [x for x in calib if rho[x] < 0.97]
    for x in calib:
        for n in (500, 1000, 2000, 4000):
            for r in range(20):
                jobs.append((x, n, 90000 + 100 * r + n))
    t = time.time()
    with Pool(os.cpu_count()) as P:
        res = P.map(des_job, jobs, chunksize=2)
    print(f"DES: {len(jobs)} experiments in {time.time()-t:.0f}s")
    agree = [r for r in res if r["n"] == 6000 and r["seed"] < 90000]
    for r in agree:
        x = r["x"]
        r.update(U_an=float(L.U[x]), conv_an=float(ev["conv"][x]), p95_an=float(ev["p95"][x]),
                 rho=float(rho[x]), stratum=("stable" if rho[x] < 0.85 else "near" if rho[x] < 0.97 else "overload"))
    cal = [r for r in res if r["seed"] >= 90000]
    # sampler noise for the same configurations
    srng = np.random.default_rng(5)
    samp = {}
    for x in calib:
        for n in (500, 1000, 2000, 4000):
            y = L.measure(np.full(2000, x), n, srng)
            samp[(x, n)] = (float(y.mean()), float(y.std(ddof=1)))
    calrows = []
    for x in calib:
        for n in (500, 1000, 2000, 4000):
            yy = np.array([r["U"] for r in cal if r["x"] == x and r["n"] == n])
            calrows.append(dict(x=x, n=n, U=float(L.U[x]), des_mean=float(yy.mean()), des_sd=float(yy.std(ddof=1)),
                                samp_mean=samp[(x, n)][0], samp_sd=samp[(x, n)][1], reps=len(yy)))
    # landscape structure
    struct = []
    for cls, insts in classes():
        for i in insts:
            Li = get_landscape(cls, i)
            s = Li.summary()
            s["sigma2000"] = get_sigma(cls, i, 2000)
            s["sigma500"] = get_sigma(cls, i, 500)
            s["sigma8000"] = get_sigma(cls, i, 8000)
            top = np.sort(Li.U)[-50:]
            s["top50_sd"] = float(top.std())
            s["cls"] = cls
            struct.append(s)
    save("e1_validation.json", dict(agree=agree, calib=calrows, struct=struct))


if __name__ == "__main__":
    main()
