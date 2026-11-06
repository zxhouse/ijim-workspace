"""E13  Analysis of the language-model judge and generator run.

Inputs (produced by blind judge sessions of a Claude model, see e13 README in
the paper's data repository): ratings  out/<model>_<svc>_batch*.json  mapping
configuration id -> 0-100 score; ideas  out/<model>_<svc>_ideas.json  mapping
leader id -> list of lists of flags to toggle.  Items and leaders are in
<svc>_items.json / <svc>_leaders.json.
"""
import glob
import json
import os
import sys

import numpy as np

from common import *  # noqa

E13 = os.environ.get("E13_DIR", os.path.join(RES, "e13"))


def load_items(svc):
    d = json.load(open(f"{E13}/{svc}_items.json"))
    return d, {it["id"]: it for it in d["items"]}


def ratings(model, svc):
    out = {}
    for f in sorted(glob.glob(f"{E13}/out/{model}_{svc}_batch*.json")):
        txt = open(f).read()
        try:
            j = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            continue
        for k, v in j.items():
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                pass
    return out


def validity(model, svc, rng):
    d, by_id = load_items(svc)
    L = get_landscape(d["cls"], d["inst"])
    r = ratings(model, svc)
    ids = [i for i in by_id if i in r]
    if len(ids) < 10:
        return None
    x = np.array([by_id[i]["x"] for i in ids]); s = np.array([r[i] for i in ids])
    u = L.U[x]
    is_rand = np.array([int(i[1:]) < d["n_rand"] for i in ids])
    res = dict(n=len(ids), n_missing=len(by_id) - len(ids))
    for name, m in (("all", np.ones(len(ids), bool)), ("random", is_rand), ("near_leaders", ~is_rand)):
        if m.sum() < 10:
            continue
        rho = np.corrcoef(s[m], u[m])[0, 1]
        from scipy import stats
        sp = stats.spearmanr(s[m], u[m])[0]
        boot = []
        idx = np.flatnonzero(m)
        for _ in range(2000):
            b = rng.choice(idx, len(idx))
            boot.append(np.corrcoef(s[b], u[b])[0, 1])
        # validity relative to the ledger's screen definition: correlation with
        # the standardised utility over the subset
        res[name] = dict(rho=float(rho), ci=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                         spearman=float(sp), n=int(m.sum()),
                         top_decile_precision=float(np.mean(u[m][np.argsort(-s[m])[: max(1, m.sum() // 10)]] >= np.percentile(u[m], 90))))
    # does the judge recognise overload? share of configurations beyond capacity in its top quartile
    over = L.ev["rho_max"][x] >= 0.97
    top_q = s >= np.percentile(s, 75)
    res["overloaded_share_in_top_quartile"] = float(np.mean(over[top_q])) if top_q.any() else None
    res["overloaded_share_overall"] = float(np.mean(over))
    return res


def ideas(model, svc):
    d, _ = load_items(svc)
    L = get_landscape(d["cls"], d["inst"]); keys = L.p.keys
    f = f"{E13}/out/{model}_{svc}_ideas.json"
    if not os.path.exists(f):
        return None
    txt = open(f).read()
    j = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    leaders = json.load(open(f"{E13}/{svc}_leaders.json"))["leaders"]
    flips, utils, parents_u, valid = [], [], [], 0
    counts = np.zeros(L.n)
    for k, t in enumerate(leaders):
        for toggles in j.get(f"L{k}", []):
            x = t; ok = True
            for name in toggles:
                if name in keys:
                    x ^= 1 << keys.index(name)
                else:
                    ok = False
            if ok and x != t:
                valid += 1; flips.append(x ^ t); utils.append(L.U[x]); parents_u.append(L.U[t])
                for i in range(L.n):
                    counts[i] += (x ^ t) >> i & 1
    jacc = []
    for i in range(len(flips)):
        for jj in range(i + 1, len(flips)):
            a, b = flips[i], flips[jj]
            jacc.append(1 - bin(a & b).count("1") / max(bin(a | b).count("1"), 1))
    # reference: random one-or-two-capability variants of the same leaders
    rng = np.random.default_rng(5)
    rflips = []
    for t in leaders:
        for _ in range(8):
            m = rng.integers(1, 3); bits = rng.choice(L.n, m, replace=False)
            f_ = 0
            for b in bits:
                f_ |= 1 << int(b)
            rflips.append(f_)
    rcounts = np.zeros(L.n)
    for f_ in rflips:
        for i in range(L.n):
            rcounts[i] += f_ >> i & 1
    rutils = []
    for t, f_ in zip(np.repeat(leaders, 8), rflips):
        rutils.append(L.U[t ^ f_])
    return dict(n_valid=valid, share_flips_in_top4=float(np.sort(counts)[-4:].sum() / max(counts.sum(), 1)),
                share_flips_in_top4_random=float(np.sort(rcounts)[-4:].sum() / max(rcounts.sum(), 1)),
                mean_jaccard_distance=float(np.mean(jacc)) if jacc else None,
                flips_per_capability={keys[i]: int(counts[i]) for i in range(L.n)},
                mean_utility_of_ideas=float(np.mean(utils)), mean_utility_random_variants=float(np.mean(rutils)),
                share_improving=float(np.mean(np.array(utils) > np.array(parents_u))),
                share_improving_random=float(np.mean(np.array(rutils) > np.repeat([L.U[t] for t in leaders], 8))))


def ledger_with(rho, L, seeds=100, V=5):
    out = []
    for s in range(seeds):
        log, _ = run(L, Config(policy="ledger", sigma=L.sigma(2000), rho=rho, ideas=V, checkpoints=(400,)), s)
        out.append(100 * log[-1]["shipped"] / L.Ustar)
    return out


def main():
    rng = np.random.default_rng(0)
    res = {}
    for model in ("opus", "haiku"):
        for svc in ("A", "B"):
            v = validity(model, svc, rng)
            if v:
                res[f"validity_{model}_{svc}"] = v
            i = ideas(model, svc)
            if i:
                res[f"ideas_{model}_{svc}"] = i
    # ledger runs with the measured near-leader validity of each model on A
    L = get_landscape("ref", 0)
    runs = {}
    for model in ("opus", "haiku"):
        v = res.get(f"validity_{model}_A", {}).get("near_leaders")
        if v:
            for V in (5, 20):
                runs[f"{model}_V{V}"] = ledger_with(max(v["rho"], 0.0), L, V=V)
    for V in (5, 20):
        runs[f"default_V{V}"] = ledger_with(RHO0, L, V=V)
        runs[f"none_V{V}"] = ledger_with(0.0, L, V=V)
    res["ledger"] = {k: dict(mean=float(np.mean(v)), half=float(1.96 * np.std(v, ddof=1) / np.sqrt(len(v)))) for k, v in runs.items()}
    for k in list(runs):
        if k.startswith(("opus", "haiku")):
            V = k.split("_V")[1]
            d = np.array(runs[k]) - np.array(runs[f"none_V{V}"])
            res["ledger"][k]["vs_none"] = dict(diff=float(d.mean()), half=float(1.96 * d.std(ddof=1) / np.sqrt(len(d))))
    save("e13_llm_judge.json", res)
    print(json.dumps({k: v for k, v in res.items()}, indent=1)[:6000])


if __name__ == "__main__":
    main()
