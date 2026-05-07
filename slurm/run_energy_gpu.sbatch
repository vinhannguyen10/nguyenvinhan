#!/bin/bash
#SBATCH --job-name=hpcq_energy
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=results/slurm_energy_%j.out
#SBATCH --error=results/slurm_energy_%j.err

set -u -o pipefail
mkdir -p results/energy_${SLURM_JOB_ID:-local}
module load apptainer 2>/dev/null || true
IMAGE=${IMAGE:-hpcq-gpu.sif}

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

print_job_metadata | tee results/energy_${SLURM_JOB_ID:-local}/slurm_environment.txt
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE"   python3 -m hpcq.energy --seconds ${SECONDS_TO_SAMPLE:-30} --interval ${INTERVAL:-1} --output results/energy_${SLURM_JOB_ID:-local}/gpu_power_monitor.json
