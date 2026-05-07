#!/usr/bin/env bash
set -euo pipefail

IMAGE=${1:-hpcq-gpu.sif}
OUTDIR=${2:-results/local_apptainer}
mkdir -p "$OUTDIR"

apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
  python3 -m hpcq.run_suite \
  --output-dir "$OUTDIR" \
  --device auto \
  --matrix-size 2048 \
  --qiskit-qubits 18 \
  --qiskit-depth 6
