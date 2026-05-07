#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Fresh Ubuntu setup for:
# https://github.com/tydeptrai21042004/hpc-container
#
# Tested target:
# - Ubuntu 22.04 / 24.04
#
# What this script installs:
# - Git, Python, venv, build tools
# - OpenMPI + mpi4py
# - Docker Engine
# - NVIDIA Container Toolkit if NVIDIA GPU/driver exists
# - Apptainer
# - Your hpc-container repo
#
# What this script runs:
# - local Python tests
# - local CPU validation
# - Docker CPU container test
# - Docker GPU container test if GPU works
# - Apptainer CPU test
# - Apptainer GPU test if GPU works
# - benchmark summary + evidence logs
# ============================================================

REPO_URL="https://github.com/tydeptrai21042004/hpc-container.git"
PROJECT_DIR="${HOME}/hpc-container"
RESULTS_DIR="${PROJECT_DIR}/results/ubuntu_real_env"

echo "============================================================"
echo "[0] Check Ubuntu"
echo "============================================================"
cat /etc/os-release || true
uname -a

echo
echo "============================================================"
echo "[1] Install base packages"
echo "============================================================"
sudo apt update
sudo apt install -y \
  git curl wget ca-certificates gnupg lsb-release \
  software-properties-common build-essential pkg-config \
  python3 python3-venv python3-pip python3-dev \
  openmpi-bin libopenmpi-dev \
  tree jq zip unzip htop nvtop \
  linux-headers-$(uname -r)

echo
echo "============================================================"
echo "[2] Optional NVIDIA driver check"
echo "============================================================"

HAS_NVIDIA_DRIVER=0

if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  HAS_NVIDIA_DRIVER=1
  echo "NVIDIA driver already works:"
  nvidia-smi
else
  echo "nvidia-smi is not working yet."
  echo
  echo "If this machine has an NVIDIA GPU, install the driver with:"
  echo "  sudo ubuntu-drivers install --gpgpu"
  echo "  sudo reboot"
  echo
  echo "This script will continue with CPU/container setup."
fi

echo
echo "============================================================"
echo "[3] Install Docker Engine"
echo "============================================================"

# Remove conflicting old Docker packages if present.
sudo apt remove -y docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc || true

sudo install -m 0755 -d /etc/apt/keyrings

if [ ! -f /etc/apt/keyrings/docker.asc ]; then
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
fi

sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable --now docker

echo "Testing Docker hello-world..."
sudo docker run --rm hello-world

echo
echo "Adding current user to docker group..."
sudo usermod -aG docker "$USER" || true

echo
echo "============================================================"
echo "[4] Install NVIDIA Container Toolkit if GPU driver works"
echo "============================================================"

if [ "${HAS_NVIDIA_DRIVER}" = "1" ]; then
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null

  sudo apt update
  sudo apt install -y nvidia-container-toolkit

  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker

  echo "Testing official NVIDIA CUDA Docker image..."
  sudo docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
else
  echo "Skipping NVIDIA Container Toolkit because host nvidia-smi is not working."
fi

echo
echo "============================================================"
echo "[5] Install Apptainer"
echo "============================================================"

sudo apt update
sudo apt install -y software-properties-common

# Official Apptainer Ubuntu PPA.
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt update
sudo apt install -y apptainer

apptainer --version
apptainer exec docker://alpine cat /etc/alpine-release

echo
echo "============================================================"
echo "[6] Clone repository"
echo "============================================================"

rm -rf "${PROJECT_DIR}"
git clone "${REPO_URL}" "${PROJECT_DIR}"
cd "${PROJECT_DIR}"

mkdir -p "${RESULTS_DIR}"

echo
echo "Repository structure:"
tree -L 2 .

echo
echo "============================================================"
echo "[7] Create Python environment"
echo "============================================================"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements-cpu.txt
python -m pip install mpi4py cirq pennylane pandas matplotlib
python -m pip install -e .

export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH:-}"

echo
echo "============================================================"
echo "[8] Save host environment report"
echo "============================================================"

{
  echo "date_utc=$(date -u)"
  echo "hostname=$(hostname)"
  echo "user=$(whoami)"
  echo "pwd=$(pwd)"
  echo
  echo "===== OS ====="
  cat /etc/os-release || true
  echo
  echo "===== Kernel ====="
  uname -a || true
  echo
  echo "===== CPU ====="
  lscpu || true
  echo
  echo "===== Memory ====="
  free -h || true
  echo
  echo "===== Docker ====="
  docker --version || sudo docker --version || true
  echo
  echo "===== Apptainer ====="
  apptainer --version || true
  echo
  echo "===== MPI ====="
  mpirun --version || true
  echo
  echo "===== NVIDIA ====="
  nvidia-smi || true
  echo
  echo "===== Python packages ====="
  python - <<'PY'
import importlib.util
mods = ["numpy", "torch", "qiskit", "qiskit_aer", "cirq", "pennylane", "mpi4py", "cudaq"]
for m in mods:
    print(f"{m}: {'OK' if importlib.util.find_spec(m) else 'MISSING'}")
PY
} | tee "${RESULTS_DIR}/host_environment.txt"

echo
echo "============================================================"
echo "[9] Run local tests"
echo "============================================================"

PYTHONPATH=src python -m pytest -q | tee "${RESULTS_DIR}/pytest.log"

echo
echo "============================================================"
echo "[10] Run local CPU validation"
echo "============================================================"

PYTHONPATH=src bash scripts/validate_project.sh | tee "${RESULTS_DIR}/validate_project.log"

echo
echo "============================================================"
echo "[11] Run local CPU full suite"
echo "============================================================"

PYTHONPATH=src python -m hpcq.run_suite \
  --output-dir "${RESULTS_DIR}/baremetal_cpu" \
  --device cpu \
  --matrix-size 512 \
  --qiskit-qubits 8 \
  --qiskit-depth 2 \
  --no-gpu-check \
  --include-ai \
  --include-cirq \
  --include-qaoa \
  --include-pennylane \
  | tee "${RESULTS_DIR}/baremetal_cpu.log" || true

echo
echo "============================================================"
echo "[12] Run local MPI smoke test"
echo "============================================================"

mpirun --oversubscribe -np 2 \
  python -m hpcq.mpi_bench \
    --iterations 50 \
    --payload-bytes 1024 \
    --output "${RESULTS_DIR}/mpi_local_2rank.json" \
  | tee "${RESULTS_DIR}/mpi_local_2rank.log" || true

echo
echo "============================================================"
echo "[13] Build and run Docker CPU container"
echo "============================================================"

sudo docker build -t hpcq-cpu:dev -f containers/Dockerfile.cpu .

sudo docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace \
  hpcq-cpu:dev \
  python3 -m pytest -q \
  | tee "${RESULTS_DIR}/docker_cpu_pytest.log"

sudo docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace \
  hpcq-cpu:dev \
  python3 -m hpcq.run_suite \
    --output-dir results/ubuntu_real_env/docker_cpu \
    --device cpu \
    --matrix-size 512 \
    --qiskit-qubits 8 \
    --qiskit-depth 2 \
    --no-gpu-check \
    --include-ai \
    --include-cirq \
    --include-qaoa \
  | tee "${RESULTS_DIR}/docker_cpu_run_suite.log" || true

echo
echo "============================================================"
echo "[14] Build and run Docker GPU container if GPU works"
echo "============================================================"

HAS_GPU_NOW=0
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
  HAS_GPU_NOW=1
fi

if [ "${HAS_GPU_NOW}" = "1" ]; then
  sudo docker build -t hpcq-gpu:dev -f containers/Dockerfile.gpu .

  sudo docker run --rm --gpus all \
    -v "$PWD":/workspace \
    -w /workspace \
    hpcq-gpu:dev \
    nvidia-smi \
    | tee "${RESULTS_DIR}/docker_gpu_nvidia_smi.log"

  sudo docker run --rm --gpus all \
    -v "$PWD":/workspace \
    -w /workspace \
    hpcq-gpu:dev \
    python3 -m hpcq.run_suite \
      --output-dir results/ubuntu_real_env/docker_gpu \
      --device gpu \
      --matrix-size 1024 \
      --qiskit-qubits 10 \
      --qiskit-depth 3 \
      --include-ai \
      --include-cirq \
      --include-qaoa \
      --include-pennylane \
      --include-energy \
    | tee "${RESULTS_DIR}/docker_gpu_run_suite.log" || true
else
  echo "Skipping Docker GPU test because nvidia-smi is not working." \
    | tee "${RESULTS_DIR}/docker_gpu_skipped.txt"
fi

echo
echo "============================================================"
echo "[15] Build Apptainer image"
echo "============================================================"

# Try to build from your Apptainer definition file.
# If this fails because of permission/user namespace, you can retry manually with --fakeroot.
apptainer build hpcq-gpu.sif containers/apptainer-gpu-qiskit.def \
  | tee "${RESULTS_DIR}/apptainer_build.log" || {
    echo "Normal Apptainer build failed. Trying --fakeroot..."
    apptainer build --fakeroot hpcq-gpu.sif containers/apptainer-gpu-qiskit.def \
      | tee "${RESULTS_DIR}/apptainer_build_fakeroot.log"
  }

ls -lh hpcq-gpu.sif | tee "${RESULTS_DIR}/apptainer_image_ls.txt"

echo
echo "============================================================"
echo "[16] Run Apptainer CPU simulation"
echo "============================================================"

apptainer exec \
  --bind "$PWD":/workspace \
  --pwd /workspace \
  hpcq-gpu.sif \
  python3 -m hpcq.run_suite \
    --output-dir results/ubuntu_real_env/apptainer_cpu \
    --device cpu \
    --matrix-size 512 \
    --qiskit-qubits 8 \
    --qiskit-depth 2 \
    --no-gpu-check \
    --include-ai \
    --include-cirq \
    --include-qaoa \
  | tee "${RESULTS_DIR}/apptainer_cpu_run_suite.log" || true

echo
echo "============================================================"
echo "[17] Run Apptainer GPU if GPU works"
echo "============================================================"

if [ "${HAS_GPU_NOW}" = "1" ]; then
  apptainer exec --nv \
    --bind "$PWD":/workspace \
    --pwd /workspace \
    hpcq-gpu.sif \
    nvidia-smi \
    | tee "${RESULTS_DIR}/apptainer_gpu_nvidia_smi.log"

  apptainer exec --nv \
    --bind "$PWD":/workspace \
    --pwd /workspace \
    hpcq-gpu.sif \
    python3 -m hpcq.run_suite \
      --output-dir results/ubuntu_real_env/apptainer_gpu \
      --device gpu \
      --matrix-size 1024 \
      --qiskit-qubits 10 \
      --qiskit-depth 3 \
      --include-ai \
      --include-cirq \
      --include-qaoa \
      --include-pennylane \
      --include-energy \
    | tee "${RESULTS_DIR}/apptainer_gpu_run_suite.log" || true

  PYTHONPATH=src bash scripts/collect_gpu_evidence.sh \
    "${RESULTS_DIR}/evidence_gpu" \
    hpcq-gpu.sif \
    | tee "${RESULTS_DIR}/collect_gpu_evidence.log" || true
else
  echo "Skipping Apptainer GPU test because nvidia-smi is not working." \
    | tee "${RESULTS_DIR}/apptainer_gpu_skipped.txt"
fi

echo
echo "============================================================"
echo "[18] Generate comparison summary"
echo "============================================================"

COMPARE_INPUTS=(
  "${RESULTS_DIR}/baremetal_cpu"
  "${RESULTS_DIR}/docker_cpu"
  "${RESULTS_DIR}/apptainer_cpu"
)

if [ -d "${RESULTS_DIR}/docker_gpu" ]; then
  COMPARE_INPUTS+=("${RESULTS_DIR}/docker_gpu")
fi

if [ -d "${RESULTS_DIR}/apptainer_gpu" ]; then
  COMPARE_INPUTS+=("${RESULTS_DIR}/apptainer_gpu")
fi

PYTHONPATH=src python -m hpcq.benchmark_matrix \
  "${COMPARE_INPUTS[@]}" \
  --baseline-runtime baremetal_cpu \
  --csv "${RESULTS_DIR}/summary.csv" \
  --md "${RESULTS_DIR}/summary.md" \
  | tee "${RESULTS_DIR}/benchmark_matrix.log" || true

echo
echo "============================================================"
echo "[19] Generate SBOM/security fallback"
echo "============================================================"

bash scripts/generate_sbom.sh . "${RESULTS_DIR}/security/sbom" || true
bash scripts/security_scan.sh . "${RESULTS_DIR}/security/scan" || true

echo
echo "============================================================"
echo "[20] Create final archive"
echo "============================================================"

cd "${PROJECT_DIR}"
zip -qr "${HOME}/hpc_container_ubuntu_real_results.zip" results

echo
echo "============================================================"
echo "DONE"
echo "============================================================"
echo "Project folder:"
echo "  ${PROJECT_DIR}"
echo
echo "Results folder:"
echo "  ${RESULTS_DIR}"
echo
echo "Results zip:"
echo "  ${HOME}/hpc_container_ubuntu_real_results.zip"
echo
echo "If you just installed NVIDIA driver, reboot and rerun this script:"
echo "  sudo reboot"
echo "  cd ${PROJECT_DIR}"
echo "  bash ~/setup_hpc_container_fresh_ubuntu.sh"