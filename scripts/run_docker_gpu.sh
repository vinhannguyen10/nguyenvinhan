#!/usr/bin/env bash
set -euo pipefail
IMAGE=${1:-hpcq-gpu:dev}
OUTDIR=${2:-results/docker_gpu}
mkdir -p "$OUTDIR"
docker run --rm --gpus all -v "$PWD":/workspace -w /workspace "$IMAGE" \
  python3 -m hpcq.run_suite --output-dir "$OUTDIR" --device auto --include-energy
