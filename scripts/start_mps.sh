#!/usr/bin/env bash
set -euo pipefail
PIPE_DIR=${CUDA_MPS_PIPE_DIRECTORY:-/tmp/nvidia-mps}
LOG_DIR=${CUDA_MPS_LOG_DIRECTORY:-/tmp/nvidia-log}
mkdir -p "$PIPE_DIR" "$LOG_DIR"
export CUDA_MPS_PIPE_DIRECTORY="$PIPE_DIR"
export CUDA_MPS_LOG_DIRECTORY="$LOG_DIR"
nvidia-cuda-mps-control -d
echo "MPS started. CUDA_MPS_PIPE_DIRECTORY=$PIPE_DIR CUDA_MPS_LOG_DIRECTORY=$LOG_DIR"
