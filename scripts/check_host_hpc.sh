#!/usr/bin/env bash
set -euo pipefail

echo "== Host identity =="
hostname || true
uname -a || true

echo "== Container runtimes =="
for cmd in apptainer singularity docker podman enroot ch-run; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "$cmd: $($cmd --version 2>&1 | head -n 1)"
  else
    echo "$cmd: not found"
  fi
done

echo "== Scheduler =="
for cmd in sinfo squeue srun sbatch; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "$cmd: available"
  else
    echo "$cmd: not found"
  fi
done

echo "== NVIDIA GPU =="
nvidia-smi || true

echo "== InfiniBand / RDMA =="
ibv_devinfo -l || true
ucx_info -v || true

echo "== Cgroups =="
stat -fc %T /sys/fs/cgroup || true
cat /proc/1/cgroup || true
