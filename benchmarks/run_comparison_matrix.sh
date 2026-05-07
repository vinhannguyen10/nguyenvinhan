#!/usr/bin/env bash
set -u -o pipefail

OUT=${1:-results/comparison}
IMAGE=${IMAGE:-hpcq-gpu.sif}
DOCKER_IMAGE=${DOCKER_IMAGE:-hpcq-gpu:dev}
MATRIX_SIZE=${MATRIX_SIZE:-1024}
QUBITS=${QUBITS:-14}
mkdir -p "$OUT"

run_host_cpu() {
  mkdir -p "$OUT/baremetal_cpu"
  python3 -m hpcq.run_suite --output-dir "$OUT/baremetal_cpu" --device cpu --matrix-size "$MATRIX_SIZE" \
    --qiskit-qubits "$QUBITS" --include-ai --include-cirq --include-qaoa || true
}

run_host_gpu() {
  mkdir -p "$OUT/baremetal_gpu"
  python3 -m hpcq.run_suite --output-dir "$OUT/baremetal_gpu" --device gpu --matrix-size "$MATRIX_SIZE" \
    --qiskit-qubits "$QUBITS" --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy || true
}

run_apptainer_gpu() {
  mkdir -p "$OUT/apptainer_gpu"
  if command -v apptainer >/dev/null 2>&1 && [ -f "$IMAGE" ]; then
    apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace "$IMAGE" \
      python3 -m hpcq.run_suite --output-dir "$OUT/apptainer_gpu" --device gpu --matrix-size "$MATRIX_SIZE" \
        --qiskit-qubits "$QUBITS" --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy || true
  else
    echo '{"name":"apptainer_gpu_skipped","ok":false,"error":"apptainer or image unavailable"}' > "$OUT/apptainer_gpu/skipped.json"
  fi
}

run_docker_gpu() {
  mkdir -p "$OUT/docker_gpu"
  if command -v docker >/dev/null 2>&1; then
    docker run --rm --gpus all -v "$PWD":/workspace -w /workspace "$DOCKER_IMAGE" \
      python3 -m hpcq.run_suite --output-dir "$OUT/docker_gpu" --device gpu --matrix-size "$MATRIX_SIZE" \
        --qiskit-qubits "$QUBITS" --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy || true
  else
    echo '{"name":"docker_gpu_skipped","ok":false,"error":"docker unavailable"}' > "$OUT/docker_gpu/skipped.json"
  fi
}

run_podman_gpu() {
  mkdir -p "$OUT/podman_gpu"
  if command -v podman >/dev/null 2>&1; then
    bash scripts/run_podman_gpu.sh "$DOCKER_IMAGE" "$OUT/podman_gpu" || true
  else
    echo '{"name":"podman_gpu_skipped","ok":false,"error":"podman unavailable"}' > "$OUT/podman_gpu/skipped.json"
  fi
}

run_host_cpu
run_host_gpu
run_apptainer_gpu
run_docker_gpu
run_podman_gpu

python3 -m hpcq.benchmark_matrix "$OUT/baremetal_cpu" "$OUT/baremetal_gpu" "$OUT/apptainer_gpu" "$OUT/docker_gpu" "$OUT/podman_gpu" \
  --baseline-runtime baremetal_cpu --csv "$OUT/summary.csv" --md "$OUT/summary.md" || true

echo "Comparison matrix complete: $OUT"
