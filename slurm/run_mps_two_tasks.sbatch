#!/bin/bash
#SBATCH --job-name=hpcq_mps_study
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --ntasks=2
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=results/hpcq_mps_%j.out
#SBATCH --error=results/hpcq_mps_%j.err

set -euo pipefail
mkdir -p results/mps_${SLURM_JOB_ID}
module load apptainer 2>/dev/null || true
IMAGE=${IMAGE:-hpcq-gpu.sif}
export CUDA_MPS_PIPE_DIRECTORY=${CUDA_MPS_PIPE_DIRECTORY:-/tmp/nvidia-mps-${SLURM_JOB_ID}}
export CUDA_MPS_LOG_DIRECTORY=${CUDA_MPS_LOG_DIRECTORY:-/tmp/nvidia-log-${SLURM_JOB_ID}}
mkdir -p "$CUDA_MPS_PIPE_DIRECTORY" "$CUDA_MPS_LOG_DIRECTORY"
nvidia-cuda-mps-control -d || true
srun --ntasks=2 apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
  python3 -m hpcq.torch_bench --device cuda --size 1024 --iterations 20
printf quit | nvidia-cuda-mps-control || true
