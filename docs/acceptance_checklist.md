# Acceptance checklist for GPU + Slurm + AI/MPI/Quantum container thesis

Use this table as the grading/demo checklist. Do not mark a row as passed until the evidence file exists and contains a successful exit code or valid benchmark JSON.

| Requirement | Command/script | Evidence file | Pass condition |
|---|---|---|---|
| Host GPU visible | `nvidia-smi` | `results/evidence/gpu/host_nvidia_smi.log` | GPU name, driver, CUDA version printed |
| GPU visible inside Apptainer | `bash scripts/collect_gpu_evidence.sh` | `results/evidence/gpu/apptainer_nvidia_smi.log` | `nvidia-smi` works inside container |
| PyTorch CUDA works | `hpcq.gpu_check` | `results/evidence/gpu/apptainer_gpu_check.json` | `ok=true`, `cuda_available=true` |
| AI workload works | `hpcq.ai_train_bench` | `results/evidence/gpu/apptainer_ai_tiny_cnn_train.json` | `ok=true`, `samples_per_second` exists |
| Slurm GPU job works | `sbatch slurm/run_full_suite_gpu.sbatch` | `results/full_gpu_<JOBID>/summary.csv` | job state COMPLETED and summary exists |
| MPI workload works | `sbatch slurm/run_mpi_bench.sbatch` | `results/mpi_<JOBID>/mpi_microbench.json` | `world_size>=2`, ping-pong/allreduce metrics exist |
| NCCL all-reduce works | `sbatch slurm/run_nccl_torchrun.sbatch` | `results/nccl_<JOBID>/nccl_rank0.json` | `backend=nccl`, `world_size>=2` |
| Quantum suite works | `sbatch slurm/run_quantum_suite.sbatch` | `results/quantum_<JOBID>/quantum_suite.jsonl` | Qiskit/Cirq/VQE/QAOA results generated |
| CUDA-Q optional path works | `sbatch slurm/run_cudaq.sbatch` | `results/cudaq_<JOBID>/cudaq_bell.json` | `ok=true` only if CUDA-Q image is available |
| Energy/Wh measured | `sbatch slurm/run_energy_gpu.sbatch` | `results/energy_<JOBID>/gpu_power_monitor.json` | `estimated_energy_wh` exists |
| SBOM generated | `make sbom` | `results/sbom/` | Syft output or fallback manifest exists |
| Security scan generated | `make scan` | `results/security/` | Trivy/Grype output or fallback note exists |
| MIG report collected | `bash scripts/mig_report.sh` | `results/mig_report.txt` | MIG mode printed or limitation recorded |
| MPS study runs | `sbatch slurm/run_mps_two_tasks.sbatch` | `results/mps_<JOBID>/` and Slurm output | two CUDA tasks run under MPS control |
| Kubernetes comparison | `kubectl apply -f k8s/gpu-comparison-job.yaml` | Kubernetes job logs | job requests `nvidia.com/gpu: 1` and produces results |

## Safe rule for the report

Only claim the rows that are actually passed on your hardware. If a row is skipped because the cluster lacks InfiniBand, MIG, Kubernetes, or CUDA-Q, write it clearly as a limitation rather than as a completed experiment.
