#!/bin/bash
#SBATCH --job-name=hpcq_mpi_container
#SBATCH --output=results/hpcq_mpi_%j.out
#SBATCH --error=results/hpcq_mpi_%j.err
#SBATCH --partition=compute
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00

set -euo pipefail

IMAGE=${IMAGE:-hpcq-gpu.sif}
WORKDIR=${WORKDIR:-$PWD}
OUTDIR=${OUTDIR:-results}
mkdir -p "$OUTDIR"

echo "Job ID: ${SLURM_JOB_ID:-local}"
echo "Nodes: ${SLURM_JOB_NODELIST:-unknown}"
echo "Tasks: ${SLURM_NTASKS:-unknown}"

srun apptainer exec --bind "$WORKDIR":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.mpi_hello --output "$OUTDIR/mpi_hello.json"
