# HPC GPU Quantum Container Reference Project

This repository is an expanded implementation for the thesis topic:

> Research of container solutions for HPC systems supporting GPU and Quantum (hybrid classical-quantum)

The main implementation path is:

```text
Slurm scheduler
  -> Apptainer/Singularity container
    -> CUDA/cuDNN + PyTorch + Qiskit/PennyLane/CUDA-Q + MPI/NCCL
      -> benchmark JSON/JSONL + summary tables + SBOM/security outputs
```

Docker/Podman and Kubernetes files are included as comparison paths. They are not the primary HPC runtime.

---

## 1. What is now covered

| Thesis requirement | Implementation in this repo |
|---|---|
| Apptainer vs Docker/Podman architecture | `containers/`, `scripts/run_docker_gpu.sh`, `scripts/run_podman_gpu.sh`, docs |
| GPU support | `hpcq.gpu_check`, `hpcq.torch_bench`, CUDA Docker/Apptainer images |
| NCCL/multi-GPU | `hpcq.nccl_bench`, `slurm/run_nccl_torchrun.sbatch` |
| MPI/high-performance networking | `hpcq.mpi_bench`, `slurm/run_mpi_bench.sbatch`, RDMA diagnostics |
| Slurm integration | multiple `slurm/*.sbatch` scripts |
| Kubernetes comparison | `k8s/gpu-quantum-job.yaml`, RDMA SR-IOV example |
| Quantum/hybrid workflows | Qiskit, PennyLane, CUDA-Q optional, `hpcq.hybrid_vqe` |
| Reproducibility | JSON/JSONL results, summary CSV/MD, lock example |
| SBOM/security scanning | `scripts/generate_sbom.sh`, `scripts/security_scan.sh` |
| MIG/MPS study | `scripts/mig_report.sh`, `scripts/start_mps.sh`, `slurm/run_mps_two_tasks.sbatch` |
| Energy/Wh | `hpcq.energy` using `nvidia-smi` power samples |

---

## 2. Repository structure

```text
containers/     Dockerfile and Apptainer definition files
src/hpcq/       Python benchmark and diagnostics package
tests/          Pytest suite that works without real GPU/Slurm
slurm/          sbatch scripts for GPU, MPI, NCCL, CUDA-Q, MPS
benchmarks/     Local benchmark launchers
scripts/        Host checks, SBOM, security scan, Docker/Podman/MIG/MPS helpers
k8s/            Kubernetes comparison manifests
docs/           Architecture, gap analysis, Vietnamese report outline, MPI/RDMA notes
results/        Default output folder
```

---

## 3. Local CPU validation

Run this first, even without GPU:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-cpu.txt
python -m pip install -e .
python -m pytest
python -m hpcq.run_suite --dry-run --output-dir results/dry_run
bash benchmarks/run_full_cpu.sh results/full_cpu
```

Expected result:

```text
pytest passes
results/full_cpu/*.json exists
results/full_cpu/summary.csv exists
```

---

## 4. Build Apptainer image

```bash
apptainer build hpcq-gpu.sif containers/apptainer-gpu-qiskit.def
```

Optional CUDA-Q image:

```bash
apptainer build hpcq-cudaq.sif containers/apptainer-cudaq.def
```

---

## 5. Run GPU suite with Apptainer

```bash
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace hpcq-gpu.sif \
  python3 -m hpcq.run_suite \
    --output-dir results/apptainer_gpu \
    --device auto \
    --matrix-size 2048 \
    --qiskit-qubits 18 \
    --qiskit-depth 6 \
    --include-pennylane \
    --include-energy
```

Summarize results:

```bash
python -m hpcq.compare_results results/apptainer_gpu \
  --csv results/apptainer_gpu/summary.csv \
  --md results/apptainer_gpu/summary.md
```

---

## 6. Slurm jobs

GPU full suite:

```bash
sbatch slurm/run_full_suite_gpu.sbatch
```

MPI benchmark:

```bash
sbatch slurm/run_mpi_bench.sbatch
```

NCCL/multi-GPU smoke test:

```bash
sbatch slurm/run_nccl_torchrun.sbatch
```

CUDA-Q optional test:

```bash
IMAGE=hpcq-cudaq.sif sbatch slurm/run_cudaq.sbatch
```

MPS study:

```bash
sbatch slurm/run_mps_two_tasks.sbatch
```

---

## 7. Docker/Podman comparison

Docker GPU path:

```bash
docker build -t hpcq-gpu:dev -f containers/Dockerfile.gpu .
bash scripts/run_docker_gpu.sh hpcq-gpu:dev results/docker_gpu
```

Podman GPU path requires NVIDIA CDI configuration on the host:

```bash
bash scripts/run_podman_gpu.sh hpcq-gpu:dev results/podman_gpu
```

---

## 8. Host diagnostics

Before writing the report, capture host information:

```bash
bash scripts/check_host_hpc.sh | tee results/host_check.txt
python -m hpcq.sysinfo --output results/system_report.json
bash scripts/mig_report.sh results/mig_report.txt
```

---

## 9. SBOM and security scan

```bash
bash scripts/generate_sbom.sh . results/sbom
bash scripts/security_scan.sh . results/security
```

The scripts use `syft`, `trivy`, or `grype` if installed. Otherwise they produce clear fallback files so the report can state what was or was not executed.

---

## 10. Safe report claim

A safe claim is:

> The project implements an Apptainer-centered HPC container workflow for GPU-accelerated AI, MPI/NCCL communication, and hybrid quantum simulation workloads. It also provides Docker/Podman and Kubernetes comparison paths, Slurm job scripts, benchmark outputs, energy sampling, SBOM/security scan hooks, and documentation for MIG/MPS/RDMA limitations.

Do not claim real InfiniBand, multi-node NCCL, MIG partitioning, or cloud QPU execution unless you actually run the corresponding scripts on hardware that supports them.

---

## 11. Main commands for grading/demo

```bash
make test
make run-full-cpu
make sbom
make scan
make summarize
```

On a GPU HPC node:

```bash
make build
make run-full-apptainer
sbatch slurm/run_full_suite_gpu.sbatch
```

---

## 12. Added Priority-1 and Priority-2 completion package

This version adds the missing practical components needed to make the project closer to the grading target:

```text
Container runs GPU
Container runs through Slurm
Container supports AI/MPI/Quantum workloads
Benchmark results and documentation are clear
```

### Priority 1 files

| Priority item | Added implementation |
|---|---|
| `collect_gpu_evidence.sh` | `scripts/collect_gpu_evidence.sh` |
| Real Slurm logs | metadata-rich `slurm/*.sbatch` scripts + `scripts/collect_slurm_evidence.sh` |
| Benchmark comparison CSV | `src/hpcq/benchmark_matrix.py`, `benchmarks/run_comparison_matrix.sh` |
| AI mini training benchmark | `src/hpcq/ai_train_bench.py`, `slurm/run_ai_train_gpu.sbatch` |
| MPI latency/bandwidth benchmark | improved `src/hpcq/mpi_bench.py`, `slurm/run_mpi_bench.sbatch`, `scripts/collect_mpi_evidence.sh` |
| Qiskit/Cirq/PennyLane/CUDA-Q suite | `src/hpcq/quantum_suite.py`, `src/hpcq/cirq_bench.py`, `src/hpcq/qaoa_bench.py`, `slurm/run_quantum_suite.sbatch` |
| Vietnamese final report draft | `docs/final_report_vi.md` |

### Priority 2 files

| Priority item | Added implementation |
|---|---|
| NCCL all-reduce benchmark | `src/hpcq/nccl_bench.py`, `slurm/run_nccl_torchrun.sbatch` |
| Energy/Wh benchmark | `src/hpcq/energy.py`, `slurm/run_energy_gpu.sbatch` |
| SBOM + Trivy/Grype output | `scripts/collect_security_evidence.sh`, `scripts/generate_sbom.sh`, `scripts/security_scan.sh` |
| MIG/MPS logs | `scripts/mig_report.sh`, `scripts/start_mps.sh`, `scripts/stop_mps.sh`, `slurm/run_mps_two_tasks.sbatch` |
| Kubernetes GPU job comparison | `k8s/gpu-comparison-job.yaml`, `k8s/nccl-multigpu-job.yaml` |

### Recommended proof-collection command sequence

```bash
# local smoke validation
make validate

# on GPU HPC node
make build
bash scripts/collect_gpu_evidence.sh results/evidence/gpu hpcq-gpu.sif

# Slurm jobs
sbatch slurm/run_full_suite_gpu.sbatch
sbatch slurm/run_ai_train_gpu.sbatch
sbatch slurm/run_mpi_bench.sbatch
sbatch slurm/run_nccl_torchrun.sbatch
sbatch slurm/run_quantum_suite.sbatch
sbatch slurm/run_energy_gpu.sbatch

# comparison and documentation tables
bash benchmarks/run_comparison_matrix.sh results/comparison
bash scripts/collect_security_evidence.sh results/security .
```

See `docs/acceptance_checklist.md` for the exact evidence files to attach to the report.
