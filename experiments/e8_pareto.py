"""E8  Several stakeholders: Pareto archive vs scalarised loops."""
from common import *  # noqa
from multiprocessing import Pool
from looplab.policies import ParetoEngine

W_SCAL = ((0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6))
MC = np.random.default_rng(3).uniform(0, 1, (20000, 3))


def hv(P):
    P = np.asarray(P)
    if len(P) == 0:
        return 0.0
    dom = np.zeros(len(MC), bool)
    for p in P:
        dom |= np.all(MC <= p[None, :], 1)
    return float(dom.mean())


@lru_cache(maxsize=64)
def front(cls, i):
    L = get_landscape(cls, i)
    C = L.C
    # non-dominated set of all configurations (vectorised in blocks)
    nd = np.ones(L.N, bool)
    for a in range(0, L.N, 512):
        blk = C[a:a + 512]
        dom = np.all(C[None, :, :] >= blk[:, None, :], 2) & np.any(C[None, :, :] > blk[:, None, :], 2)
        nd[a:a + 512] = ~dom.any(1)
    idx = np.flatnonzero(nd)
    return idx, hv(C[idx])


def local_pareto(L, x):
    nb = L.neighbours(x, 2)
    Cx, Cn = L.C[x], L.C[nb]
    return not np.any(np.all(Cn >= Cx, 1) & np.any(Cn > Cx, 1))


def job(args):
    cls, i, seed, budget = args
    L = get_landscape(cls, i)
    sig = get_sigma(cls, i, 2000)
    F, hv_star = front(cls, i)
    Fset = set(F.tolist())
    out = []
    # Pareto archive
    cfg = Config(policy="loop", sigma=sig, rho=RHO0, budget=budget)
    E = ParetoEngine(L, cfg, seed)
    arch = [int(a) for a in E.run()]
    # scalarised: three loops with fixed weights, budget split
    sc = []
    for k, w in enumerate(W_SCAL):
        L.set_weights(w)
        cfgk = Config(policy="loop", sigma=L.sigma(2000), rho=RHO0, budget=budget // 3,
                      checkpoints=(budget // 3,))
        log, Ek = run(L, cfgk, seed * 10 + k)
        sc.append(int(log[-1]["ship_x"]))
    L.set_weights(L.p.w)
    # single DVF-weighted loop with the full budget
    log, E1 = run(L, Config(policy="loop", sigma=sig, rho=RHO0, budget=budget, checkpoints=(budget,)), seed)
    single = [int(log[-1]["ship_x"])]
    for name, S in (("archive", arch), ("scalarised3", sc), ("single", single)):
        S = sorted(set(S))
        out.append(dict(cls=cls, inst=i, seed=seed, budget=budget, method=name, size=len(S),
                        hv=hv(L.C[S]) / hv_star,
                        share_global=float(np.mean([x in Fset for x in S])),
                        share_local=float(np.mean([local_pareto(L, x) for x in S])),
                        best_U=float(L.U[S].max() / L.Ustar)))
    return out


def main():
    jobs = []
    for budget in (200, 400, 800):
        for s in range(60):
            jobs.append(("ref", 0, s, budget))
        for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
            for i in range(n_inst):
                for s in range(3):
                    jobs.append((cls, i, s, budget))
    t = time.time()
    with Pool(os.cpu_count()) as P:
        res = P.map(job, jobs, chunksize=2)
    print(f"{len(jobs)} runs in {time.time()-t:.0f}s")
    fronts = {f"{c}{i}": len(front(c, i)[0]) for c, ins in classes() for i in ins}
    save("e8_pareto.json", dict(rows=[r for rr in res for r in rr], fronts=fronts))


if __name__ == "__main__":
    main()
