#!/bin/bash
#SBATCH --job-name=hpcq_mpi_bench
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=results/slurm_mpi_%j.out
#SBATCH --error=results/slurm_mpi_%j.err

set -u -o pipefail
mkdir -p results/mpi_${SLURM_JOB_ID:-local}
module load apptainer 2>/dev/null || true
IMAGE=${IMAGE:-hpcq-mpi.sif}

print_job_metadata() {
  echo "===== SLURM JOB INFO ====="
  echo "timestamp_utc=$(date -u +%FT%TZ)"
  echo "hostname=$(hostname)"
  echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unset}"
  echo "SLURM_JOB_NAME=${SLURM_JOB_NAME:-unset}"
  echo "SLURM_JOB_NODELIST=${SLURM_JOB_NODELIST:-unset}"
  echo "SLURM_NTASKS=${SLURM_NTASKS:-unset}"
  echo "SLURM_GPUS=${SLURM_GPUS:-unset}"
  echo "SLURM_JOB_GPUS=${SLURM_JOB_GPUS:-unset}"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
  echo "PWD=$PWD"
  module list 2>&1 || true
  nvidia-smi || true
  nvidia-smi topo -m || true
}

print_job_metadata | tee results/mpi_${SLURM_JOB_ID:-local}/slurm_environment.txt
if command -v ibv_devinfo >/dev/null 2>&1; then ibv_devinfo > results/mpi_${SLURM_JOB_ID:-local}/ibv_devinfo.txt 2>&1 || true; fi
if command -v ucx_info >/dev/null 2>&1; then ucx_info -d > results/mpi_${SLURM_JOB_ID:-local}/ucx_devices.txt 2>&1 || true; fi
srun apptainer exec --bind "$PWD":/workspace --pwd /workspace "$IMAGE"   python3 -m hpcq.mpi_bench --iterations ${ITERATIONS:-100} --payload-bytes ${PAYLOAD_BYTES:-1048576}   --output results/mpi_${SLURM_JOB_ID:-local}/mpi_microbench.json
python3 -m hpcq.benchmark_matrix results/mpi_${SLURM_JOB_ID:-local} --csv results/mpi_${SLURM_JOB_ID:-local}/summary.csv --md results/mpi_${SLURM_JOB_ID:-local}/summary.md || true
