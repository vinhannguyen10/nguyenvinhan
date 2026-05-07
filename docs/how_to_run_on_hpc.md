# How to run this project on an HPC cluster

## 1. Build images

```bash
module load apptainer
apptainer build hpcq-gpu.sif containers/apptainer-gpu-qiskit.def
apptainer build hpcq-mpi.sif containers/apptainer-hpc-mpi.def
apptainer build hpcq-cudaq.sif containers/apptainer-cudaq.def   # optional
```

## 2. Collect GPU evidence on an allocated GPU node

```bash
salloc --partition=gpu --gres=gpu:1 --cpus-per-task=4 --mem=16G --time=00:30:00
bash scripts/collect_gpu_evidence.sh results/evidence/gpu hpcq-gpu.sif
```

This produces host/container `nvidia-smi`, PyTorch CUDA, AI training, quantum, and energy evidence logs.

## 3. Submit Slurm jobs

```bash
sbatch slurm/run_full_suite_gpu.sbatch
sbatch slurm/run_ai_train_gpu.sbatch
sbatch slurm/run_mpi_bench.sbatch
sbatch slurm/run_nccl_torchrun.sbatch
sbatch slurm/run_quantum_suite.sbatch
sbatch slurm/run_energy_gpu.sbatch
```

After each job finishes, collect accounting information:

```bash
sacct -j <JOBID> --format=JobID,JobName,Partition,AllocCPUS,Elapsed,State,ExitCode,MaxRSS
scontrol show job <JOBID>
```

## 4. Run comparison matrix

For a compact comparison:

```bash
bash benchmarks/run_comparison_matrix.sh results/comparison
```

The output is:

```text
results/comparison/summary.csv
results/comparison/summary.md
```

## 5. Security and reproducibility evidence

```bash
bash scripts/collect_security_evidence.sh results/security .
```

Install `syft`, `trivy`, or `grype` on the host for real SBOM/security outputs. If they are missing, the scripts still write fallback files so the limitation is visible.
