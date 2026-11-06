"""Analysis of all experiments: figures (paper/figures) and numbers (results/numbers.json).

Usage:  python3 analyze.py [e1 e2 ...]   (default: every experiment with results)
"""
from __future__ import annotations

import collections
import json
import os
import sys

import numpy as np
from scipy import stats

from common import RES, FIG, load, t_ci, holm, summarise, paired, get_landscape  # noqa
from figstyle import setup, plt, W_FULL, W_HALF, COL, CLS_NAME, POL_COL, POL_NAME

setup()
NUM_PATH = os.path.join(RES, "numbers.json")
NUM = json.load(open(NUM_PATH)) if os.path.exists(NUM_PATH) else {}
CLASSES = ("ref", "svc", "rug")


def check_axes(fig, name):
    """Every axis of every panel must carry a label and a visible numeric or
    categorical scale; the figure is not written otherwise."""
    fig.canvas.draw()
    problems = []
    for k, ax in enumerate(fig.axes):
        if not ax.get_visible() or not ax.axison:
            continue
        for which, lab, ticks in (("x", ax.get_xlabel(), ax.get_xticklabels()),
                                  ("y", ax.get_ylabel(), ax.get_yticklabels())):
            if not lab.strip():
                problems.append(f"panel {k}: {which}-axis has no label")
            if not any(t.get_visible() and t.get_text().strip() for t in ticks):
                problems.append(f"panel {k}: {which}-axis has no scale (tick labels)")
    if problems:
        raise ValueError(f"{name}: " + "; ".join(problems))


def savefig(fig, name):
    check_axes(fig, name)
    fig.savefig(os.path.join(FIG, name))
    plt.close(fig)


def r2(x, k=2):
    return float(np.round(x, k))


# --------------------------------------------------------------------- E1 --
def e1():
    d = load("e1_validation.json")
    A = d["agree"]
    out = {}
    L = get_landscape("ref", 0)
    sig6000 = L.sigma(6000)
    for st in ("stable", "near", "overload", "all"):
        a = [r for r in A if st == "all" or r["stratum"] == st]
        U = np.array([r["U"] for r in a]); Ua = np.array([r["U_an"] for r in a])
        c = np.array([r["conv"] for r in a]); ca = np.array([r["conv_an"] for r in a])
        p = np.array([r["p95"] for r in a]); pa = np.array([r["p95_an"] for r in a])
        resid_var = np.var(U - Ua, ddof=1)
        out[st] = dict(n=len(a), r=r2(np.corrcoef(U, Ua)[0, 1], 3), spearman=r2(stats.spearmanr(U, Ua)[0], 3),
                       bias=r2((U - Ua).mean(), 3), mae=r2(np.abs(U - Ua).mean(), 3),
                       model_sd=r2(np.sqrt(max(resid_var - sig6000 ** 2, 0)), 3),
                       conv_relbias=r2(100 * ((c - ca) / ca).mean(), 1),
                       p95_relbias=r2(100 * ((p - pa) / pa).mean(), 1),
                       p95_r=r2(np.corrcoef(p, pa)[0, 1], 3),
                       conv_r=r2(np.corrcoef(c, ca)[0, 1], 3))
    out["sigma6000"] = r2(sig6000, 3)
    cal = d["calib"]
    ratio = np.array([r["des_sd"] / r["samp_sd"] for r in cal])
    out["sd_ratio_mean"] = r2(ratio.mean(), 2)
    out["sd_ratio_range"] = [r2(ratio.min(), 2), r2(ratio.max(), 2)]
    # F-test pooled over configurations: log variance ratio
    lv = np.log(np.array([r["des_sd"] ** 2 / r["samp_sd"] ** 2 for r in cal]))
    out["log_var_ratio"] = dict(mean=r2(lv.mean(), 3), p=r2(stats.ttest_1samp(lv, 0).pvalue, 3))
    for n in (500, 1000, 2000, 4000):
        out[f"sd_samp_{n}"] = r2(np.mean([r["samp_sd"] for r in cal if r["n"] == n]), 3)
        out[f"sd_des_{n}"] = r2(np.mean([r["des_sd"] for r in cal if r["n"] == n]), 3)
    S = d["struct"]
    struct = {}
    for c in CLASSES:
        s = [x for x in S if x["cls"] == c]
        f = lambda k: [r2(np.median([x[k] for x in s]), 3), r2(min(x[k] for x in s), 3), r2(max(x[k] for x in s), 3)]
        struct[c] = {k: f(k) for k in ("Ustar", "Umean", "Usd", "lo1", "lo2", "sigma500", "sigma2000", "sigma8000", "top50_sd")}
    out["struct"] = struct
    NUM["e1"] = out

    fig, ax = plt.subplots(1, 2, figsize=(W_FULL, 2.55))
    mk = {"stable": ("o", "#1E88E5", r"stable ($\rho_{\max}<0.85$)"), "near": ("s", "#FB8C00", r"near capacity ($0.85\leq\rho_{\max}<0.97$)"),
          "overload": ("^", "#E53935", r"over capacity ($\rho_{\max}\geq 0.97$)")}
    for st, (m, c, lab) in mk.items():
        a = [r for r in A if r["stratum"] == st]
        ax[0].scatter([r["U_an"] for r in a], [r["U"] for r in a], s=11, marker=m, color=c, alpha=0.8, lw=0, label=lab)
    ax[0].plot([-0.4, 1.2], [-0.4, 1.2], color="#555", lw=0.8, ls="--")
    ax[0].set_xlim(-0.05, 1.0); ax[0].set_ylim(-0.45, 1.15)
    ax[0].set_xlabel("utility from the analytic model (steady state)")
    ax[0].set_ylabel("utility measured in the emulator\n(one experiment, 6,000 sessions)")
    ax[0].set_title("(a) Emulator vs analytic model")
    ax[0].legend(loc="lower right", frameon=False, handletextpad=0.2)
    ns = np.array([500, 1000, 2000, 4000])
    xs = sorted(set(r["x"] for r in cal))
    des = np.array([[next(r["des_sd"] for r in cal if r["x"] == x and r["n"] == n) for n in ns] for x in xs])
    smp = np.array([[next(r["samp_sd"] for r in cal if r["x"] == x and r["n"] == n) for n in ns] for x in xs])
    for k in range(len(xs)):
        ax[1].plot(ns * (1 + 0.03 * (k - 2.5)), des[k], "o", ms=3, color="#E53935", alpha=0.7, label="emulator (20 replications)" if k == 0 else None)
    ax[1].plot(ns, smp.mean(0), "-", color="#1E88E5", lw=1.5, label="statistical test sampler")
    ax[1].plot(ns, smp.mean(0)[2] * np.sqrt(2000 / ns), ":", color="#333", lw=1, label=r"$\propto n^{-1/2}$")
    ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_xticks(ns); ax[1].set_xticklabels([str(n) for n in ns]); ax[1].minorticks_off()
    ax[1].set_yticks([0.1, 0.15, 0.2, 0.3]); ax[1].set_yticklabels(["0.10", "0.15", "0.20", "0.30"])
    ax[1].set_xlabel("sessions per test $n$"); ax[1].set_ylabel(r"s.d. of a test result $\sigma$")
    ax[1].set_title("(b) Noise of a test")
    ax[1].legend(frameon=False, loc="upper right")
    fig.tight_layout(w_pad=2.0)
    savefig(fig, "fig_e1_validation.pdf")


# --------------------------------------------------------------------- E2 --
def e2():
    rows = load("e2_dynamics.json")
    out = {}
    short = [r for r in rows if r["run"] == "short"]
    fig, ax = plt.subplots(1, 2, figsize=(W_FULL, 2.6))
    for pol, ls in (("loop", "-"), ("ledger", "--")):
        a = [r for r in short if r["cls"] == "ref" and r["pol"] == pol]
        T = sorted(set(r["tests"] for r in a))
        for key, col, lab in (("shipped_pct", "#1E88E5", "shipped"), ("found_pct", "#43A047", "best found"), ("belief_pct", "#E53935", "believed")):
            m = np.array([np.mean([r[key] for r in a if r["tests"] == t]) for t in T])
            h = np.array([t_ci([r[key] for r in a if r["tests"] == t])[1] for t in T])
            if pol == "loop":
                ax[0].plot(T, m, ls, color=col, label=lab)
                ax[0].fill_between(T, m - h, m + h, color=col, alpha=0.15, lw=0)
            elif key == "shipped_pct":
                ax[0].plot(T, m, ls, color=col, label="shipped, ledger")
    ax[0].axhline(100, color="#555", lw=0.7)
    ax[0].set_xlabel("tests"); ax[0].set_ylabel(r"utility, % of $U^*$")
    ax[0].set_title("(a) Reference instance, 400 tests")
    ax[0].set_ylim(70, 112); ax[0].legend(frameon=False, ncol=2, loc="lower right")
    for c in CLASSES:
        for pol in ("loop", "ledger"):
            a = [r for r in short if r["cls"] == c and r["pol"] == pol and r["tests"] == 400]
            if not a:
                continue
            o = {}
            for key in ("shipped_pct", "found_pct", "belief_pct"):
                o[key] = [r2(v, 2) for v in summarise(a, ("cls",), key)[(c,)][:2]]
            gap = summarise([dict(r, g=r["found_pct"] - r["shipped_pct"]) for r in a], ("cls",), "g")[(c,)]
            over = summarise([dict(r, g=r["belief_pct"] - 100 * r["shipped"] / r["ustar"]) for r in a], ("cls",), "g")[(c,)]
            notfound = summarise([dict(r, g=100 - r["found_pct"]) for r in a], ("cls",), "g")[(c,)]
            o["choose_loss"] = [r2(gap[0], 2), r2(gap[1], 2)]
            o["find_loss"] = [r2(notfound[0], 2), r2(notfound[1], 2)]
            o["overestimate"] = [r2(over[0], 2), r2(over[1], 2)]
            o["share_local"] = r2(np.mean([r["local_opt"] for r in a]), 3)
            out[f"{c}_{pol}_400"] = o
        for t in (25, 50, 100, 200):
            a = [r for r in short if r["cls"] == c and r["pol"] == "loop" and r["tests"] == t]
            out[f"{c}_loop_{t}"] = dict(shipped=r2(np.mean([r["shipped_pct"] for r in a]), 1),
                                       found=r2(np.mean([r["found_pct"] for r in a]), 1),
                                       belief=r2(np.mean([r["belief_pct"] for r in a]), 1))
    # crossing of belief over 100 %
    a = [r for r in short if r["cls"] == "ref" and r["pol"] == "loop"]
    T = sorted(set(r["tests"] for r in a))
    bel = [np.mean([r["belief_pct"] for r in a if r["tests"] == t]) for t in T]
    cross = next((t for t, b in zip(T, bel) if b > 100), None)
    out["ref_belief_cross"] = cross
    longr = [r for r in rows if r["run"] == "long"]
    for c in CLASSES:
        a = [r for r in longr if r["cls"] == c]
        T = sorted(set(r["tests"] for r in a))
        fav = [np.mean([r["local_opt"] for r in a if r["tests"] == t]) for t in T]
        fnd = [np.mean([r["found_local_opt"] for r in a if r["tests"] == t]) for t in T]
        ax[1].plot(T, fav, "-o", ms=2.5, color=COL[c], label=CLS_NAME[c])
        ax[1].plot(T, fnd, "--", color=COL[c], lw=1)
        out[f"{c}_long"] = {str(t): dict(fav_lo=r2(f, 3), found_lo=r2(g, 3),
                                         shipped=r2(np.mean([r["shipped_pct"] for r in a if r["tests"] == t]), 2),
                                         found=r2(np.mean([r["found_pct"] for r in a if r["tests"] == t]), 2))
                           for t, f, g in zip(T, fav, fnd)}
    ax[1].set_xscale("log"); ax[1].set_xticks([100, 400, 800, 1600, 3200]); ax[1].set_xticklabels(["100", "400", "800", "1600", "3200"])
    ax[1].minorticks_off()
    ax[1].set_ylim(0, 1); ax[1].set_xlabel("tests (log scale)"); ax[1].set_ylabel("share of runs at a local optimum")
    ax[1].set_title("(b) Distance to the limit (loop)")
    ax[1].plot([], [], "k-", label="favourite"); ax[1].plot([], [], "k--", lw=1, label="best found")
    ax[1].legend(frameon=False, loc="upper left", ncol=1)
    fig.tight_layout(w_pad=2.0)
    savefig(fig, "fig_e2_dynamics.pdf")
    NUM["e2"] = out


# --------------------------------------------------------------------- E3 --
POLS = ("random", "abtest", "oneshot", "loop", "ledger", "thompson")


def e3():
    rows = [r for r in load("e3_policies.json") if r["tests"] == 400]
    out = {}
    fig, axes = plt.subplots(3, 1, figsize=(W_FULL, 6.4))
    for k, c in enumerate(CLASSES):
        ax = axes[k]
        for j, n in enumerate((2000, 500)):
            a = [r for r in rows if r["cls"] == c and r["n"] == n]
            S = summarise(a, ("pol",))
            for i, pol in enumerate(POLS):
                m, h, _ = S[(pol,)]
                y = i + (0.18 if n == 2000 else -0.18)
                ax.errorbar(m, y, xerr=h, fmt="o" if n == 2000 else "s", ms=3.5, color=POL_COL[pol],
                            mfc=POL_COL[pol] if n == 2000 else "white", lw=1, capsize=0)
                out.setdefault(f"{c}_{n}", {})[pol] = dict(shipped=[r2(m), r2(h)])
            for pol in POLS:
                aa = [r for r in a if r["pol"] == pol]
                over = summarise([dict(r, g=r["belief_pct"] - r["shipped_pct"]) for r in aa], ("cls",), "g")[(c,)]
                gap = summarise([dict(r, g=r["found_pct"] - r["shipped_pct"]) for r in aa], ("cls",), "g")[(c,)]
                out[f"{c}_{n}"][pol].update(overestimate=[r2(over[0]), r2(over[1])], choose_loss=[r2(gap[0]), r2(gap[1])],
                                            found=r2(np.mean([r["found_pct"] for r in aa])),
                                            n_built=r2(np.mean([r["n_built"] for r in aa]), 0))
            # paired tests of the ledger against each alternative, Holm-adjusted
            comps = [p for p in POLS if p != "ledger"]
            res = [paired(a, "pol", "ledger", p) for p in comps]
            adj = holm([x["p"] for x in res])
            for p, x, pa in zip(comps, res, adj):
                out[f"{c}_{n}"]["ledger_vs_" + p] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p_holm=float(f"{pa:.2g}"), dz=r2(x["dz"]), units=x["n"])
        ax.set_yticks(range(len(POLS)))
        ax.set_yticklabels([POL_NAME[p] for p in POLS])
        ax.set_ylabel("policy")
        ax.set_xlim(68, 100)
        ax.set_title(f"({'abc'[k]}) {CLS_NAME[c]}")
        ax.set_xlabel(r"shipped utility, % of $U^*$")
        ax.grid(axis="y", visible=False)
    h1, = axes[0].plot([], [], "o", color="#555", ms=3.5, label="filled: $n=2000$ sessions per test")
    h2, = axes[0].plot([], [], "s", color="#555", mfc="white", ms=3.5, label="open: $n=500$ sessions per test")
    fig.legend(handles=[h1, h2], loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.55, -0.005))
    fig.tight_layout(h_pad=1.2, rect=(0, 0.035, 1, 1))
    savefig(fig, "fig_e3_policies.pdf")
    NUM["e3"] = out


# --------------------------------------------------------------------- E4 --
def e4():
    rows = load("e4_allocation.json")
    out = {}
    K = (0.5, 1, 2, 3, 4, 5)
    fig, axes = plt.subplots(1, 3, figsize=(W_FULL, 2.4), sharey=False)
    ncol = {500: "#E53935", 2000: "#1E88E5", 8000: "#43A047"}
    for k, c in enumerate(CLASSES):
        ax = axes[k]
        for n in (500, 2000, 8000):
            a = [r for r in rows if r["cls"] == c and r["n"] == n]
            S = summarise(a, ("k_new",))
            m = np.array([S[(kk,)][0] for kk in K]); h = np.array([S[(kk,)][1] for kk in K])
            ax.errorbar(K, m, yerr=h, color=ncol[n], marker="o", ms=3, lw=1.1, capsize=0,
                        label=f"$n={n}$ ({800000 // n} tests)")
            best = K[int(np.argmax(m))]
            ax.plot(best, m.max(), "o", ms=7, mfc="none", mec=ncol[n], mew=1.0)
            worst = K[int(np.argmin(m))]
            d5 = paired(a, "k_new", best, 5) if best != 5 else None
            out[f"{c}_{n}"] = dict(means={str(kk): r2(v) for kk, v in zip(K, m)}, best=best, worst=worst,
                                   best_minus_all_new=(dict(diff=r2(d5["mean"]), half=r2(d5["half"])) if d5 else None))
        ax.set_xticks(K); ax.set_xticklabels(["½", "1", "2", "3", "4", "5"])
        ax.set_xlabel("new configurations per 5 tests")
        ax.set_title(f"({'abc'[k]}) {CLS_NAME[c]}")
        ax.set_ylabel(r"shipped utility, % of $U^*$")
    axes[2].legend(frameon=False, loc="lower left")
    fig.tight_layout(w_pad=1.0)
    savefig(fig, "fig_e4_allocation.pdf")
    # best test size given the traffic budget
    for c in CLASSES:
        best = {}
        for n in (500, 2000, 8000):
            best[str(n)] = max(out[f"{c}_{n}"]["means"].values())
        out[f"{c}_best_by_n"] = best
    NUM["e4"] = out


# --------------------------------------------------------------------- E5 --
def anova_eta(rows, factors, value):
    """Partial eta^2 for main effects and two-way interactions in a balanced design
    (cell means over instances first, so families weigh instances equally)."""
    import itertools
    cell = collections.defaultdict(list)
    for r in rows:
        unit = r["seed"] if r["cls"] == "ref" else r["inst"]
        cell[tuple(r[f] for f in factors) + (unit,)].append(r[value])
    data = [(k[:-1], k[-1], np.mean(v)) for k, v in cell.items()]
    y = np.array([d[2] for d in data]); grand = y.mean()
    levels = [sorted(set(d[0][i] for d in data)) for i in range(len(factors))]
    ss = {}
    for i, f in enumerate(factors):
        m = {l: np.mean([d[2] for d in data if d[0][i] == l]) for l in levels[i]}
        ss[f] = sum(len([1 for d in data if d[0][i] == l]) * (m[l] - grand) ** 2 for l in levels[i])
    for i, j in itertools.combinations(range(len(factors)), 2):
        mij = collections.defaultdict(list)
        for d in data:
            mij[(d[0][i], d[0][j])].append(d[2])
        mi = {l: np.mean([d[2] for d in data if d[0][i] == l]) for l in levels[i]}
        mj = {l: np.mean([d[2] for d in data if d[0][j] == l]) for l in levels[j]}
        ss[f"{factors[i]}x{factors[j]}"] = sum(len(v) * (np.mean(v) - mi[a] - mj[b] + grand) ** 2 for (a, b), v in mij.items())
    sst = ((y - grand) ** 2).sum()
    sse = sst - sum(ss.values())
    return {k: r2(v / (v + sse), 3) for k, v in ss.items()}


def e5():
    rows = [r for r in load("e5_genai.json") if r["tests"] == 400]
    out = {}
    RH = (0.0, 0.25, 0.5, 0.75, 0.9); VV = (1, 5, 20); HH = (0.0, 0.5, 0.9)
    fig, axes = plt.subplots(1, 3, figsize=(W_FULL, 2.55))
    vcol = {1: "#9E9E9E", 5: "#1E88E5", 20: "#0D3C78"}
    for k, c in enumerate(CLASSES):
        a = [r for r in rows if r["cls"] == c]
        S = summarise(a, ("rho", "V", "h"))
        ax = axes[k]
        for h, ls in ((0.0, "-"), (0.9, "--")):
            for V in VV:
                m = [S[(rho, V, h)][0] for rho in RH]
                ax.plot(RH, m, ls, color=vcol[V], marker="o", ms=2.5, lw=1.2,
                        label=f"$V={V}$, $h={h:g}$")
        ax.set_xlabel(r"validity of screening $\rho$")
        ax.set_xticks(RH); ax.set_xticklabels(["0", ".25", ".5", ".75", ".9"])
        ax.set_title(f"({'abc'[k]}) {CLS_NAME[c]}")
        ax.set_ylabel(r"shipped utility, % of $U^*$")
        out[c] = dict(cells={f"{rho}_{V}_{h}": r2(S[(rho, V, h)][0]) for rho in RH for V in VV for h in HH},
                      eta=anova_eta(a, ("rho", "V", "h"), "shipped_pct"),
                      eta_V5_20=anova_eta([r for r in a if r["V"] in (5, 20)], ("rho", "V", "h"), "shipped_pct"))
        out[c]["rho_effect_V5"] = r2(np.mean([S[(0.9, V, h)][0] - S[(0.0, V, h)][0] for V in (5, 20) for h in HH]))
        x = paired([r for r in a if r["h"] == 0.0 and ((r["V"] == 20 and r["rho"] == 0.0) or (r["V"] == 1 and r["rho"] == 0.5))],
                   "V", 20, 1)
        out[c]["V20rho0_minus_V1"] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
        # marginal effects
        out[c]["rho_effect"] = r2(np.mean([S[(0.9, V, h)][0] - S[(0.0, V, h)][0] for V in VV for h in HH]))
        out[c]["V_effect_1_20"] = r2(np.mean([S[(rho, 20, h)][0] - S[(rho, 1, h)][0] for rho in RH for h in HH]))
        out[c]["V_effect_5_20"] = r2(np.mean([S[(rho, 20, h)][0] - S[(rho, 5, h)][0] for rho in RH for h in HH]))
        out[c]["h_effect"] = r2(np.mean([S[(rho, V, 0.9)][0] - S[(rho, V, 0.0)][0] for rho in RH for V in VV]))
        out[c]["V20_rho0_vs_V1_rho05"] = r2(S[(0.0, 20, 0.0)][0] - S[(0.5, 1, 0.0)][0])
    hs, ls_ = axes[0].get_legend_handles_labels()
    fig.legend(hs, ls_, loc="lower center", ncol=6, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=6.8,
               handlelength=2.2, columnspacing=1.0)
    fig.tight_layout(w_pad=1.0, rect=(0, 0.07, 1, 1))
    savefig(fig, "fig_e5_genai.pdf")
    NUM["e5"] = out


# --------------------------------------------------------------------- E6 --
def e6():
    rows = load("e6_bias.json")
    out = {}
    R = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)
    fig, axes = plt.subplots(1, 2, figsize=(W_FULL, 2.5))
    kinds = (("hippo", 2000, "#1E88E5", "favourite (H)"), ("novelty", 2000, "#FB8C00", "novelty (N)"),
             ("instrument", 2000, "#E53935", "instrumentation (I)"),
             ("instrument_audit", 2000, "#43A047", "instrumentation + audit"))

    def loss_curve(a, base_rows=None):
        base_rows = a if base_rows is None else base_rows
        base = {(r["cls"], r["inst"], r["seed"]): r["shipped_pct"] for r in base_rows if r["ratio"] == 0.0}
        res = {}
        for rr in R:
            d = [dict(r, g=r["shipped_pct"] - base[(r["cls"], r["inst"], r["seed"])]) for r in a if r["ratio"] == rr]
            pooled = collections.defaultdict(list)
            for r in d:
                pooled[(r["cls"], r["inst"])].append(r["g"])
            vals = [np.mean(v) for (cc, i), v in pooled.items() if cc != "ref"]
            ref = [r["g"] for r in d if r["cls"] == "ref"]
            res[rr] = dict(fam=t_ci(vals), ref=t_ci(ref), by_cls={cc: t_ci([np.mean(v) for (c2, i), v in pooled.items() if c2 == cc]) if cc != "ref" else t_ci(ref) for cc in CLASSES})
        return res

    for kind, n, col, lab in kinds:
        a = [r for r in rows if r["kind"] == kind and r["n"] == n]
        if kind == "instrument_audit":   # compare with unbiased runs without an audit
            res = loss_curve(a, [r for r in rows if r["kind"] == "instrument" and r["n"] == n])
        else:
            res = loss_curve(a)
        m = [np.mean([res[rr]["by_cls"][c][0] for c in CLASSES]) for rr in R]
        axes[0].plot(R, m, "-o", ms=3, color=col, label=lab)
        out[kind] = {str(rr): {c: [r2(res[rr]["by_cls"][c][0]), r2(res[rr]["by_cls"][c][1])] for c in CLASSES} for rr in R}
    axes[0].axhline(0, color="#555", lw=0.7); axes[0].axvline(1.0, color="#555", lw=0.7, ls="--")
    axes[0].set_xlabel(r"bias relative to test noise $b/\sigma$")
    axes[0].set_ylabel("change in shipped utility (points)")
    axes[0].set_title("(a) Kinds of bias ($n=2000$)")
    axes[0].legend(frameon=False, loc="lower left")
    for n, col in ((500, "#E53935"), (2000, "#1E88E5"), (8000, "#43A047")):
        a = [r for r in rows if r["kind"] == "hippo" and r["n"] == n]
        res = loss_curve(a)
        bs = [np.mean([np.mean([r["b"] for r in a if r["ratio"] == rr])]) for rr in R]
        m = [np.mean([res[rr]["by_cls"][c][0] for c in CLASSES]) for rr in R]
        axes[1].plot(bs, m, "-o", ms=3, color=col, label=f"$n={n}$")
        out[f"hippo_{n}"] = {str(rr): dict(b=r2(b, 3), loss={c: [r2(res[rr]["by_cls"][c][0]), r2(res[rr]["by_cls"][c][1])] for c in CLASSES}) for rr, b in zip(R, bs)}
    axes[1].axhline(0, color="#555", lw=0.7)
    axes[1].set_xlabel("favourite bias $b$ (utility units)")
    axes[1].set_ylabel("change in shipped utility (points)")
    axes[1].set_title("(b) Favourite bias at three test sizes")
    axes[1].legend(frameon=False, loc="lower left")
    fig.tight_layout(w_pad=2.0)
    savefig(fig, "fig_e6_bias.pdf")
    NUM["e6"] = out


# --------------------------------------------------------------------- E7 --
def e7():
    rows = load("e7_drift.json")
    out = {}
    G = (1.0, 0.98, 0.95, 0.90); A = (0.0, 0.05, 0.10, 0.20)
    gcol = {1.0: "#37474F", 0.98: "#1E88E5", 0.95: "#43A047", 0.90: "#E53935"}
    fig, axes = plt.subplots(1, 2, figsize=(W_FULL, 2.5))
    dr = [r for r in rows if r["mode"] == "drift"]
    # tracking: mean over checkpoints from 100 tests on
    agg = collections.defaultdict(list)
    for r in dr:
        if r["tests"] >= 100:
            agg[(r["cls"], r["inst"], r["seed"], r["amp"], r["gamma"])].append(r["track"])
    trows = [dict(cls=k[0], inst=k[1], seed=k[2], amp=k[3], gamma=k[4], track=np.mean(v)) for k, v in agg.items()]
    for g in G:
        m = []
        for amp in A:
            S = summarise([r for r in trows if r["amp"] == amp and r["gamma"] == g], ("cls",), "track")
            m.append(np.mean([S[(c,)][0] for c in CLASSES]))
            out[f"drift_{amp}_{g}"] = {c: [r2(S[(c,)][0]), r2(S[(c,)][1])] for c in CLASSES}
        axes[0].plot(A, m, "-o", ms=3, color=gcol[g], label=fr"$\gamma={g}$")
    axes[0].set_xlabel("amplitude of weight drift"); axes[0].set_ylabel(r"tracking, % of current $U_k^*$")
    axes[0].set_title("(a) Drifting criteria"); axes[0].legend(frameon=False, loc="lower left")
    axes[0].set_ylim(84, 96); axes[0].set_xticks(A)
    # empirical D and 4D check at 400 tests
    late = [r for r in dr if r["tests"] == 400 and r["amp"] > 0]
    for amp in A[1:]:
        a = [r for r in late if r["amp"] == amp]
        D = np.array([r["D"] for r in a]); gap = np.array([r["gap"] for r in a])
        out[f"D_{amp}"] = dict(D_med=r2(np.median(D), 3), gap_med=r2(np.median(gap), 3),
                               share_within_4D=r2(np.mean(gap <= 4 * D), 3), share_within_2D=r2(np.mean(gap <= 2 * D), 3))
    sh = [r for r in rows if r["mode"] == "shift"]
    for g in G:
        T = sorted(set(r["tests"] for r in sh))
        m = []
        for t in T:
            S = summarise([r for r in sh if r["gamma"] == g and r["tests"] == t], ("cls",), "track")
            m.append(np.mean([S[(c,)][0] for c in CLASSES]))
        axes[1].plot(T, m, "-", color=gcol[g], label=fr"$\gamma={g}$")
        out[f"shift_{g}"] = {str(t): r2(v) for t, v in zip(T, m)}
        # mean over the post-shift window
        post = [r for r in sh if r["gamma"] == g and r["tests"] > 200]
        pre = [r for r in sh if r["gamma"] == g and r["tests"] <= 200 and r["tests"] >= 100]
        out[f"shift_{g}_post"] = r2(np.mean([summarise(post, ("cls",), "track")[(c,)][0] for c in CLASSES]))
        out[f"shift_{g}_pre"] = r2(np.mean([summarise(pre, ("cls",), "track")[(c,)][0] for c in CLASSES]))
    axes[1].axvline(200, color="#E53935", lw=0.8, ls="--")
    axes[1].set_xlabel("tests"); axes[1].set_title("(b) Regime shift after 200 tests")
    axes[1].set_ylabel(r"tracking, % of current $U^*$")
    axes[1].legend(frameon=False, loc="lower right")
    fig.tight_layout(w_pad=2.0)
    savefig(fig, "fig_e7_drift.pdf")
    # paired: forgetting 0.95 vs none after the shift
    for g in (0.98, 0.95, 0.90):
        post = [dict(r, gg=str(r["gamma"])) for r in sh if r["tests"] > 200 and r["gamma"] in (1.0, g)]
        agg2 = collections.defaultdict(list)
        for r in post:
            agg2[(r["cls"], r["inst"], r["seed"], r["gamma"])].append(r["track"])
        pr = [dict(cls=k[0], inst=k[1], seed=k[2], gamma=k[3], track=np.mean(v)) for k, v in agg2.items()]
        for c in CLASSES:
            x = paired([r for r in pr if r["cls"] == c], "gamma", g, 1.0, "track")
            out[f"shift_paired_{g}_{c}"] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
        agg3 = collections.defaultdict(list)
        for r in trows:
            if r["gamma"] in (1.0, g) and r["amp"] == 0.0:
                agg3[0].append(r)
        for c in CLASSES:
            x = paired([r for r in trows if r["cls"] == c and r["amp"] == 0.0], "gamma", g, 1.0, "track")
            out[f"static_paired_{g}_{c}"] = dict(diff=r2(x["mean"]), half=r2(x["half"]))
    for g in (0.98, 0.95, 0.90):
        for t in (225, 250, 400):
            for c in CLASSES:
                x = paired([r for r in sh if r["cls"] == c and r["tests"] == t], "gamma", g, 1.0, "track")
                out[f"shift_at{t}_{g}_{c}"] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
    NUM["e7"] = out


# --------------------------------------------------------------------- E8 --
def e8():
    d = load("e8_pareto.json")
    rows = d["rows"]
    out = {"fronts": {c: [int(np.median([v for k, v in d["fronts"].items() if k.startswith(c)])),
                          int(min(v for k, v in d["fronts"].items() if k.startswith(c))),
                          int(max(v for k, v in d["fronts"].items() if k.startswith(c)))] for c in CLASSES}}
    M = (("archive", "#43A047", "Pareto archive"), ("scalarised3", "#1E88E5", "three scalarised loops"), ("single", "#9E9E9E", "one DVF-weighted loop"))
    B = (200, 400, 800)
    fig, axes = plt.subplots(1, 3, figsize=(W_FULL, 2.4))
    for metric, ax, lab in (("hv", axes[0], "Hypervolume, share of the true front"), ("share_local", axes[1], "Share locally Pareto-optimal"),
                            ("size", axes[2], "Configurations delivered")):
        for k, (m, col, name) in enumerate(M):
            ys, hs = [], []
            for b in B:
                S = summarise([r for r in rows if r["method"] == m and r["budget"] == b], ("cls",), metric)
                ys.append(np.mean([S[(c,)][0] for c in CLASSES])); hs.append(np.mean([S[(c,)][1] for c in CLASSES]))
                for c in CLASSES:
                    out.setdefault(f"{m}_{b}", {}).setdefault(metric, {})[c] = [r2(S[(c,)][0], 3), r2(S[(c,)][1], 3)]
            ax.errorbar(np.array(B) * (1 + 0.04 * (k - 1)), ys, yerr=hs, fmt="-o", ms=3, color=col, label=name, capsize=0)
        ax.set_xscale("log"); ax.set_xticks(B); ax.set_xticklabels([str(b) for b in B]); ax.minorticks_off()
        ax.set_xlabel("tests (log scale)")
        ax.set_ylabel({"hv": "hypervolume / true-front hypervolume", "share_local": "share of delivered configurations",
                       "size": "number of configurations"}[metric])
        ax.set_title(f"({'abc'[['hv','share_local','size'].index(metric)]}) {lab}", loc="left", fontsize=7.5)
    axes[0].legend(frameon=False, loc="lower right", fontsize=6.5)
    fig.tight_layout(w_pad=1.0)
    savefig(fig, "fig_e8_pareto.pdf")
    for b in B:
        for c in CLASSES:
            x = paired([r for r in rows if r["cls"] == c and r["budget"] == b], "method", "archive", "scalarised3", "hv")
            out[f"hv_paired_{b}_{c}"] = dict(diff=r2(x["mean"], 3), half=r2(x["half"], 3), p=float(f"{x['p']:.2g}"))
    NUM["e8"] = out


# --------------------------------------------------------------------- E9 --
def e9():
    rows = load("e9_robustness.json")
    out = {}
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["sid"], r["seed"])][r["pol"]] = r
    sc = collections.defaultdict(lambda: collections.defaultdict(list))
    meta = {}
    for (sid, seed), v in by.items():
        for p, r in v.items():
            sc[sid][p].append(r["shipped_pct"])
        meta[sid] = next(iter(v.values()))
    recs = []
    for sid, v in sc.items():
        m = meta[sid]
        L = get_landscape(m["fam"], m["inst"], 2 if m["nf"] == 14 else 0, ("CHAT", "AUTOC") if m["nf"] == 10 else ())
        sig = L.sigma(m["n_sess"])
        top = np.sort(L.U)[-50:].std()
        rec = dict(sid=sid, fam=m["fam"], nf=m["nf"], n_sess=m["n_sess"], budget=m["budget"], rho=m["rho"], V=m["V"],
                   radius=m["radius"], snr=float(top / sig), lo2=int(L.local_optima(2).sum()))
        for p in ("abtest", "oneshot", "loop", "ledger"):
            rec[p] = float(np.mean(v[p]))
        recs.append(rec)
    out["n_scen"] = len(recs)
    for comp in ("abtest", "oneshot", "loop"):
        dlt = np.array([r["ledger"] - r[comp] for r in recs])
        out[f"vs_{comp}"] = dict(mean=r2(dlt.mean()), median=r2(np.median(dlt)), share_pos=r2(np.mean(dlt > 0), 3),
                                 q10=r2(np.percentile(dlt, 10)), q90=r2(np.percentile(dlt, 90)))
    # regression of the advantages on standardised scenario factors
    names = ["log test size", "log budget", "screen validity", "ideas per round", "radius", "features", "rugged family", "log SNR"]
    X = np.array([[np.log(r["n_sess"]), np.log(r["budget"]), r["rho"], r["V"], r["radius"], r["nf"],
                   1.0 if r["fam"] == "rug" else 0.0, np.log(r["snr"])] for r in recs])
    Xs = (X - X.mean(0)) / X.std(0)
    Xd = np.column_stack([np.ones(len(Xs)), Xs])
    fig, axes = plt.subplots(1, 2, figsize=(W_FULL, 2.6), gridspec_kw=dict(width_ratios=[1.25, 1]))
    for j, (comp, col) in enumerate((("abtest", "#FB8C00"), ("oneshot", "#8E24AA"), ("loop", "#1E88E5"))):
        y = np.array([r["ledger"] - r[comp] for r in recs])
        beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
        res = y - Xd @ beta
        # HC3 robust standard errors
        H = Xd @ np.linalg.inv(Xd.T @ Xd) @ Xd.T
        hdiag = np.diag(H)
        meat = Xd.T @ np.diag(res ** 2 / (1 - hdiag) ** 2) @ Xd
        bread = np.linalg.inv(Xd.T @ Xd)
        se = np.sqrt(np.diag(bread @ meat @ bread))
        r2v = 1 - res.var() / y.var()
        out[f"reg_{comp}"] = dict(coef={n: [r2(b), r2(1.96 * s)] for n, b, s in zip(["intercept"] + names, beta, se)}, R2=r2(r2v, 3))
        yy = np.arange(len(names)) + (j - 1) * 0.22
        axes[0].errorbar(beta[1:], yy, xerr=1.96 * se[1:], fmt="o", ms=3, color=col, capsize=0, lw=1,
                         label="ledger − " + {"abtest": "champion–challenger A/B", "oneshot": "launch-and-learn", "loop": "design-thinking loop"}[comp])
    axes[0].axvline(0, color="#555", lw=0.7)
    axes[0].set_yticks(range(len(names))); axes[0].set_yticklabels(names); axes[0].invert_yaxis()
    axes[0].set_xlabel("effect of +1 s.d. of the factor (points)")
    axes[0].set_ylabel("scenario factor (standardised)")
    axes[0].set_title("(a) What drives the ledger's advantage")
    axes[0].grid(axis="y", visible=False)
    axes[0].legend(frameon=False, loc="upper center", fontsize=6.5, ncol=3, bbox_to_anchor=(0.75, -0.2),
                   columnspacing=1.0, handletextpad=0.3)
    snr = np.array([r["snr"] for r in recs])
    for comp, col in (("abtest", "#FB8C00"), ("oneshot", "#8E24AA")):
        y = np.array([r["ledger"] - r[comp] for r in recs])
        axes[1].scatter(snr, y, s=9, color=col, alpha=0.75, lw=0, label="vs " + {"abtest": "champion–challenger A/B", "oneshot": "launch-and-learn"}[comp])
    axes[1].axhline(0, color="#555", lw=0.7)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("signal-to-noise: s.d. of top-50 utilities / $\\sigma$")
    axes[1].set_ylabel("ledger advantage (points)")
    axes[1].set_title("(b) Advantage by signal-to-noise")
    axes[1].legend(frameon=True, framealpha=0.92, edgecolor="none", loc="upper right")
    fig.tight_layout(w_pad=1.5, rect=(0, 0.06, 1, 1))
    savefig(fig, "fig_e9_robustness.pdf")
    out["snr_range"] = [r2(snr.min(), 3), r2(snr.max(), 3)]
    NUM["e9"] = out


if __name__ == "__main__":
    which = [w for w in (sys.argv[1:] or ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "e9", "e10", "e11"]) if w not in ("e10", "e11")]
    for w in which:
        fn = {"e1": "e1_validation.json", "e2": "e2_dynamics.json", "e3": "e3_policies.json", "e4": "e4_allocation.json",
              "e5": "e5_genai.json", "e6": "e6_bias.json", "e7": "e7_drift.json", "e8": "e8_pareto.json", "e9": "e9_robustness.json"}[w]
        if os.path.exists(os.path.join(RES, fn)):
            print("analysing", w, flush=True)
            globals()[w]()
            json.dump(NUM, open(NUM_PATH, "w"), indent=1)


# -------------------------------------------------------------------- E10 --
def e10():
    rows = load("e10_review.json")
    out = {}
    for part in ("ab", "kappa", "perturb"):
        a = [r for r in rows if r["part"] == part]
        key = ("pol", "sd") if part == "perturb" else ("pol",)
        for c in CLASSES:
            S = summarise([r for r in a if r["cls"] == c], key)
            for k, v in S.items():
                out.setdefault(part, {}).setdefault(" | ".join(map(str, k)), {})[c] = [r2(v[0]), r2(v[1])]
    # paired: ledger vs strongest A/B variant
    a = [r for r in rows if r["part"] == "ab"]
    for c in CLASSES:
        for p in ("A/B (5%, no pooling)", "A/B pooled (5%)", "A/B ship-higher", "A/B pooled ship-higher"):
            x = paired([r for r in a if r["cls"] == c], "pol", "ledger", p)
            out.setdefault("ab_paired", {}).setdefault(p, {})[c] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
    a = [r for r in rows if r["part"] == "perturb"]
    for sd in (0.0, 0.044, 0.088):
        for c in CLASSES:
            for p in ("abtest", "oneshot", "loop"):
                x = paired([r for r in a if r["cls"] == c and r["sd"] == sd], "pol", "ledger", p)
                out.setdefault("perturb_paired", {}).setdefault(f"{sd}", {}).setdefault(p, {})[c] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
    NUM["e10"] = out


if __name__ == "__main__" and "e10" in sys.argv[1:]:
    e10()
    json.dump(NUM, open(NUM_PATH, "w"), indent=1)


# -------------------------------------------------------------------- E11 --
def e11():
    import importlib
    LADDER = [n for n, _ in importlib.import_module("e11_audit").LADDER]
    rows = [r for r in load("e11_audit.json") if r["tests"] == 400]
    rows += [r for r in load("e11b_audit.json") if r["tests"] == 400]
    out = {}
    lad = [r for r in rows if r["part"] == "ladder"]
    steps = LADDER[:8]
    names = ["A/B, one test per arm", "+ pool champion evidence", "+ retain all variants", "+ re-test favourite 4x per build",
             "+ re-test three leaders", "+ rotating re-test (loop)", "+ ship on lower bound", "+ three builds per round (ledger)"]
    fig, axes = plt.subplots(1, 2, figsize=(W_FULL, 2.9), gridspec_kw=dict(width_ratios=[1.25, 1]))
    for c in CLASSES:
        S = summarise([r for r in lad if r["cls"] == c], ("pol",))
        m = [S[(s,)][0] for s in steps]; h = [S[(s,)][1] for s in steps]
        axes[0].errorbar(m, np.arange(len(steps)) + {"ref": -0.2, "svc": 0, "rug": 0.2}[c], xerr=h, fmt="o", ms=3.5,
                         color=COL[c], capsize=0, lw=1, label=CLS_NAME[c])
        out[f"ladder_{c}"] = {s: [r2(S[(s,)][0]), r2(S[(s,)][1])] for s in steps + ["launch-and-learn", "L2b + screen from the idea pool"]}
        out[f"ladder_steps_{c}"] = {}
        for p, q in zip(steps[:-1], steps[1:]):
            x = paired([r for r in lad if r["cls"] == c], "pol", q, p)
            out[f"ladder_steps_{c}"][q] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
        x = paired([r for r in lad if r["cls"] == c], "pol", "L2b + screen from the idea pool", "L2 + retain all variants")
        out[f"ladder_steps_{c}"]["L2b vs L2"] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
    axes[0].set_yticks(range(len(steps))); axes[0].set_yticklabels(names); axes[0].invert_yaxis()
    axes[0].set_ylabel("design principle added"); axes[0].set_xlabel(r"shipped utility, % of $U^*$")
    axes[0].set_title("(a) From A/B testing to the ledger"); axes[0].grid(axis="y", visible=False)
    axes[0].legend(frameon=False, loc="lower left", fontsize=6.5)
    kn = [r for r in rows if r["part"] == "knew"] + [r for r in rows if r["part"] == "start" and r["pol"] in ("oneshot", "abtest_pooled")]
    labels = {"ledger k_new=1": ("ledger, 1 build / 5 tests", "#43A047", "-"), "ledger k_new=2": ("ledger, 2 builds / 5 tests", "#43A047", "--"),
              "ledger k_new=3": ("ledger, 3 builds / 5 tests", "#43A047", ":"), "oneshot": ("launch-and-learn", "#8E24AA", "-"),
              "abtest_pooled": ("A/B, pooled champion", "#FB8C00", "-")}
    for pol, (lab, col, ls) in labels.items():
        ys = []
        for st in ("random", "statusquo"):
            S = summarise([r for r in kn if r["pol"] == pol and r["start"] == st], ("cls",))
            ys.append(np.mean([S[(c,)][0] for c in CLASSES]))
            out.setdefault(f"start_{st}", {})[pol] = {c: [r2(S[(c,)][0]), r2(S[(c,)][1])] for c in CLASSES}
        axes[1].plot([0, 1], ys, ls, marker="o", ms=3.5, color=col, label=lab)
    axes[1].set_xticks([0, 1]); axes[1].set_xticklabels(["five random\nconfigurations", "production configuration\nwith history"])
    axes[1].set_xlim(-0.3, 1.3); axes[1].set_xlabel("starting point of the programme")
    axes[1].set_ylabel(r"shipped utility, % of $U^*$ (mean of classes)")
    axes[1].set_title("(b) Build rate and starting point"); axes[1].legend(frameon=False, fontsize=6.3, loc="lower left")
    fig.tight_layout(w_pad=2.0)
    savefig(fig, "fig_e11_audit.pdf")
    for st in ("random", "statusquo"):
        for c in CLASSES:
            a = [r for r in kn if r["cls"] == c and r["start"] == st]
            for q, p in (("ledger k_new=3", "ledger k_new=1"), ("ledger k_new=3", "oneshot"), ("ledger k_new=3", "abtest_pooled")):
                x = paired(a, "pol", q, p)
                out.setdefault(f"start_paired_{st}", {})[f"{q} - {p} | {c}"] = dict(diff=r2(x["mean"]), half=r2(x["half"]), p=float(f"{x['p']:.2g}"))
    sg = [r for r in rows if r["part"] == "sigma"]
    for c in CLASSES:
        S = summarise([r for r in sg if r["cls"] == c], ("pol", "factor"))
        out[f"sigma_{c}"] = {f"{k[0]} x{k[1]}": [r2(v[0]), r2(v[1])] for k, v in S.items()}
    NUM["e11"] = out


if __name__ == "__main__" and "e11" in sys.argv[1:]:
    e11()
    json.dump(NUM, open(NUM_PATH, "w"), indent=1)
