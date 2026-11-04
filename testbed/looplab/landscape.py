"""Analytic (queueing) model of the testbed and the utility landscape.

For every configuration (a bitmask over the features) the model computes the
load on each tier of the service topology, the waiting times from M/M/c
(Erlang-C) formulas, the page-load time experienced by each user segment,
the expected conversion, the 95th percentile of page-load time, the error
rate, the running cost and the profit.  These are mapped to the three
criteria of the design-thinking utility (desirability, feasibility,
viability), and the utility of every configuration is known exactly.

A *test* of a configuration is an online experiment on ``n`` sessions.  The
statistical sampler in :meth:`Landscape.measure` draws what such an
experiment would report (conversions, sample p95, metered cost); it is
validated against the discrete-event simulator in :mod:`looplab.des`.
"""
from __future__ import annotations

import math
import numpy as np
from .params import Params

GH_X, GH_W = np.polynomial.hermite_e.hermegauss(24)
GH_W = GH_W / GH_W.sum()


def all_configs(n: int) -> np.ndarray:
    """Bit matrix (2**n, n) of all configurations."""
    idx = np.arange(2 ** n, dtype=np.int64)
    return ((idx[:, None] >> np.arange(n)) & 1).astype(np.float64)


def erlang_c_wait(lam, s, c):
    """Mean waiting time in an M/M/c queue (vectorised, c may vary).

    Utilisation is capped at 0.97; the caller adds an overload penalty.
    """
    lam = np.asarray(lam, float)
    s = np.asarray(s, float) * np.ones_like(lam)
    c = np.asarray(c) * np.ones_like(lam)
    rho = lam * s / c
    rho_c = np.minimum(rho, 0.97)
    W = np.zeros_like(lam)
    for cv in np.unique(c):
        m = c == cv
        cv = int(cv)
        a = rho_c[m] * cv
        k = np.arange(cv)[:, None]
        terms = a[None, :] ** k / np.array([math.factorial(int(i)) for i in range(cv)])[:, None]
        top = a ** cv / math.factorial(cv) / (1 - rho_c[m])
        pc = top / (terms.sum(0) + top)
        W[m] = pc * s[m] / (cv * (1 - rho_c[m]))
    over = np.maximum(rho - 0.97, 0.0)
    W = W + 6.0 * over + 25.0 * over * s  # steep overload penalty
    return W, rho


def _lognorm_sigma(cv):
    return np.sqrt(np.log1p(np.asarray(cv) ** 2))


def evaluate(p: Params, X: np.ndarray | None = None) -> dict:
    """Evaluate configurations X (bit matrix).  Default: all 2**n."""
    n = p.n
    if X is None:
        X = all_configs(n)
    F = p.features
    col = lambda attr: np.array([getattr(f, attr) for f in F], float)
    key = {f.key: i for i, f in enumerate(F)}

    pages = p.pages0 + X @ col("pages_delta")
    pages = np.maximum(pages, 2.0)
    lam_p = p.lam_s * pages

    cdn = X[:, key["CDN"]] if "CDN" in key else np.zeros(len(X))
    static = p.static_reqs * (1 - 0.85 * cdn)
    s_app = p.s_app0 + X @ col("s_app") + static * p.s_static
    c_app = p.c_app + X @ col("servers_add")

    dbf = np.prod(np.where(X > 0, col("db_factor")[None, :], 1.0), axis=1)
    calls = p.db_calls * dbf
    W_db, rho_db = erlang_c_wait(lam_p * calls, p.s_db, p.c_db)

    ml_s = X @ col("ml_s")
    has_ml = ml_s > 0
    W_ml = np.zeros(len(X)); rho_ml = np.zeros(len(X))
    if has_ml.any():
        w, r = erlang_c_wait(lam_p[has_ml], ml_s[has_ml], p.c_ml)
        W_ml[has_ml] = w; rho_ml[has_ml] = r

    # an application worker is held for the whole synchronous request,
    # including its database and ML calls (thread-per-request server)
    hold = s_app + calls * (p.s_db + W_db) + ml_s + W_ml
    W_app, rho_app = erlang_c_wait(lam_p, hold, c_app)
    server = hold + W_app + X @ col("ext_delay")
    bytes_ = p.page_bytes * np.prod(np.where(X > 0, col("byte_factor")[None, :], 1.0), axis=1)
    out = {}
    T = {}
    for seg, rtt, bw in (("m", p.rtt_m, p.bw_m), ("d", p.rtt_d, p.bw_d)):
        rtt_eff = rtt * (1 - 0.65 * cdn) + 0.65 * cdn * p.rtt_edge
        bw_eff = bw * (1 + 0.3 * cdn)
        T[seg] = p.k_rtt * rtt_eff + bytes_ * 8 / bw_eff + server
    rho_max = np.maximum.reduce([rho_app, rho_db, rho_ml])
    err = np.clip((rho_max - 0.93) * 4.0, 0.0, 0.6)

    # log-lift of conversion
    L = {"m": X @ col("lift_m"), "d": X @ col("lift_d")}
    inter = np.zeros(len(X))
    for (a, b), v in p.interactions.items():
        if a in key and b in key:
            inter += v * X[:, key[a]] * X[:, key[b]]
    if p.rand_inter is not None:
        inter += np.einsum("ij,ki,kj->k", p.rand_inter, X, X)
        for (i, j, k), v in p.rand_triples:
            inter += v * X[:, i] * X[:, j] * X[:, k]
    if p.nk is not None:
        K, tau, nbrs, tables = p.nk
        Xi = X.astype(np.int64)
        f = np.zeros(len(X))
        for i in range(n):
            code = Xi[:, i].copy()
            for b, j in enumerate(nbrs[i]):
                code |= Xi[:, j] << (b + 1)
            f += tables[i][code]
        inter += tau * (f / n - 0.5)

    conv = {}
    cv_s = p.cv_page / np.sqrt(np.maximum(pages, 1.0)) * 1.6
    for seg in ("m", "d"):
        base = p.base_conv_m if seg == "m" else p.base_conv_d
        sig = _lognorm_sigma(cv_s)
        mu = np.log(T[seg]) - sig ** 2 / 2
        Ts = np.exp(mu[:, None] + sig[:, None] * GH_X[None, :])
        pen = np.exp(-p.kappa * np.maximum(Ts - p.t0, 0.0)) @ GH_W
        conv[seg] = np.clip(base * np.exp(L[seg] + inter) * pen * (1 - err), 0, 1)
    ms = p.mobile_share
    conv_all = ms * conv["m"] + (1 - ms) * conv["d"]

    # p95 of page-load time over the mixture of segments
    sig_p = _lognorm_sigma(p.cv_page)
    mu_m = np.log(T["m"]) - sig_p ** 2 / 2
    mu_d = np.log(T["d"]) - sig_p ** 2 / 2
    from scipy.special import ndtr
    lo = np.full(len(X), 0.01); hi = np.full(len(X), 200.0)
    for _ in range(50):
        mid = np.sqrt(lo * hi)
        cdf = ms * ndtr((np.log(mid) - mu_m) / sig_p) + (1 - ms) * ndtr((np.log(mid) - mu_d) / sig_p)
        lo = np.where(cdf < 0.95, mid, lo); hi = np.where(cdf >= 0.95, mid, hi)
    p95 = np.minimum(np.sqrt(lo * hi), p.timeout)

    fraud = p.fraud0 * np.prod(np.where(X > 0, col("fraud_factor")[None, :], 1.0), axis=1)
    sess_h = p.lam_s * 3600
    revenue = sess_h * conv_all * p.aov * p.margin * (1 - fraud)
    gb_h = lam_p * 3600 * bytes_ / 1e9
    cost = (c_app * p.app_cost_h + X @ col("cost_h") + sess_h * (X @ col("cost_sess"))
            + gb_h * p.bw_cost_gb * (1 - (1 - p.cdn_bw_share) * cdn))
    profit = revenue - cost
    cx = X @ col("complexity")

    out.update(dict(X=X, pages=pages, lam_p=lam_p, s_app=s_app, c_app=c_app, hold=hold,
                    calls=calls, ml_s=ml_s, rho_app=rho_app, rho_db=rho_db,
                    rho_ml=rho_ml, rho_max=rho_max, err=err, T_m=T["m"], T_d=T["d"],
                    server=server, bytes=bytes_, conv_m=conv["m"], conv_d=conv["d"],
                    conv=conv_all, p95=p95, fraud=fraud, revenue=revenue, cost=cost,
                    profit=profit, complexity=cx, cx_total=col("complexity").sum()))
    return out


class Landscape:
    """Exact utility landscape of one testbed instance (all 2**n configs)."""

    def __init__(self, p: Params, name: str = ""):
        self.p = p
        self.name = name
        self.n = p.n
        self.N = 2 ** p.n
        ev = evaluate(p)
        self.ev = ev
        ok = ev["rho_max"] < 0.97          # stable configurations set the scale
        self.c_lo, self.c_hi = ev["conv"][ok].min(), ev["conv"].max()
        self.v_lo, self.v_hi = ev["profit"][ok].min(), ev["profit"].max()
        self.Ud = np.clip(self._ud(ev["conv"]), 0, 1)
        self.Uf = self._uf(ev["p95"], ev["err"], ev["complexity"])
        self.Uv = np.clip(self._uv(self._profit(ev["conv"], np.arange(self.N))), 0, 1)
        self.C = np.stack([self.Ud, self.Uf, self.Uv], 1)
        self.set_weights(p.w)
        # neighbourhood masks within Hamming radius 1 and 2
        self.masks1 = np.array([1 << i for i in range(self.n)], dtype=np.int64)
        m2 = [(1 << i) | (1 << j) for i in range(self.n) for j in range(i + 1, self.n)]
        self.masks2 = np.concatenate([self.masks1, np.array(m2, dtype=np.int64)])

    # --- criteria ---------------------------------------------------------
    def _ud(self, conv):
        return (conv - self.c_lo) / (self.c_hi - self.c_lo)

    def _uf(self, p95, err, cx):
        p = self.p
        slo = 1.0 / (1.0 + np.exp((p95 - p.slo_p95) / p.slo_scale))
        return p.feas_mix * slo * (1 - np.minimum(1.0, 1.5 * err)) + (1 - p.feas_mix) * (1 - cx / self.ev["cx_total"])

    def _profit(self, conv, idx, cost=None):
        ev, p = self.ev, self.p
        rev = p.lam_s * 3600 * conv * p.aov * p.margin * (1 - ev["fraud"][idx])
        return rev - (ev["cost"][idx] if cost is None else cost)

    def _uv(self, profit):
        return (profit - self.v_lo) / (self.v_hi - self.v_lo)

    def set_weights(self, w):
        self.w = np.asarray(w, float)
        self.U = self.C @ self.w
        self.Ustar = self.U.max()
        self.opt = int(self.U.argmax())
        self._lo = {}

    # --- structure --------------------------------------------------------
    def neighbours(self, x: int, radius: int = 2) -> np.ndarray:
        m = self.masks1 if radius == 1 else self.masks2
        return x ^ m

    def local_optima(self, radius: int = 2, U=None) -> np.ndarray:
        U = self.U if U is None else U
        key = (radius, id(U))
        if U is self.U and radius in self._lo:
            return self._lo[radius]
        m = self.masks1 if radius == 1 else self.masks2
        idx = np.arange(self.N)
        best_nb = np.max(U[idx[:, None] ^ m[None, :]], axis=1)
        lo = U > best_nb
        if U is self.U:
            self._lo[radius] = lo
        return lo

    def local_gap(self, x: int, radius: int = 2, U=None) -> float:
        """How much the best variant of x beats x (<=0 if x is locally optimal)."""
        U = self.U if U is None else U
        return float(U[self.neighbours(x, radius)].max() - U[x])

    # --- tests ------------------------------------------------------------
    def measure(self, x, n_sess: int, rng: np.random.Generator, components=False):
        """Outcome of an online experiment with n_sess sessions on config x.

        Returns the measured utility (or the three measured criteria).
        x may be an int or an int array (vectorised over tests).
        """
        x = np.atleast_1d(np.asarray(x, dtype=np.int64))
        ev, p = self.ev, self.p
        k = len(x)
        nm = rng.binomial(n_sess, p.mobile_share, size=k)
        nd = n_sess - nm
        cm = rng.binomial(nm, ev["conv_m"][x]); cd = rng.binomial(nd, ev["conv_d"][x])
        conv_hat = (cm + cd) / n_sess
        # sample p95 of N page loads: asymptotic normal of a sample quantile
        Np = n_sess * ev["pages"][x]
        sig_p = float(_lognorm_sigma(p.cv_page))
        q = ev["p95"][x]
        z95 = 1.6449
        dens = np.exp(-0.5 * z95 ** 2) / (np.sqrt(2 * np.pi) * sig_p * q)
        sd_q = np.sqrt(0.95 * 0.05 / Np) / dens
        p95_hat = np.maximum(q + rng.normal(0, 1, k) * sd_q * 1.15, 0.05)
        err_hat = rng.binomial(np.maximum(Np.astype(np.int64), 1), ev["err"][x]) / np.maximum(Np, 1)
        cost_hat = ev["cost"][x] * (1 + rng.normal(0, 0.01, k))
        ud = self._ud(conv_hat)
        uf = self._uf(p95_hat, err_hat, ev["complexity"][x])
        uv = self._uv(self._profit(conv_hat, x, cost_hat))
        if components:
            return np.stack([ud, uf, uv], 1)
        return np.stack([ud, uf, uv], 1) @ self.w

    def sigma(self, n_sess: int, rng=None, sample=200, reps=200) -> float:
        """Empirical s.d. of a test of n_sess sessions (averaged over configs)."""
        rng = np.random.default_rng(12345) if rng is None else rng
        xs = rng.choice(self.N, sample, replace=False)
        y = np.stack([self.measure(xs, n_sess, rng) for _ in range(reps)])
        return float(np.sqrt(np.mean(y.var(0, ddof=1))))

    def summary(self) -> dict:
        lo1 = self.local_optima(1); lo2 = self.local_optima(2)
        return dict(name=self.name, n=self.n, Ustar=float(self.Ustar),
                    Umean=float(self.U.mean()), Usd=float(self.U.std()),
                    lo1=int(lo1.sum()), lo2=int(lo2.sum()),
                    opt=int(self.opt), opt_features=[self.p.keys[i] for i in range(self.n) if self.opt >> i & 1])
