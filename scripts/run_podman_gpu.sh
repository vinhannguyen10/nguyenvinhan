#!/usr/bin/env bash
set -euo pipefail
IMAGE=${1:-hpcq-gpu:dev}
OUTDIR=${2:-results/podman_gpu}
mkdir -p "$OUTDIR"
# Requires host NVIDIA Container Toolkit CDI setup, for example: nvidia-ctk cdi generate.
podman run --rm --device nvidia.com/gpu=all -v "$PWD":/workspace:Z -w /workspace "$IMAGE" \
  python3 -m hpcq.run_suite --output-dir "$OUTDIR" --device auto
