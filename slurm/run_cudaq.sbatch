#!/bin/bash
#SBATCH --job-name=hpcq_cudaq
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --output=results/hpcq_cudaq_%j.out
#SBATCH --error=results/hpcq_cudaq_%j.err

set -euo pipefail
mkdir -p results/cudaq_${SLURM_JOB_ID}
module load apptainer 2>/dev/null || true
IMAGE=${IMAGE:-hpcq-cudaq.sif}
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
  python3 -m hpcq.cudaq_bench --shots 1000 --output results/cudaq_${SLURM_JOB_ID}/cudaq_bell.json
