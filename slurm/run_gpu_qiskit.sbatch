#!/bin/bash
#SBATCH --job-name=hpcq_gpu_qiskit
#SBATCH --output=results/hpcq_gpu_qiskit_%j.out
#SBATCH --error=results/hpcq_gpu_qiskit_%j.err
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00

set -euo pipefail

IMAGE=${IMAGE:-hpcq-gpu.sif}
WORKDIR=${WORKDIR:-$PWD}
OUTDIR=${OUTDIR:-results}
mkdir -p "$OUTDIR"

echo "Job ID: ${SLURM_JOB_ID:-local}"
echo "Node: $(hostname)"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-not_set}"
echo "Image: $IMAGE"
echo "Workdir: $WORKDIR"

apptainer exec --nv --bind "$WORKDIR":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.run_suite \
    --output-dir "$OUTDIR" \
    --device gpu \
    --matrix-size 2048 \
    --qiskit-qubits 18 \
    --qiskit-depth 6
