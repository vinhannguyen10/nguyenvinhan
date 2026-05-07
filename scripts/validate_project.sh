#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=${PYTHONPATH:-src}
export PYTHONPATH
python -m pytest
python -m hpcq.run_suite --dry-run --output-dir results/validate_dry_run --include-ai --include-cirq --include-qaoa --include-energy --include-cudaq
python -m hpcq.hybrid_vqe --steps 40 --learning-rate 0.15 --output results/validate_dry_run/vqe.json
python -m hpcq.qaoa_bench --grid-size 8 --output results/validate_dry_run/qaoa.json
python -m hpcq.sysinfo --output results/validate_dry_run/system_report.json
python -m hpcq.benchmark_matrix results/validate_dry_run --baseline-runtime validate_dry_run --csv results/validate_dry_run/summary.csv --md results/validate_dry_run/summary.md
bash scripts/generate_sbom.sh . results/validate_security/sbom || true
bash scripts/security_scan.sh . results/validate_security/scan || true
