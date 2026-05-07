#!/usr/bin/env bash
set -u -o pipefail

OUT=${1:-results/evidence/gpu}
IMAGE=${2:-hpcq-gpu.sif}
PYTHON_BIN=${PYTHON_BIN:-python3}
MATRIX_SIZE=${MATRIX_SIZE:-2048}
QUBITS=${QUBITS:-18}
DEPTH=${DEPTH:-6}

mkdir -p "$OUT"

run_and_capture() {
  local name="$1"
  shift
  echo "===== $name =====" | tee "$OUT/${name}.log"
  "$@" > >(tee -a "$OUT/${name}.log") 2> >(tee -a "$OUT/${name}.log" >&2)
  local rc=$?
  echo "exit_code=$rc" | tee -a "$OUT/${name}.log"
  return 0
}

{
  echo "timestamp_utc=$(date -u +%FT%TZ)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un 2>/dev/null || true)"
  echo "pwd=$PWD"
  echo "image=$IMAGE"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
} | tee "$OUT/metadata.env"

run_and_capture host_nvidia_smi nvidia-smi
run_and_capture host_gpu_topology bash -lc 'nvidia-smi topo -m || true'
run_and_capture host_sysinfo "$PYTHON_BIN" -m hpcq.sysinfo --output "$OUT/host_system_report.json"

if command -v apptainer >/dev/null 2>&1 && [ -f "$IMAGE" ]; then
  run_and_capture apptainer_nvidia_smi apptainer exec --nv "$IMAGE" nvidia-smi
  run_and_capture apptainer_gpu_check apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.gpu_check --output "$OUT/apptainer_gpu_check.json"
  run_and_capture apptainer_torch_gpu apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.torch_bench --device cuda --size "$MATRIX_SIZE" --iterations 5 --output "$OUT/apptainer_torch_matmul_gpu.json"
  run_and_capture apptainer_ai_train apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.ai_train_bench --device cuda --samples 4096 --epochs 2 --output "$OUT/apptainer_ai_tiny_cnn_train.json"
  run_and_capture apptainer_energy apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.energy --seconds 10 --interval 1 --output "$OUT/apptainer_gpu_energy.json"
  run_and_capture apptainer_full_suite apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
    python3 -m hpcq.run_suite --output-dir "$OUT/run_suite_gpu" --device gpu --matrix-size "$MATRIX_SIZE" \
      --qiskit-qubits "$QUBITS" --qiskit-depth "$DEPTH" --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy
else
  echo "Apptainer or image not available. Skipping Apptainer evidence." | tee "$OUT/apptainer_skipped.txt"
fi

if command -v docker >/dev/null 2>&1; then
  DOCKER_IMAGE=${DOCKER_IMAGE:-hpcq-gpu:dev}
  run_and_capture docker_nvidia_smi docker run --rm --gpus all "$DOCKER_IMAGE" nvidia-smi
  run_and_capture docker_gpu_suite docker run --rm --gpus all -v "$PWD":/workspace -w /workspace "$DOCKER_IMAGE" \
    python3 -m hpcq.run_suite --output-dir "$OUT/docker_gpu_suite" --device gpu --matrix-size "$MATRIX_SIZE" \
      --qiskit-qubits "$QUBITS" --qiskit-depth "$DEPTH" --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy
else
  echo "Docker not available. Skipping Docker GPU evidence." | tee "$OUT/docker_skipped.txt"
fi

"$PYTHON_BIN" -m hpcq.benchmark_matrix "$OUT" "$OUT/run_suite_gpu" "$OUT/docker_gpu_suite" \
  --baseline-runtime gpu --csv "$OUT/gpu_evidence_summary.csv" --md "$OUT/gpu_evidence_summary.md" || true

echo "Evidence collection finished. Check: $OUT"
