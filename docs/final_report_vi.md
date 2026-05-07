# Báo cáo kỹ thuật: Container cho HPC hỗ trợ GPU và Quantum hybrid

## 1. Mục tiêu

Mục tiêu của project là xây dựng một workflow container ưu tiên Apptainer/Singularity cho hệ thống HPC có GPU, có thể chạy được workload AI, MPI/NCCL và quantum/hybrid classical-quantum. Docker/Podman và Kubernetes được dùng làm nhánh so sánh, không phải runtime chính trong môi trường HPC multi-user.

## 2. Kiến trúc đề xuất

Luồng chính của hệ thống là:

```text
User -> Slurm sbatch/srun -> Apptainer container --nv -> CUDA/cuDNN/PyTorch/MPI/Quantum SDK -> benchmark JSON/CSV
```

Trong kiến trúc này, Slurm chịu trách nhiệm cấp phát CPU/RAM/GPU và quản lý job. Apptainer chịu trách nhiệm đóng gói môi trường phần mềm và bind GPU/library từ host vào container. Các workload chạy bên trong container gồm PyTorch AI training, MPI microbenchmark, NCCL all-reduce và quantum simulation.

## 3. Các thành phần đã triển khai

| Thành phần | File chính | Vai trò |
|---|---|---|
| GPU evidence | `scripts/collect_gpu_evidence.sh` | Chứng minh host/container nhìn thấy GPU và chạy CUDA/PyTorch |
| Slurm evidence | `slurm/*.sbatch` | Chạy benchmark qua scheduler HPC |
| AI workload | `src/hpcq/ai_train_bench.py` | Train CNN nhỏ trên synthetic data, đo samples/s |
| MPI workload | `src/hpcq/mpi_bench.py` | Đo ping-pong latency và allreduce |
| NCCL workload | `src/hpcq/nccl_bench.py` | Đo all-reduce multi-GPU bằng torch.distributed NCCL |
| Quantum suite | `src/hpcq/quantum_suite.py` | Chạy Qiskit, Cirq, VQE, QAOA, tùy chọn CUDA-Q |
| Energy | `src/hpcq/energy.py` | Lấy power draw từ `nvidia-smi` và ước lượng Wh |
| SBOM/security | `scripts/generate_sbom.sh`, `scripts/security_scan.sh` | Tạo SBOM và scan CVE nếu có Syft/Trivy/Grype |
| Kubernetes comparison | `k8s/*.yaml` | Minh họa cách chạy GPU container trên Kubernetes |
| MIG/MPS | `scripts/mig_report.sh`, `slurm/run_mps_two_tasks.sbatch` | Ghi nhận khả năng chia sẻ/phân vùng GPU |

## 4. Kế hoạch benchmark

Các runtime cần so sánh gồm bare-metal CPU, bare-metal GPU, Apptainer GPU, Docker GPU và Podman GPU nếu host hỗ trợ. Các workload gồm PyTorch matrix multiplication, AI mini training, MPI latency/bandwidth, NCCL all-reduce, quantum simulation và energy/Wh.

Bảng kết quả cuối cùng được sinh bởi:

```bash
bash benchmarks/run_comparison_matrix.sh results/comparison
```

Kết quả cần đưa vào báo cáo:

| Workload | Bare metal | Apptainer | Docker/Podman | Overhead | Ghi chú |
|---|---:|---:|---:|---:|---|
| PyTorch matmul | điền từ CSV | điền từ CSV | điền từ CSV | điền từ CSV | GPU |
| AI train | điền từ CSV | điền từ CSV | điền từ CSV | điền từ CSV | samples/s |
| MPI ping-pong | điền từ JSON | điền từ JSON | nếu có | điền từ CSV | 1-2 nodes |
| NCCL all-reduce | điền từ JSON | điền từ JSON | nếu có | điền từ CSV | multi-GPU |
| Quantum suite | điền từ CSV | điền từ CSV | nếu có | điền từ CSV | Qiskit/Cirq/VQE/QAOA |
| Energy | điền từ JSON | điền từ JSON | nếu có | điền từ CSV | Wh |

## 5. Cách kết luận an toàn

Nếu đã chạy thành công trên GPU/Slurm, có thể kết luận:

> Project đã triển khai được một workflow container HPC dựa trên Apptainer, chạy được GPU thông qua `--nv`, tích hợp được với Slurm bằng `sbatch/srun`, hỗ trợ workload AI bằng PyTorch, workload MPI/NCCL và workload quantum/hybrid thông qua Qiskit/Cirq/PennyLane/CUDA-Q tùy chọn. Kết quả được lưu dạng JSON/CSV/Markdown để phục vụ tái lập và phân tích.

Nếu chưa có InfiniBand, MIG, Kubernetes hoặc CUDA-Q thật, không nên nói là đã hoàn thành thực nghiệm. Hãy viết:

> Các thành phần InfiniBand/RDMA, MIG, Kubernetes GPU Operator hoặc cloud QPU được cung cấp ở mức script/tài liệu và cần được kiểm chứng thêm trên hạ tầng có phần cứng/dịch vụ tương ứng.

## 6. Checklist nghiệm thu

Xem `docs/acceptance_checklist.md` và chỉ đánh dấu Pass cho những mục có log thật trong `results/`.
