# Audit of the manuscript and testbed (round 2)

Scope: code of the testbed and policies, the assumptions behind the evaluation, and every numerical claim in the manuscript. Where an assumption looked load-bearing it was tested by experiment (E11, 17,200 runs; `experiments/e11_audit.py`, `e11b_audit.py`).

## 1. Defect found and corrected

**Champion–challenger engine stopped early.** When every variant of the champion had been built (small ideation reach), `ABEngine` broke out of its loop before the budget was spent. The policy now proposes variants of another tested configuration. E3, E9 and E10 were re-run; A/B results rose by up to 3 points on the rugged family, and the "ideation reach" effect in the E9 regression (−4.5 points per s.d.) disappeared (now +0.1): it was an artefact of the defect. All numbers in the manuscript, highlights and graphical abstract were updated (headline advantage now 7.9–16.7 points instead of 8.5–14.7; E9 share of scenarios won 90 % instead of 92.5 %, mean +7.6 instead of +11.2; lead over the pooled A/B variant 4.9–7.3 instead of 7.6–8.4).

## 2. Assumptions tested

| Assumption / choice | Risk | Test | Outcome | Change to the paper |
|---|---|---|---|---|
| Beliefs use the landscape-average test noise, but noise is heteroscedastic (σ = 0.156 among the top-50 vs 0.120 average; r(σ,U)=0.88) | over-confident beliefs where decisions are made | σ assumed ×0.5, ×1.3, ×2; σ learned online from re-test residuals | ±1.5 points at most; learned σ (≈0.145) changes nothing | reported in E11; no change to conclusions |
| Programmes start from 5 random configurations (38 % of U*) | flatters all policies; A/B champion starts untested | start from the production configuration (57 % of U*) with 10 free history tests | all policies lose 0.2–3.0 points; the ledger (1 build/5 tests) loses most and falls behind launch-and-learn | **recommendation 3 and DP4 changed**: build 2–3 per 5 tests; with 3 builds the ledger regains 0.9–5.6 points and is level with launch-and-learn, +5.8 to +8.5 vs pooled A/B |
| The ledger's default build rate (1 per 5 tests) came from the theory's loop, not from E4 (which found 3–4 best) | artefact not at its own optimum | k_new ∈ {1,2,3} × start | see above | limitation and E11 text |
| The loop screens the best idea from an accumulating pool, A/B only from the current round's ideas | A/B handicapped by weaker use of the screen, not by evidence management | A/B + pool + retention + pool screening | −0.1 to −2.3 points (n.s.): no handicap | stated in E11 |
| Which design principle carries the advantage? | the paper attributed it loosely | ladder A/B → +pool → +retain → +re-test ×4 → +3 leaders → +rotation → +LCB | pooling +3, re-tests per build +4, three leaders +1–3, LCB +1, **rotation 0 or negative** | 6.1 decomposition rewritten; rotating re-test (theorem's A4) reported as worthless at this horizon |
| E5: "20 ideas without a valid screen = 1 idea" | tautological in a model where ideas are exchangeable without a screen | reading of the model | structural, not empirical | sentence added to 5.5 |

## 3. Claims checked against `results/numbers.json`

Every number in Sections 5.1–5.10, the abstract, Table 10 (hypotheses), the recommendations, highlights and the graphical abstract was re-derived from `numbers.json` after the re-runs. Changed values are listed in section 1. Unchanged experiments (E1, E2, E4–E8) do not involve the A/B engine.

## 4. What the audit did not change

- The advantage over champion–challenger testing (7.9–16.7 points; 4.9–7.3 over its strongest pooled variant) and its direction in every class, budget and scenario.
- The equivalence of the ledger with Thompson sampling and, at n = 2,000, with launch-and-learn.
- The bias, drift and stakeholder results (E6–E8), which do not depend on the A/B engine or on the start.

## 5. Open points for the authors

1. The ledger as evaluated in E2–E10 uses 1 build per 5 tests. E11 shows 2–3 is better from a realistic start. A full re-run of E2–E10 with the new default (~30 min) would make the artefact consistent with its own recommendation; the paper currently reports the discrepancy instead.
2. `L.sigma(n)` is a landscape average; a per-leader σ (or the learned σ now implemented, `sigma_learn=True`) is the cleaner default for a production system, although it makes no difference in the testbed.
3. The production-start scenario uses the bare service as status quo; a service that already has several capabilities enabled would start closer to the optimum and reduce every policy's measured gain.
