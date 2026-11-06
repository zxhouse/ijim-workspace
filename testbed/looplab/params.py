"""Parameters of the LoopLab digital-service testbed.

A configuration of the service is a subset of deployable capabilities
(feature flags).  Each capability changes the load placed on the service
topology, the experience of users in two segments, the running cost and the
operational complexity of the service.  The defaults describe the *reference
instance*; ``random_params`` draws further instances for the landscape
families used in the experiments.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import numpy as np


@dataclass
class Feature:
    key: str
    name: str
    s_app: float = 0.0          # extra app CPU per page (s)
    db_factor: float = 1.0      # multiplier of DB calls per page
    ml_s: float = 0.0           # ML-inference service time per page (s)
    cdn: bool = False           # offloads static content to the edge
    byte_factor: float = 1.0    # multiplier of page weight
    pages_delta: float = 0.0    # change of pages per session
    servers_add: int = 0        # extra application servers
    lift_m: float = 0.0         # log-lift of conversion, mobile
    lift_d: float = 0.0         # log-lift of conversion, desktop
    cost_h: float = 0.0         # fixed running cost per hour
    cost_sess: float = 0.0      # variable cost per session
    complexity: float = 1.0     # operational complexity points
    fraud_factor: float = 1.0   # multiplier of the fraud-loss rate
    ext_delay: float = 0.0      # perceived external-API delay per page (s)


def default_features() -> list[Feature]:
    return [
        Feature("CDN", "Edge content delivery network", cdn=True,
                cost_h=420.0, complexity=1.0),
        Feature("COMP", "Response compression", s_app=0.003,
                byte_factor=0.72, complexity=0.3),
        Feature("CACHE", "Application data cache", db_factor=0.35,
                s_app=0.001, cost_h=180.0, complexity=1.2),
        Feature("REPL", "Three extra application replicas", servers_add=3,
                cost_h=900.0, complexity=0.6),
        Feature("RECO", "ML recommendation service", ml_s=0.025,
                lift_m=0.030, lift_d=0.040, cost_h=1500.0, complexity=2.0,
                pages_delta=0.4),
        Feature("CHAT", "Generative-AI shopping assistant", lift_m=0.020,
                lift_d=0.060, cost_sess=0.045, complexity=1.8,
                ext_delay=0.045, s_app=0.002),
        Feature("ONECLICK", "One-click checkout", lift_m=0.150,
                lift_d=0.120, pages_delta=-1.0, complexity=0.8,
                fraud_factor=1.25),
        Feature("MFA", "Step-up authentication", s_app=0.002,
                lift_m=-0.080, lift_d=-0.060, cost_sess=0.010,
                complexity=0.9, fraud_factor=0.25),
        Feature("MEDIA", "Rich product media", byte_factor=2.0,
                lift_m=0.030, lift_d=0.085, cost_h=250.0, complexity=0.4),
        Feature("AUTOC", "Search autocomplete", s_app=0.0035,
                lift_m=0.020, lift_d=0.050, pages_delta=-0.3,
                complexity=0.6),
        Feature("PRIV", "Privacy dashboard and consent manager",
                lift_m=0.020, lift_d=0.020, cost_h=120.0, complexity=0.7),
        Feature("TELEM", "Fine-grained behavioural telemetry",
                s_app=0.004, lift_m=-0.015, lift_d=-0.015, cost_h=600.0,
                complexity=1.0),
    ]


# Pairwise log-lift interactions between named features.  They are what
# makes the landscape non-additive (the "integration" part of feasibility
# and desirability):
DEFAULT_INTERACTIONS = {
    ("RECO", "TELEM"): 0.095,     # recommendations need behavioural data
    ("ONECLICK", "MFA"): -0.110,  # friction defeats one-click checkout
    ("MFA", "PRIV"): 0.045,       # trust offsets authentication friction
    ("TELEM", "PRIV"): 0.020,     # consent management removes friction
    ("CHAT", "RECO"): 0.020,      # the assistant can use recommendations
    ("MEDIA", "CHAT"): -0.015,    # attention competition
}


@dataclass
class Params:
    features: list[Feature] = field(default_factory=default_features)
    interactions: dict = field(default_factory=lambda: dict(DEFAULT_INTERACTIONS))
    # random interaction matrix (rugged family); shape (n, n), upper part used
    rand_inter: np.ndarray | None = None
    rand_triples: list | None = None
    # NK-type preference term of the rugged family: (K, tau, nbrs, tables)
    nk: tuple | None = None

    lam_s: float = 30.0          # sessions per second
    mobile_share: float = 0.62
    pages0: float = 6.0          # pages per session
    base_conv_m: float = 0.026
    base_conv_d: float = 0.041
    aov: float = 62.0            # average order value
    margin: float = 0.22
    fraud0: float = 0.030        # fraud loss rate of revenue

    # topology
    c_app: int = 9
    s_app0: float = 0.016        # base app service time per page (s)
    static_reqs: float = 6.0     # static requests per page served by origin
    s_static: float = 0.0010
    c_db: int = 3
    db_calls: float = 3.0
    s_db: float = 0.0040
    c_ml: int = 6
    rtt_m: float = 0.065
    rtt_d: float = 0.028
    rtt_edge: float = 0.012
    bw_m: float = 12e6           # bits/s
    bw_d: float = 60e6
    page_bytes: float = 1.1e6
    k_rtt: float = 4.0
    cv_page: float = 0.55        # coefficient of variation of a page load
    timeout: float = 8.0

    # behaviour
    t0: float = 1.0              # tolerated mean page time (s)
    kappa: float = 0.32          # conversion decay per second above t0
    slo_p95: float = 2.6
    slo_scale: float = 0.35

    # cost
    app_cost_h: float = 160.0
    bw_cost_gb: float = 0.90   # fully loaded egress cost per GB
    cdn_bw_share: float = 0.55   # share of bandwidth cost left with a CDN

    # utility weights (desirability, feasibility, viability)
    w: tuple = (0.45, 0.25, 0.30)
    feas_mix: float = 0.65       # weight of the SLO inside feasibility

    @property
    def n(self) -> int:
        return len(self.features)

    @property
    def keys(self) -> list[str]:
        return [f.key for f in self.features]


def random_params(rng: np.random.Generator, rugged: float = 0.0,
                  n_extra: int = 0, drop: tuple = (), K: int = 0,
                  tau: float = 0.0, tails: float = 0.0) -> Params:
    """Draw one instance of the testbed.

    rugged : standard deviation of random pairwise log-lift interactions
             (0 gives the smooth "service" family); triples are added too.
    K, tau : NK-type user-preference term (each feature's contribution
             depends on K others) scaled by tau; used by the rugged family.
    tails  : scale of heavy-tailed (Student-t, 2 d.f.) main effects and
             pairwise interactions added to the conversion lifts, so that
             most capabilities do little and a few do much (fat-tailed family).
    n_extra: number of generic additional features.
    drop   : keys of default features to remove.
    """
    p = Params()
    feats = []
    for f in default_features():
        if f.key in drop:
            continue
        j = lambda x, s=0.35: x * float(np.exp(rng.normal(0.0, s)))
        feats.append(replace(
            f,
            s_app=j(f.s_app), ml_s=j(f.ml_s), cost_h=j(f.cost_h),
            cost_sess=j(f.cost_sess), complexity=j(f.complexity, 0.2),
            lift_m=f.lift_m * float(np.exp(rng.normal(0, 0.45))) + rng.normal(0, 0.01),
            lift_d=f.lift_d * float(np.exp(rng.normal(0, 0.45))) + rng.normal(0, 0.01),
            byte_factor=float(np.clip(f.byte_factor * np.exp(rng.normal(0, 0.15)), 0.3, 3.0)),
        ))
    for e in range(n_extra):
        lift = rng.normal(0.0, 0.03)
        feats.append(Feature(f"X{e+1}", f"Generic capability {e+1}",
                             s_app=abs(rng.normal(0.0015, 0.001)),
                             lift_m=lift, lift_d=lift + rng.normal(0, 0.01),
                             cost_h=abs(rng.normal(200, 120)),
                             complexity=abs(rng.normal(0.7, 0.3))))
    if tails > 0:
        # fat-tailed family: the designed lifts are shrunk so that most
        # capabilities do little, and heavy-tailed effects are added
        for f in feats:
            t = float(rng.standard_t(2)) * tails
            f.lift_m = 0.3 * f.lift_m + t; f.lift_d = 0.3 * f.lift_d + t + float(rng.standard_t(2)) * tails * 0.3
    p.features = feats
    p.interactions = {k: v * float(np.exp(rng.normal(0, 0.3)))
                      for k, v in DEFAULT_INTERACTIONS.items()}
    p.lam_s = float(rng.uniform(22, 36))
    p.mobile_share = float(rng.uniform(0.45, 0.78))
    p.base_conv_m = float(rng.uniform(0.020, 0.032))
    p.base_conv_d = float(rng.uniform(0.033, 0.050))
    p.margin = float(rng.uniform(0.16, 0.28))
    p.c_app = int(rng.integers(8, 11))
    p.kappa = float(rng.uniform(0.22, 0.42))
    p.slo_p95 = float(rng.uniform(2.3, 3.0))
    n = len(feats)
    if tails > 0:
        R = rng.standard_t(2, size=(n, n)) * tails * 0.5
        p.rand_inter = np.triu(R, 1)
        p.rand_triples = []
    if rugged > 0:
        R = rng.normal(0.0, rugged, size=(n, n))
        p.rand_inter = np.triu(R, 1)
        trip = []
        for _ in range(n):
            idx = tuple(sorted(rng.choice(n, 3, replace=False).tolist()))
            trip.append((idx, float(rng.normal(0.0, rugged))))
        p.rand_triples = trip
    if K > 0 and tau > 0:
        nbrs = np.array([rng.choice([j for j in range(n) if j != i], K, replace=False)
                         for i in range(n)])
        tables = rng.uniform(0, 1, size=(n, 2 ** (K + 1)))
        p.nk = (K, tau, nbrs, tables)
    return p
