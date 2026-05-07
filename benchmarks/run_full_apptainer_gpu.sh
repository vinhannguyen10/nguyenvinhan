#!/usr/bin/env bash
set -euo pipefail
IMAGE=${1:-hpcq-gpu.sif}
OUTDIR=${2:-results/full_apptainer_gpu}
mkdir -p "$OUTDIR"
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
  python3 -m hpcq.run_suite \
    --output-dir "$OUTDIR" \
    --device auto \
    --matrix-size 2048 \
    --qiskit-qubits 18 \
    --qiskit-depth 6 \
    --include-pennylane \
    --include-energy
python -m hpcq.compare_results "$OUTDIR" --csv "$OUTDIR/summary.csv" --md "$OUTDIR/summary.md"
