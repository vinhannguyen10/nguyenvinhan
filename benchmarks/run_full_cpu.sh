#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-results/full_cpu}
mkdir -p "$OUTDIR"
python -m hpcq.run_suite \
  --output-dir "$OUTDIR" \
  --device cpu \
  --matrix-size 512 \
  --qiskit-qubits 8 \
  --qiskit-depth 2 \
  --no-gpu-check
python -m hpcq.compare_results "$OUTDIR" --csv "$OUTDIR/summary.csv" --md "$OUTDIR/summary.md"
