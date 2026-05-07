#!/usr/bin/env bash
set -euo pipefail

python -m hpcq.run_suite \
  --output-dir results/local_cpu \
  --device cpu \
  --matrix-size 512 \
  --qiskit-qubits 8 \
  --qiskit-depth 2
