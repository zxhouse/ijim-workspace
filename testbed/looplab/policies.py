"""Experimentation policies run against a :class:`Landscape`.

All policies share one engine: a dense ledger of evidence (sum and count of
test results for every configuration), conjugate normal beliefs, an idea pool
with rough pre-screening estimates, and a test budget.  Policies differ in
how they generate ideas, which tests they run and what they ship.

Policies
--------
loop        the iterate-test loop of the design-thinking model (baseline)
oneshot     every test on a new configuration ("launch and learn")
abtest      champion-challenger A/B testing with a significance rule
ledger      evidence-ledger loop: the loop plus a ship decision that
            discounts thin evidence (lower confidence bound)
thompson    Thompson sampling with arrivals of new arms
random      random search among variants
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .landscape import Landscape


@dataclass
class Config:
    policy: str = "loop"
    budget: int = 400               # number of tests
    n_sess: int = 2000              # sessions per test
    sigma: float | None = None      # s.d. of a test assumed by the beliefs
    ideas: int = 5                  # ideas proposed per round
    radius: int = 2                 # ideation reach (Hamming radius)
    leaders: int = 3
    tests_per_round: int = 5
    k_new: float = 1.0              # new configurations built per round
    rotate: bool = True             # rotating re-test (Assumption 4)
    prescreen: bool = True
    rho: float | None = None        # validity of pre-screening (None: one-test equivalent)
    homog: float = 0.0              # homogenisation of generated ideas (0..1)
    homog_k: int = 4                # size of the favoured feature subset
    prior: tuple = (0.5, 0.08)      # (mean, variance) of the belief prior
    eb_prior: bool = False          # empirical-Bayes prior (ledger)
    ship: str = "mean"              # "mean" or "lcb"
    lcb_k: float = 1.0
    retest: str = "top"             # "top" or "ttts"
    alpha_z: float = 1.645          # A/B decision threshold (one-sided 5 %)
    n_init: int = 5
    checkpoints: tuple = (25, 50, 100, 200, 300, 400)
    # bias injection: kind in {None, "hippo", "novelty", "instrument"}
    bias_kind: str | None = None
    bias: float = 0.0
    bias_feature: int = 11          # TELEM for instrumentation bias
    audit: int = 0                  # audit tests that estimate instrumentation bias
    ab_pool: bool = False           # A/B: pool the champion's evidence across experiments
    # drift: callable round -> weights, and forgetting factor
    drift: object = None
    forget: float = 1.0
    retain: int | None = None       # keep only the best `retain` configurations
    reco: dict = field(default_factory=dict)


class Engine:
    def __init__(self, L: Landscape, cfg: Config, seed: int):
        self.L, self.c = L, cfg
        self.rng = np.random.default_rng(seed)
        N = L.N
        self.S = np.zeros(N); self.Cn = np.zeros(N); self.first = np.full(N, np.nan)
        self.built: list[int] = []
        self.is_built = np.zeros(N, bool)
        self.est = np.full(N, np.nan)      # rough estimate of unbuilt ideas
        self.in_pool = np.zeros(N, bool)
        self.tests = 0
        self.sigma = cfg.sigma if cfg.sigma is not None else L.sigma(cfg.n_sess)
        self.m0, self.v0 = cfg.prior
        rho = cfg.rho
        if rho is None:  # as informative as one test
            rho = L.U.std() / np.sqrt(L.U.std() ** 2 + self.sigma ** 2)
        self.rho = float(rho)
        self.zU = (L.U - L.U.mean()) / L.U.std()
        self.fav_set = self.rng.choice(L.n, cfg.homog_k, replace=False)
        self.rot = 0
        self.round = 0
        self.log = []
        self.cp = list(cfg.checkpoints)
        self.U_now = L.U
        self.b_hat = 0.0
        if cfg.audit > 0 and cfg.bias_kind == "instrument":
            # A/A-style audit: each audit test compares the instrumented and a
            # server-side measurement of the same sessions, so it observes the
            # bias with noise sigma*sqrt(2); the ledger then corrects tests.
            self.b_hat = float(cfg.bias + self.rng.normal(0, self.sigma * np.sqrt(2.0 / cfg.audit)))
            self.tests += cfg.audit

    # ----------------------------------------------------------- beliefs --
    def post(self, idx=None):
        prec0 = 1.0 / self.v0
        s2 = self.sigma ** 2
        S = self.S if idx is None else self.S[idx]
        C = self.Cn if idx is None else self.Cn[idx]
        prec = prec0 + C / s2
        m0 = self.m0 if np.isscalar(self.m0) or idx is None else self.m0[idx]
        mu = (m0 * prec0 + S / s2) / prec
        return np.clip(mu, 0, 1), 1.0 / prec

    def update_eb(self):
        """Empirical-Bayes prior with the pre-screening score as covariate.

        The first test result of every built configuration is regressed on
        its rough estimate; the fitted value is the prior mean of each
        configuration and the residual variance net of test noise is the
        prior variance.  Shrinkage is therefore towards what the screen
        predicted, not towards a global mean.
        """
        b = np.array(self.built)
        f = self.first[b]; e = self.est[b]
        ok = ~np.isnan(f) & ~np.isnan(e)
        if ok.sum() >= 6:
            A = np.stack([np.ones(ok.sum()), e[ok]], 1)
            coef, *_ = np.linalg.lstsq(A, f[ok], rcond=None)
            res = f[ok] - A @ coef
            v = np.var(res, ddof=2) - self.sigma ** 2
            self.v0 = float(max(v, 0.25 * self.sigma ** 2 / ok.sum(), 1e-4))
            M0 = coef[0] + coef[1] * np.nan_to_num(self.est, nan=0.0)
            self.m0 = np.clip(M0, 0, 1)

    def leaders(self, k):
        b = np.array(self.built)
        mu, _ = self.post(b)
        return b[np.argsort(-mu)[:k]]

    def favourite(self):
        b = np.array(self.built)
        mu, var = self.post(b)
        return int(b[np.argmax(mu)])

    def shipped(self):
        b = np.array(self.built)
        mu, var = self.post(b)
        if self.c.ship == "lcb":
            return int(b[np.argmax(mu - self.c.lcb_k * np.sqrt(var))])
        return int(b[np.argmax(mu)])

    # ------------------------------------------------------------- tests --
    def _bias(self, xs, kinds):
        c = self.c
        if c.bias_kind is None or c.bias == 0:
            return 0.0
        b = np.zeros(len(xs))
        if c.bias_kind == "hippo":
            fav = self.favourite() if self.built else -1
            b[(xs == fav) & (kinds == 1)] = c.bias
        elif c.bias_kind == "novelty":
            b[kinds == 0] = c.bias
        elif c.bias_kind == "instrument":
            b[(xs >> c.bias_feature) & 1 == 1] = c.bias - self.b_hat
        return b

    def test(self, xs, kinds):
        """Run tests on xs; kinds: 0 = first test of a new build, 1 = re-test."""
        xs = np.asarray(xs, dtype=np.int64); kinds = np.asarray(kinds)
        room = self.c.budget - self.tests
        if room <= 0:
            return
        xs, kinds = xs[:room], kinds[:room]
        y = self.L.measure(xs, self.c.n_sess, self.rng) + self._bias(xs, kinds)
        for x, v in zip(xs, y):
            if np.isnan(self.first[x]):
                self.first[x] = v
            self.S[x] += v; self.Cn[x] += 1
        before = self.tests
        self.tests += len(xs)
        while self.cp and self.tests >= self.cp[0] and before < self.cp[0]:
            self.record(self.cp.pop(0))

    def build(self, x):
        x = int(x)
        if not self.is_built[x]:
            self.is_built[x] = True
            self.built.append(x)
            self.in_pool[x] = False
            if self.c.retain is not None and len(self.built) > self.c.retain:
                self._prune()

    def _prune(self):
        b = np.array(self.built)
        mu, _ = self.post(b)
        keep = b[np.argsort(-mu)[: self.c.retain]]
        drop = np.setdiff1d(b, keep)
        self.built = [int(v) for v in keep]
        # discarded configurations lose their evidence, but stay "built"
        # so they are not proposed again
        self.S[drop] = 0; self.Cn[drop] = 0

    # ------------------------------------------------------------- ideas --
    def rough(self, xs):
        e = self.rho * self.zU[xs] + np.sqrt(max(1 - self.rho ** 2, 0)) * self.rng.normal(size=len(xs))
        return e

    def propose(self, parent, k=None):
        c, L = self.c, self.L
        k = c.ideas if k is None else k
        out = []
        for _ in range(k):
            if c.radius >= L.n:
                x = int(self.rng.integers(L.N))
            else:
                m = int(self.rng.integers(1, c.radius + 1))
                if c.homog > 0 and self.rng.random() < c.homog:
                    bits = self.rng.choice(self.fav_set, min(m, len(self.fav_set)), replace=False)
                else:
                    bits = self.rng.choice(L.n, m, replace=False)
                x = parent
                for bt in bits:
                    x ^= 1 << int(bt)
            if not self.is_built[x]:
                out.append(x)
        out = np.array(sorted(set(out)), dtype=np.int64)
        new = out[~self.in_pool[out]] if len(out) else out
        if len(new):
            self.est[new] = self.rough(new)
            self.in_pool[new] = True
        return out

    def pick_build(self, round_ideas):
        if self.c.prescreen:
            pool = np.flatnonzero(self.in_pool)
            if len(pool) == 0:
                return None
            return int(pool[np.argmax(self.est[pool])])
        if len(round_ideas) == 0:
            return None
        return int(self.rng.choice(round_ideas))

    # ------------------------------------------------------------ record --
    def record(self, t):
        if not self.built:
            return
        L = self.L
        U = self.U_now
        x = self.shipped()
        b = np.array(self.built)
        mu, _ = self.post(np.array([x]))
        ever = np.flatnonzero(self.is_built)
        self.log.append(dict(
            tests=t, shipped=float(U[x]), found=float(U[ever].max()),
            belief=float(mu[0]), ustar=float(U.max()),
            local_opt=bool(L.local_gap(x, 2, U) <= 0),
            found_local_opt=bool(L.local_gap(int(ever[np.argmax(U[ever])]), 2, U) <= 0),
            gap=float(L.local_gap(x, 2, U)), n_built=len(ever), ship_x=int(x)))

    # --------------------------------------------------------------- run --
    def init(self):
        xs = self.rng.choice(self.L.N, self.c.n_init, replace=False)
        self.est[xs] = self.rough(xs)     # starting ideas get a screen score too
        for x in xs:
            self.build(x)
        self.test(xs, np.zeros(len(xs), int))
        if self.c.eb_prior:
            self.update_eb()

    def run(self):
        w0 = self.L.w.copy()
        try:
            getattr(self, "run_" + self.c.policy)()
        finally:
            if self.c.drift is not None:
                self.L.set_weights(w0)
            if self.cp:  # budget exhausted before a checkpoint was reached
                for t in self.cp:
                    self.record(t)
        return self.log

    def _drift(self):
        c = self.c
        if c.drift is not None:
            self.L.set_weights(c.drift(self.round))
            self.U_now = self.L.U
        if c.forget < 1.0:
            self.S *= c.forget; self.Cn *= c.forget

    def run_loop(self):
        c = self.c
        self.init()
        acc = 0.0
        while self.tests < c.budget:
            self.round += 1
            self._drift()
            leaders = self.leaders(c.leaders)
            parent = int(self.rng.choice(leaders))
            ideas = self.propose(parent)
            acc += c.k_new
            nb = int(acc); acc -= nb
            new = []
            for _ in range(nb):
                x = self.pick_build(ideas)
                if x is None:
                    break
                self.build(x); new.append(x)
                ideas = ideas[ideas != x]
            xs = list(new); kinds = [0] * len(new)
            n_re = c.tests_per_round - len(new) - (1 if c.rotate else 0)
            n_re = max(n_re, 0)
            if c.retest == "ttts":
                re = self._ttts(n_re, exclude=set(new))
            else:
                lead = [int(v) for v in self.leaders(c.leaders) if v not in new]
                re = [lead[i % len(lead)] for i in range(n_re)] if lead else []
            xs += re; kinds += [1] * len(re)
            if c.rotate and self.built:
                self.rot = (self.rot + 1) % len(self.built)
                xs.append(self.built[self.rot]); kinds.append(1)
            self.test(xs, kinds)
            if c.eb_prior:
                self.update_eb()

    def _ttts(self, k, exclude=()):
        b = np.array(self.built)
        mu, var = self.post(b)
        sd = np.sqrt(var)
        chosen = []
        for _ in range(k):
            for _try in range(20):
                th = mu + sd * self.rng.normal(size=len(b))
                x = int(b[np.argmax(th)])
                if x not in chosen and x not in exclude:
                    break
            chosen.append(x)
        return chosen

    def run_ledger(self):
        """Evidence-ledger loop.

        The loop of the design-thinking model plus a shipping rule that
        discounts thin evidence (lower confidence bound of the belief).
        The ledger keeps every tested configuration with its evidence count
        (retention), re-tests the leaders and a rotating member, and ships
        the configuration whose belief minus ``lcb_k`` posterior standard
        deviations is highest.
        """
        self.c.ship = "lcb"
        self.run_loop()

    def run_oneshot(self):
        c = self.c
        c.k_new = c.tests_per_round
        c.rotate = False
        self.run_loop()

    def run_thompson(self):
        c = self.c
        self.init()
        every = max(int(round(c.tests_per_round / max(c.k_new, 1e-9))), 1)
        while self.tests < c.budget:
            self.round += 1
            self._drift()
            if self.tests % every == 0:
                fav = self.favourite()
                ideas = self.propose(fav)
                x = self.pick_build(ideas)
                if x is not None:
                    self.build(x); self.test([x], [0]); continue
            b = np.array(self.built)
            mu, var = self.post(b)
            th = mu + np.sqrt(var) * self.rng.normal(size=len(b))
            self.test([int(b[np.argmax(th)])], [1])

    def run_random(self):
        c = self.c
        self.init()
        while self.tests < c.budget:
            self.round += 1
            parent = int(self.rng.choice(self.built))
            ideas = self.propose(parent, 1)
            if len(ideas) == 0:
                continue
            x = int(ideas[0]); self.build(x); self.test([x], [0])


class ABEngine(Engine):
    """Champion-challenger A/B testing.

    Each round runs a two-arm experiment (challenger vs current champion, one
    test each) and replaces the champion if the challenger wins at the
    one-sided 5 % level.  Evidence is not pooled across experiments, as in a
    sequence of independent A/B tests.
    """

    def run_abtest(self):
        c = self.c
        self.init()
        champ = self.favourite()
        self._champ = champ; self._champ_y = float(self.S[champ] / self.Cn[champ])
        while self.tests < c.budget:
            self.round += 1
            self._drift()
            cand = self.propose(champ)
            if len(cand) == 0:
                cand = self.propose(champ, 30)
                if len(cand) == 0:
                    break
            x = int(cand[np.argmax(self.est[cand])]) if c.prescreen else int(self.rng.choice(cand))
            self.build(x)
            y = self.L.measure(np.array([x, champ]), c.n_sess, self.rng) + self._bias(np.array([x, champ]), np.array([0, 1]))
            for v, val in zip((x, champ), y):
                self.S[v] += val; self.Cn[v] += 1
            before = self.tests
            self.tests += 2
            if c.ab_pool:
                # champion's evidence pooled over all its tests
                yc, nc = self.S[champ] / self.Cn[champ], self.Cn[champ]
                z = (y[0] - yc) / (self.sigma * np.sqrt(1 + 1 / nc))
                if z > c.alpha_z:
                    champ, self._champ_y = x, float(y[0])
                else:
                    self._champ_y = float(yc)
            elif (y[0] - y[1]) / (self.sigma * np.sqrt(2)) > c.alpha_z:
                champ, self._champ_y = x, float(y[0])
            else:
                self._champ_y = float(y[1])
            self._champ = champ
            while self.cp and self.tests >= self.cp[0] and before < self.cp[0]:
                self.record(self.cp.pop(0))

    def shipped(self):
        return getattr(self, "_champ", super().shipped())

    def record(self, t):
        L, U = self.L, self.U_now
        x = self.shipped()
        ever = np.flatnonzero(self.is_built)
        self.log.append(dict(
            tests=t, shipped=float(U[x]), found=float(U[ever].max()),
            belief=float(getattr(self, "_champ_y", np.nan)), ustar=float(U.max()),
            local_opt=bool(L.local_gap(x, 2, U) <= 0),
            found_local_opt=bool(L.local_gap(int(ever[np.argmax(U[ever])]), 2, U) <= 0),
            gap=float(L.local_gap(x, 2, U)), n_built=len(ever), ship_x=int(x)))


class ParetoEngine(Engine):
    """Multi-stakeholder loop with an archive of non-dominated configurations.

    Each test returns one noisy observation per stakeholder criterion
    (desirability, feasibility, viability).  Beliefs are kept per criterion;
    the archive is the set of built configurations that no other built
    configuration dominates according to current beliefs.
    """

    def __init__(self, L, cfg, seed):
        super().__init__(L, cfg, seed)
        self.S3 = np.zeros((L.N, 3))
        rng = np.random.default_rng(777)
        xs = rng.choice(L.N, 200, replace=False)
        y = np.stack([L.measure(xs, cfg.n_sess, rng, components=True) for _ in range(60)])
        self.sig3 = np.sqrt(y.var(0, ddof=1).mean(0))
        Cz = L.C
        self.zC = (Cz - Cz.mean(0)) / Cz.std(0)

    def post3(self, idx):
        prec0 = 1.0 / self.v0
        s2 = self.sig3 ** 2
        prec = prec0 + self.Cn[idx][:, None] / s2[None, :]
        mu = (self.m0 * prec0 + self.S3[idx] / s2[None, :]) / prec
        return mu, 1.0 / prec

    def archive(self):
        b = np.array(self.built)
        mu, _ = self.post3(b)
        dom = np.all(mu[:, None, :] >= mu[None, :, :], 2) & np.any(mu[:, None, :] > mu[None, :, :], 2)
        nd = ~dom.any(0)
        return b[nd]

    def test3(self, xs):
        xs = np.asarray(xs, dtype=np.int64)[: self.c.budget - self.tests]
        if len(xs) == 0:
            return
        y = self.L.measure(xs, self.c.n_sess, self.rng, components=True)
        for x, v in zip(xs, y):
            self.S3[x] += v; self.Cn[x] += 1
        self.tests += len(xs)

    def run(self):
        c, L = self.c, self.L
        xs = self.rng.choice(L.N, c.n_init, replace=False)
        for x in xs:
            self.build(x)
        self.test3(xs)
        while self.tests < c.budget:
            arch = self.archive()
            parent = int(self.rng.choice(arch))
            self.propose(parent)
            pool = np.flatnonzero(self.in_pool)
            if len(pool):
                w = self.rng.dirichlet(np.ones(3))
                est = (self.rho * self.zC[pool] + np.sqrt(1 - self.rho ** 2) * self.rng.normal(size=(len(pool), 3))) @ w
                x = int(pool[np.argmax(est)])
                self.build(x)
                new = [x]
            else:
                new = []
            arch = [int(a) for a in self.archive() if a not in new]
            re = list(self.rng.choice(arch, min(3, len(arch)), replace=False)) if arch else []
            self.rot = (self.rot + 1) % len(self.built)
            self.test3(new + re + [self.built[self.rot]])
        return self.archive()


def run(L: Landscape, cfg: Config, seed: int):
    E = ABEngine(L, cfg, seed) if cfg.policy == "abtest" else Engine(L, cfg, seed)
    return E.run(), E
