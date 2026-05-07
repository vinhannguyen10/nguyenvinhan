#!/usr/bin/env bash
set -euo pipefail
OUT=${1:-results/security}
IMAGE_OR_DIR=${2:-.}
mkdir -p "$OUT"
bash scripts/generate_sbom.sh "$IMAGE_OR_DIR" "$OUT/sbom" || true
bash scripts/security_scan.sh "$IMAGE_OR_DIR" "$OUT/scan" || true
{
  echo "timestamp_utc=$(date -u +%FT%TZ)"
  echo "target=$IMAGE_OR_DIR"
  echo "syft=$(command -v syft || true)"
  echo "trivy=$(command -v trivy || true)"
  echo "grype=$(command -v grype || true)"
} > "$OUT/security_tool_versions.txt"
