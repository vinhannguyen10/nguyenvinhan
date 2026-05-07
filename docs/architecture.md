# Architecture Document

## 1. Target architecture

```text
User / researcher
    |
    | sbatch / srun
    v
Slurm scheduler
    |
    | allocates CPU, memory, GPU, node
    v
GPU compute node
    |
    | apptainer exec --nv
    v
Apptainer SIF image
    |
    | CUDA + Python + MPI + quantum SDK
    v
Workloads
    |-- PyTorch matrix benchmark
    |-- Qiskit Aer quantum simulation
    |-- PennyLane Lightning GPU benchmark
    |-- MPI hello / MPI benchmark placeholder
```

## 2. Why Apptainer is the main runtime

Apptainer is selected as the primary path because it fits a multi-user HPC model better than a privileged Docker daemon. In most HPC clusters, users submit jobs through Slurm and run applications without root privileges. Apptainer also produces a single `.sif` image, which is convenient for reproducibility and file movement.

## 3. Why Docker is still included

Docker is useful for local development, CI, and comparison. However, Docker requires the NVIDIA Container Toolkit for GPU access and is often not the preferred runtime on shared HPC clusters.

## 4. GPU model

The host provides:

- NVIDIA kernel driver
- physical GPU devices
- Slurm GPU allocation

The container provides:

- CUDA user-space runtime/libraries
- Python packages
- benchmark scripts

At runtime, `apptainer exec --nv` exposes the required NVIDIA devices and driver libraries to the container.

## 5. Quantum/hybrid model

The thesis does not require building a real quantum computer. The implementation packages quantum software and runs quantum circuit simulation. The practical workflow is:

```text
Classical host CPU/GPU
    -> quantum circuit code
    -> simulator backend
    -> GPU-accelerated statevector or tensor simulation
    -> benchmark output
```

## 6. Evaluation design

The same workload should be executed under several conditions:

1. Bare metal Python environment.
2. Apptainer container.
3. Docker container, optional.
4. Slurm-submitted Apptainer job.

The report compares correctness, runtime, GPU visibility, GPU memory, and operational complexity.
