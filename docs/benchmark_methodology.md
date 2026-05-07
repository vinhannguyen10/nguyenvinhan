# Benchmark Methodology

## 1. Benchmark principles

The benchmark should answer three questions:

1. Does the container see the allocated GPU?
2. Does the workload run correctly inside the container?
3. How much overhead does the container introduce compared with bare metal?

## 2. Metrics

| Metric | Meaning |
|---|---|
| Runtime seconds | Total wall-clock runtime of the workload |
| Seconds per iteration | Average runtime for repeated AI matrix multiplication |
| Approx TFLOPS | Rough compute throughput for matrix multiplication |
| GPU name | Whether the expected GPU is visible |
| Max GPU memory | Memory pressure of benchmark |
| Qiskit count states | Sanity check that quantum simulation returns counts |
| Slurm job log | Proof of scheduler integration |

## 3. Recommended experiments

### Experiment A: GPU visibility

```bash
python -m hpcq.gpu_check --output results/gpu_check.json
```

Purpose: verify `nvidia-smi` and PyTorch CUDA visibility.

### Experiment B: PyTorch AI workload

```bash
python -m hpcq.torch_bench --device cuda --size 4096 --iterations 10 --output results/torch_matmul.json
```

Purpose: measure a simple GPU compute workload.

### Experiment C: Qiskit quantum simulation

```bash
python -m hpcq.qiskit_bench --device gpu --n-qubits 20 --depth 8 --shots 1024 --output results/qiskit_aer.json
```

Purpose: show a quantum circuit simulation inside the container.

### Experiment D: Slurm integration

```bash
sbatch slurm/run_gpu_qiskit.sbatch
```

Purpose: prove scheduler integration.

### Experiment E: MPI integration

```bash
sbatch slurm/run_mpi_apptainer.sbatch
```

Purpose: show basic MPI execution inside the container.

## 4. Fair comparison rule

For bare metal vs container comparison:

- Use the same GPU.
- Use the same number of CPU cores.
- Use the same number of qubits and shots.
- Use the same matrix size and iterations.
- Run each experiment at least 3 times.
- Report mean and standard deviation.

## 5. Suggested result table

| Runtime | Workload | Mean runtime | Std | GPU memory | Notes |
|---|---|---:|---:|---:|---|
| Bare metal | PyTorch matmul | | | | |
| Apptainer | PyTorch matmul | | | | |
| Docker | PyTorch matmul | | | | optional |
| Bare metal | Qiskit GPU | | | | |
| Apptainer | Qiskit GPU | | | | |

## 6. Interpreting results

A good result is not necessarily zero overhead. A good result is:

- GPU is correctly isolated and visible.
- Slurm allocation is respected.
- Runtime is close to bare metal.
- Environment is easier to reproduce.
- The image can be rebuilt from the definition file.
