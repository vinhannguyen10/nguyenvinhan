#!/bin/bash
#SBATCH --job-name=hpcq_nccl
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=results/slurm_nccl_%j.out
#SBATCH --error=results/slurm_nccl_%j.err

set -u -o pipefail
mkdir -p results/nccl_${SLURM_JOB_ID:-local}
module load apptainer 2>/dev/null || true
IMAGE=${IMAGE:-hpcq-gpu.sif}
MASTER_PORT=${MASTER_PORT:-29501}
export NCCL_DEBUG=${NCCL_DEBUG:-INFO}
export NCCL_SOCKET_IFNAME=${NCCL_SOCKET_IFNAME:-^lo,docker0}
export NCCL_IB_DISABLE=${NCCL_IB_DISABLE:-0}

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

print_job_metadata | tee results/nccl_${SLURM_JOB_ID:-local}/slurm_environment.txt
srun apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE"   python3 -m torch.distributed.run     --nnodes=1     --nproc_per_node=${SLURM_NTASKS_PER_NODE:-2}     --master_port=${MASTER_PORT}     -m hpcq.nccl_bench     --backend nccl     --elements ${ELEMENTS:-1000000}     --iterations ${ITERATIONS:-20}     --output results/nccl_${SLURM_JOB_ID:-local}/nccl_rank0.json
python3 -m hpcq.benchmark_matrix results/nccl_${SLURM_JOB_ID:-local} --csv results/nccl_${SLURM_JOB_ID:-local}/summary.csv --md results/nccl_${SLURM_JOB_ID:-local}/summary.md || true
