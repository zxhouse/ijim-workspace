# Response to internal review round 1

All page/section references are to the revised manuscript (`paper/manuscript.pdf`). New analyses are in `experiments/e10_robustness_review.py` (8,800 runs) and are reported in the new Section 5.10 and Table 9.

| ID | Comment (short) | Response and change |
|---|---|---|
| R1.1 | What is the IS contribution? Present the design theory (Gregor & Jones). | New Section 3.3 *The ledger as an information system*: what the ledger stores, displays and proposes, and which decisions stay with people. New Table 2 maps the study onto the eight components of a design theory. |
| R1.2 | State the evaluation strategy; add an expository instantiation. | Section 4 now states the FEDS strategy (summative, artificial; efficacy and robustness; technical risk first; naturalistic evaluation next). New Table 3 shows a real ledger excerpt after 100 tests, illustrating the optimiser's curse and the role of evidence counts and screening. |
| R1.3 | Champion–challenger may be a straw man. | New E10(a): pooled champion evidence and a "ship the higher arm" rule. Pooling raises A/B to 86.0–87.2 %; the ledger still leads by 7.6–8.4 points (p < 10⁻⁵ on every class); the looser rule is worse. Added to Section 5.3, 5.10, Table 9 and Table 10 (H2). |
| R1.4 | Do not attribute the large gains to DP5 alone. | Section 6.1 now decomposes the advantage: most from retaining/pooling/re-testing (shared with the loop), about one point from the ship rule, which shrinks under model misspecification. |
| R1.5 | Ethics of experimenting on users. | New paragraph in Section 6.3 (consent, review of sensitive variants, accountability, fewer users exposed to falsely promoted variants). |
| R2.1 | Ground truth is the model. | New E10(c): true utilities perturbed by the model error measured in E1 (s.d. 0.044) and twice that. The lead over champion–challenger stays at 7.2–11.7 points; the lead over the plain loop shrinks to 0.0–0.5 points (reported). |
| R2.2 | Sensitivity to κ; was it tuned? | κ = 1 was fixed a priori (one posterior s.d.). New E10(b): κ between 0.5 and 2 changes shipped utility by at most 0.8 points; κ = 0 is the plain loop. |
| R2.3 | Justify the number of runs. | Section 4.8: runs chosen for ≈1-point half-widths on the reference instance and several runs per family instance. |
| R2.4 | Common shocks. | Limitations: direction of the bias (penalises comparisons with earlier evidence, favours concurrent re-tests of leaders) stated. |
| R2.5 | Units in the ANOVA. | Stated in the text of Section 5.5. |
| R3.1 | How to estimate screening validity ρ in practice? | Section 3.3 and Recommendation 4: the ledger stores screening scores and first test results, so their correlation, corrected for the reliability of one test, estimates ρ online. |
| R3.2 | Cost of building variants. | Limitations: dearer building moves the optimum towards re-testing, strengthening the case for the ledger relative to launch-and-learn. |
| R3.3 | Engage with recent LLM ideation literature. | Added and verified: Girotra et al. (2023) evaluation-bottleneck conjecture, Si et al. (2025), Anderson et al. (2024), Meincke et al. (2024), Boussioux et al. (2024); Dell'Acqua et al. updated to the 2026 *Organization Science* version. |
| R3.4 | Caveat on many small tests. | Recommendation 3 now notes the lower bound from metric stability and sample-ratio checks (Fabijan et al., 2019). |

Additional literature integrated during the review: Auer et al. (2021) review of continuous experimentation; Deng et al. (2013) variance reduction; Schwartz et al. (2017) bandits in marketing; Prat et al. (2015) IS artefact evaluation; Wang & Strong (1996) data quality; Azevedo et al. (2020) now used to interpret E4.
