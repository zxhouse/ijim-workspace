"""E13  A language model as idea generator and screen in the testbed.

Requires an Anthropic API key in ANTHROPIC_API_KEY (not available in the
cloud session in which the other experiments were run; run locally).

Measures, on the reference service:
(a) screening validity rho_LLM: the model rates the promise of configurations
    (as a product manager would, from the capability descriptions and a short
    brief of the service) and the ratings are correlated with true utility
    across the configuration space and among variants of the leaders;
(b) idea diversity: the model proposes variants of a leader; the share of
    proposals confined to the model's favourite capabilities (homogenisation
    h_LLM) and the mean pairwise Jaccard distance of proposals;
(c) a ledger run in which the model's ratings replace the synthetic screen,
    compared with the synthetic screen of the same measured validity.

Costs about 2,000 requests of a few hundred tokens each; use
MODEL="claude-haiku-5-5" for a cheaper first pass.
"""
import json
import os
import sys

import numpy as np

from common import *  # noqa

MODEL = os.environ.get("E13_MODEL", "claude-opus-5-5")
N_RATE = int(os.environ.get("E13_N_RATE", "300"))
N_IDEAS = int(os.environ.get("E13_N_IDEAS", "40"))


def brief(L):
    p = L.p
    lines = [f"Online retail service, {p.lam_s:.0f} sessions per second, {100*p.mobile_share:.0f}% on mobile; "
             f"application pool of {p.c_app} workers; profit margin {100*p.margin:.0f}%.",
             "Optional capabilities (flag: description):"]
    for f in p.features:
        lines.append(f"- {f.key}: {f.name}")
    lines.append("A configuration is judged on user conversion (45%), feasibility: p95 latency within SLO and "
                 "operational complexity (25%), and hourly profit after infrastructure and fraud costs (30%).")
    return "\n".join(lines)


def client():
    import anthropic
    return anthropic.Anthropic()


def rate_configs(L, xs, cl):
    keys = L.p.keys
    scores = []
    for x in xs:
        on = [keys[i] for i in range(L.n) if x >> i & 1] or ["(no optional capability)"]
        msg = (brief(L) + "\n\nRate the following configuration on a 0-100 scale for its overall value under the "
               "three criteria. Reply with the number only.\nEnabled: " + ", ".join(on))
        r = cl.messages.create(model=MODEL, max_tokens=16, output_config={"effort": "low"},
                               messages=[{"role": "user", "content": msg}])
        txt = "".join(b.text for b in r.content if b.type == "text")
        try:
            scores.append(float(txt.strip().split()[0]))
        except (ValueError, IndexError):
            scores.append(np.nan)
    return np.array(scores)


def propose_ideas(L, parent, n, cl):
    keys = L.p.keys
    on = [keys[i] for i in range(L.n) if parent >> i & 1]
    msg = (brief(L) + f"\n\nThe current leading configuration enables: {', '.join(on) or '(none)'}. "
           f"Propose {n} distinct variants that change one or two capabilities (enable or disable). "
           "Reply as a JSON list of lists of flag names to toggle, nothing else.")
    r = cl.messages.create(model=MODEL, max_tokens=2000, messages=[{"role": "user", "content": msg}])
    txt = "".join(b.text for b in r.content if b.type == "text")
    try:
        ideas = json.loads(txt[txt.index("["): txt.rindex("]") + 1])
    except (ValueError, json.JSONDecodeError):
        return []
    out = []
    for toggles in ideas:
        x = parent
        for t in toggles:
            if t in keys:
                x ^= 1 << keys.index(t)
        if x != parent:
            out.append(x)
    return out


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("E13 needs ANTHROPIC_API_KEY; see the docstring.")
    cl = client()
    L = get_landscape("ref", 0)
    rng = np.random.default_rng(13)
    # (a) screening validity over the space and near the leaders
    xs_all = rng.choice(L.N, N_RATE, replace=False)
    top = np.argsort(L.U)[-30:]
    xs_near = np.unique(np.concatenate([L.neighbours(int(t), 1) for t in top]))[:N_RATE]
    s_all = rate_configs(L, xs_all, cl); s_near = rate_configs(L, xs_near, cl)
    ok_a = ~np.isnan(s_all); ok_n = ~np.isnan(s_near)
    rho_all = float(np.corrcoef(s_all[ok_a], L.U[xs_all][ok_a])[0, 1])
    rho_near = float(np.corrcoef(s_near[ok_n], L.U[xs_near][ok_n])[0, 1])
    # (b) diversity of proposals
    ideas = []
    for t in rng.choice(top, 5, replace=False):
        ideas += [(int(t), x) for x in propose_ideas(L, int(t), N_IDEAS // 5, cl)]
    flips = [p ^ x for p, x in ideas]
    counts = np.zeros(L.n)
    for f in flips:
        for i in range(L.n):
            counts[i] += f >> i & 1
    share_top4 = float(np.sort(counts)[-4:].sum() / max(counts.sum(), 1))
    jacc = []
    for i in range(len(flips)):
        for j in range(i + 1, len(flips)):
            a, b = flips[i], flips[j]
            jacc.append(1 - bin(a & b).count("1") / max(bin(a | b).count("1"), 1))
    out = dict(model=MODEL, rho_all=rho_all, rho_near=rho_near, n_rated=int(ok_a.sum() + ok_n.sum()),
               share_flips_in_top4=share_top4, mean_jaccard_distance=float(np.mean(jacc)) if jacc else None,
               n_ideas=len(ideas), flips_per_capability=counts.tolist())
    # (c) ledger with the measured validity against the synthetic screen
    rows = []
    for s in range(60):
        for rho, lab in ((rho_near, "llm-equivalent"), (RHO0, "default")):
            log, E = run(L, Config(policy="ledger", sigma=L.sigma(2000), rho=rho, checkpoints=(400,)), s)
            rows.append(dict(seed=s, screen=lab, shipped_pct=100 * log[-1]["shipped"] / L.Ustar))
    out["ledger_runs"] = rows
    save("e13_llm_ideation.json", out)
    print(json.dumps({k: v for k, v in out.items() if k != "ledger_runs"}, indent=1))


if __name__ == "__main__":
    main()
