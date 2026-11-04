#!/bin/bash
# Reproduces every experiment; results go to experiments/results/*.json
set -e
cd "$(dirname "$0")"
for e in e1_validation e2_dynamics e3_policies e4_allocation e5_genai e6_bias e7_drift e8_pareto e9_robustness; do
  echo "== $e"; python3 $e.py
done
