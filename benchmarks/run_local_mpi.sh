#!/usr/bin/env bash
set -euo pipefail
OUTDIR=${1:-results/local_mpi}
mkdir -p "$OUTDIR"
mpirun -np "${NP:-2}" python -m hpcq.mpi_bench --iterations 20 --payload-bytes 4096 --output "$OUTDIR/mpi_microbench.json"
