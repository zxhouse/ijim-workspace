"""E7  Drifting criteria and an abrupt regime shift, with and without forgetting."""
from common import *  # noqa
from dataclasses import replace
from multiprocessing import Pool
from looplab.policies import Engine

AMPS = (0.0, 0.05, 0.10, 0.20)
GAMMAS = (1.0, 0.98, 0.95, 0.90)
CP = tuple(range(25, 401, 25))


def weights_fn(amp, seed, w0=(0.45, 0.25, 0.30), period=30):
    ph = np.random.default_rng(seed).uniform(0, 2 * np.pi, 3)

    def f(k):
        w = np.array(w0) + amp * np.sin(2 * np.pi * k / period + ph)
        w = np.maximum(w, 0.05)
        return w / w.sum()
    return f


class ShiftEngine(Engine):
    def __init__(self, L, cfg, seed, L2, at):
        super().__init__(L, cfg, seed)
        self.L2, self.at, self.done = L2, at, False

    def _drift(self):
        super()._drift()
        if not self.done and self.tests >= self.at:
            self.L, self.U_now, self.done = self.L2, self.L2.U, True


@lru_cache(maxsize=64)
def shifted(cls, i):
    L = get_landscape(cls, i)
    p = replace(L.p, lam_s=L.p.lam_s * 1.3, mobile_share=min(L.p.mobile_share + 0.15, 0.9))
    return Landscape(p, L.name + "-shift")


def job(args):
    mode, cls, i, amp, g, seed = args
    L = get_landscape(cls, i)
    sig = get_sigma(cls, i, 2000)
    rows = []
    if mode == "drift":
        f = weights_fn(amp, 7000 + seed)
        cfg = Config(policy="ledger", sigma=sig, rho=RHO0, drift=f, forget=g, checkpoints=CP)
        E = Engine(L, cfg, seed)
        log = E.run()
        # empirical drift bound D over the run
        rounds = E.round
        Ub = L.U
        D = max(float(np.max(np.abs(L.C @ f(k) - Ub))) for k in range(1, rounds + 1)) if amp > 0 else 0.0
        for r in log:
            r = dict(r, mode=mode, cls=cls, inst=i, amp=amp, gamma=g, seed=seed, D=D,
                     track=100 * r["shipped"] / r["ustar"])
            rows.append(r)
        L.set_weights(L.p.w)
    else:
        L2 = shifted(cls, i)
        cfg = Config(policy="ledger", sigma=sig, rho=RHO0, forget=g, checkpoints=CP)
        E = ShiftEngine(L, cfg, seed, L2, 200)
        log = E.run()
        for r in log:
            rows.append(dict(r, mode=mode, cls=cls, inst=i, amp=0.0, gamma=g, seed=seed, D=0.0,
                             track=100 * r["shipped"] / r["ustar"]))
    return rows


def main():
    jobs = []
    for g in GAMMAS:
        for amp in AMPS:
            for s in range(100):
                jobs.append(("drift", "ref", 0, amp, g, s))
            for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
                for i in range(n_inst):
                    for s in range(3):
                        jobs.append(("drift", cls, i, amp, g, s))
        for s in range(150):
            jobs.append(("shift", "ref", 0, 0.0, g, s))
        for cls, n_inst in (("svc", N_SVC), ("rug", N_RUG)):
            for i in range(n_inst):
                for s in range(4):
                    jobs.append(("shift", cls, i, 0.0, g, s))
    t = time.time()
    with Pool(os.cpu_count()) as P:
        res = P.map(job, jobs, chunksize=4)
    print(f"{len(jobs)} runs in {time.time()-t:.0f}s")
    save("e7_drift.json", [r for rr in res for r in rr])


if __name__ == "__main__":
    main()
