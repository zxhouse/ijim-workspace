# Internal review round 1 — IJIM manuscript

*Managing evidence, not ideas: A convergence-based design of experimentation information systems for digital services in the age of generative AI*

Three internal reviews written in the role of IJIM referees (double-anonymised; the reviewers saw the anonymised PDF only). Each comment has an ID that the response letter (`round1_response.md`) refers to.

---

## Reviewer 1 — Information systems theory and design science

**Summary.** The paper derives design principles for experimentation information systems from a convergence theorem, instantiates them in an "evidence ledger" and evaluates the artefact in a simulated digital service. The topic fits IJIM well (decision-making, analytics, GenAI). Recommendation: **major revision**.

**R1.1 (major) — What exactly is the IS contribution?** The ledger reads partly as an algorithm (a ship rule plus a re-test schedule). The paper should make explicit what is *information-systems* about it: the information it stores, who uses it, which decisions it supports, and what remains a human judgement. Please present the design theory with the components of Gregor and Jones (2007) so that readers can see purpose, constructs, principles, mutability, testable propositions, justificatory knowledge, implementation principles and the expository instantiation.

**R1.2 (major) — Evaluation strategy.** Evaluation is purely artificial. That is defensible for a first DSR cycle (FEDS), but the paper should state its evaluation strategy explicitly (purpose, paradigm, properties evaluated, risks) and lay out a concrete naturalistic evaluation path. An expository walk-through of one round of the ledger on the reference service would make the artefact tangible.

**R1.3 (major) — Is the champion–challenger baseline a straw man?** The practice baseline discards the evidence of earlier tests and uses a 5 % one-sided threshold. Many organisations pool the champion's evidence or use a looser rule ("ship the higher"). Please show that the main result survives stronger versions of the practice baseline.

**R1.4 (minor)** — The difference between the ledger and the plain loop is about one point; the abstract and highlights should not suggest that DP5 alone produces the large gains.

**R1.5 (minor)** — Ethics: online experimentation on users raises consent and privacy issues (the testbed even contains a privacy feature). A short paragraph is expected in IJIM.

---

## Reviewer 2 — Methods, simulation and statistics

**Summary.** Carefully built testbed, unusually transparent validation, sound paired analysis. Several robustness questions remain. Recommendation: **minor-to-major revision**.

**R2.1 (major) — Ground truth is the model.** The analytic model is the ground truth, and the emulator shows a model error of s.d. 0.044 in the stable region and large errors near capacity. Do the conclusions survive if the true utilities differ from the modelled ones by an error of that size?

**R2.2 (major) — Tuning constants.** The ledger uses κ = 1 in its ship rule, three leaders and a rotating re-test. How sensitive are the results to κ? Was κ chosen on the evaluation instances?

**R2.3 (minor)** — Report how the number of runs was chosen (precision of the main contrasts).

**R2.4 (minor)** — Tests are independent draws; real experiments share common shocks (day of week, campaigns). Discuss the direction of the bias this omission introduces.

**R2.5 (minor)** — The partial η² in Table 6 for the reference instance uses runs as units, for the families instances; say so in the text, not only in the caption.

---

## Reviewer 3 — Practice and generative AI

**Summary.** Relevant and timely, with clear managerial recommendations. The GenAI part is abstract. Recommendation: **minor revision**.

**R3.1 (major) — How would a firm know its screening validity ρ?** The central GenAI result hinges on ρ, which practitioners cannot observe directly. Please explain how ρ can be estimated in practice.

**R3.2 (minor)** — Building a variant has an engineering cost that is not modelled; discuss how this would affect the allocation result (E4).

**R3.3 (minor)** — The literature on LLM idea homogenisation and on LLM self-evaluation has grown quickly; please engage with it beyond Doshi and Hauser (2024).

**R3.4 (minor)** — Recommendation 3 ("many small tests") should carry the caveat that test size is bounded below by metric stability and sample-ratio checks.
