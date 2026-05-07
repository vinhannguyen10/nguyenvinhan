#!/usr/bin/env bash
set -euo pipefail
TARGET=${1:-.}
OUT=${2:-results/security}
mkdir -p "$OUT"
if command -v trivy >/dev/null 2>&1; then
  trivy fs --format json --output "$OUT/trivy-fs.json" "$TARGET" || true
  echo "Wrote $OUT/trivy-fs.json"
elif command -v grype >/dev/null 2>&1; then
  grype "$TARGET" -o json > "$OUT/grype.json" || true
  echo "Wrote $OUT/grype.json"
else
  echo "No trivy/grype installed. Install one scanner for real CVE reporting." | tee "$OUT/SCAN_NOT_RUN.txt"
fi
