#!/usr/bin/env bash
set -euo pipefail
OUT=${1:-results/mig_report.txt}
mkdir -p "$(dirname "$OUT")"
{
  echo "== NVIDIA MIG status =="
  nvidia-smi -L || true
  nvidia-smi -q | grep -A 12 -i "MIG Mode" || true
  echo
  echo "== MIG profiles =="
  nvidia-smi mig -lgip || true
  echo
  echo "== MIG compute instances =="
  nvidia-smi mig -lci || true
} | tee "$OUT"
