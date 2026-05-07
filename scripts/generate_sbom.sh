#!/usr/bin/env bash
set -euo pipefail
IMAGE_OR_DIR=${1:-.}
OUT=${2:-results/sbom}
mkdir -p "$OUT"
if command -v syft >/dev/null 2>&1; then
  syft "$IMAGE_OR_DIR" -o spdx-json > "$OUT/sbom.spdx.json"
  echo "Wrote $OUT/sbom.spdx.json with syft"
else
  python -m pip freeze > "$OUT/pip-freeze.txt" || true
  find "$IMAGE_OR_DIR" -maxdepth 3 -type f | sort > "$OUT/file-manifest.txt" || true
  echo "syft not found; wrote pip-freeze and file manifest fallback in $OUT"
fi
