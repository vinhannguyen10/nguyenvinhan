#!/usr/bin/env bash
set -u -o pipefail

OUT=${1:-results/evidence/mpi}
IMAGE=${2:-hpcq-mpi.sif}
mkdir -p "$OUT"

{
  echo "timestamp_utc=$(date -u +%FT%TZ)"
  echo "hostname=$(hostname)"
  echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
  echo "SLURM_NTASKS=${SLURM_NTASKS:-unset}"
  echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST:-unset}"
  command -v mpirun || true
  command -v srun || true
  command -v apptainer || true
} | tee "$OUT/mpi_environment.txt"

python3 -m hpcq.mpi_bench --iterations 10 --payload-bytes 1024 --output "$OUT/host_mpi_single.json" || true

if command -v mpirun >/dev/null 2>&1; then
  mpirun -np 2 python3 -m hpcq.mpi_bench --iterations 100 --payload-bytes 1048576 --output "$OUT/host_mpi_2rank.json" | tee "$OUT/host_mpi_2rank.log" || true
fi

if command -v apptainer >/dev/null 2>&1 && [ -f "$IMAGE" ]; then
  if command -v mpirun >/dev/null 2>&1; then
    mpirun -np 2 apptainer exec --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
      python3 -m hpcq.mpi_bench --iterations 100 --payload-bytes 1048576 --output "$OUT/apptainer_mpi_2rank.json" \
      | tee "$OUT/apptainer_mpi_2rank.log" || true
  fi
else
  echo "apptainer or image unavailable" > "$OUT/apptainer_mpi_skipped.txt"
fi

if command -v ibv_devinfo >/dev/null 2>&1; then ibv_devinfo > "$OUT/ibv_devinfo.txt" 2>&1 || true; fi
if command -v ucx_info >/dev/null 2>&1; then ucx_info -d > "$OUT/ucx_devices.txt" 2>&1 || true; fi
python3 -m hpcq.benchmark_matrix "$OUT" --baseline-runtime mpi --csv "$OUT/mpi_summary.csv" --md "$OUT/mpi_summary.md" || true
