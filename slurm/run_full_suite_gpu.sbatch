#!/bin/bash
#SBATCH --job-name=hpcq_full_gpu
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=results/slurm_full_gpu_%j.out
#SBATCH --error=results/slurm_full_gpu_%j.err

set -u -o pipefail
mkdir -p results/full_gpu_${SLURM_JOB_ID:-local}
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

print_job_metadata | tee results/full_gpu_${SLURM_JOB_ID:-local}/slurm_environment.txt
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" nvidia-smi | tee results/full_gpu_${SLURM_JOB_ID:-local}/container_nvidia_smi.txt || true
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE"   python3 -m hpcq.run_suite     --output-dir results/full_gpu_${SLURM_JOB_ID:-local}     --device gpu     --matrix-size ${MATRIX_SIZE:-2048}     --qiskit-qubits ${QISKIT_QUBITS:-18}     --qiskit-depth ${QISKIT_DEPTH:-6}     --include-ai     --include-cirq     --include-qaoa     --include-pennylane     --include-energy
python3 -m hpcq.benchmark_matrix results/full_gpu_${SLURM_JOB_ID:-local}   --baseline-runtime full_gpu_${SLURM_JOB_ID:-local}   --csv results/full_gpu_${SLURM_JOB_ID:-local}/summary.csv   --md results/full_gpu_${SLURM_JOB_ID:-local}/summary.md || true
sacct -j ${SLURM_JOB_ID:-0} --format=JobID,JobName,Partition,AllocCPUS,Elapsed,State,ExitCode,MaxRSS > results/full_gpu_${SLURM_JOB_ID:-local}/sacct.txt 2>&1 || true
