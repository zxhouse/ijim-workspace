# Managing evidence, not ideas — IJIM manuscript and LoopLab testbed

Manuscript for the *International Journal of Information Management*:
**"Managing evidence, not ideas: A convergence-based design of experimentation information systems for digital services in the age of generative AI"**
— Paweł Kuraś (Kozminski University), Ewelina Nycz and Patryk Organiściak (Rzeszów University of Technology).

It builds on the preprint in `preprint/` (Kuraś et al., 2026, arXiv:2611.03034).

## Contents

| Path | What |
|---|---|
| `paper/manuscript.tex`, `.pdf` | full manuscript with authors (`\anonfalse`) |
| `paper/manuscript_anonymised.tex`, `.pdf` | blind version (`\anontrue`; self-citation and repository link withheld) |
| `paper/Title_page.docx`, `Highlights.docx`, `highlights.txt` | submission files |
| `paper/tikz/` | sources of the schematic figures (device icons in `icons.tex`) |
| `paper/figures/` | all figures as vector PDF |
| `testbed/looplab/` | the programmable testbed: `params.py` (service, 12 capabilities), `landscape.py` (queueing model, exact utilities, test sampler), `des.py` (SimPy discrete-event emulation of the topology), `policies.py` (loop, evidence ledger, A/B champion–challenger, launch-and-learn, Thompson, random, Pareto archive) |
| `experiments/e1_…e9_*.py` | the nine experiments |
| `experiments/e10_robustness_review.py`, `e11_audit.py`, `e11b_audit.py` | review-round and audit experiments (stronger baselines, κ, misspecified truth; design-principle decomposition, noise, production start, build rate) |
| `experiments/e13_llm_ideation.py` | language model as generator and screen (needs `ANTHROPIC_API_KEY`; not run in the paper) |
| `paper/review/` | internal reviews, response letter, audit report |
| `experiments/analyze.py` | figures and `results/numbers.json` (every number quoted in the paper) |
| `experiments/results/*.json` | raw outputs |

## Reproduce

```bash
pip install numpy scipy simpy matplotlib
cd experiments
./run_all.sh            # ~35 min on 4 cores
python3 analyze.py      # figures -> paper/figures, numbers -> results/numbers.json
cd ../paper/tikz && for f in fig_*.tex; do pdflatex $f; done && cp fig_*.pdf ../figures/
cd .. && pdflatex manuscript && pdflatex manuscript
```

All runs use fixed seeds.
