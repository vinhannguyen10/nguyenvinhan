# Tài liệu chi tiết: Container cho HPC hỗ trợ GPU và Quantum

## 1. Mục tiêu của phần triển khai

Mục tiêu của phần code không phải là tự viết một container runtime mới như Docker hay Apptainer. Mục tiêu thực tế là xây dựng một quy trình hoàn chỉnh để:

1. Đóng gói môi trường chạy workload HPC/AI/Quantum vào container.
2. Cho container truy cập GPU NVIDIA.
3. Chạy workload qua Slurm scheduler.
4. Đo hiệu năng và so sánh với môi trường bare-metal.
5. Tạo tài liệu để người khác có thể tái lập kết quả.

Hướng chính của repo là:

```text
Slurm + Apptainer + CUDA + PyTorch + Qiskit/PennyLane + MPI
```

Docker được dùng như hướng phụ để phát triển local và so sánh.

---

## 2. Vai trò của từng thư mục

| Thư mục | Ý nghĩa |
|---|---|
| `containers/` | Chứa công thức build container: Apptainer `.def` và Dockerfile |
| `src/hpcq/` | Chứa code kiểm tra GPU, benchmark AI, benchmark quantum, MPI |
| `tests/` | Chứa test case bằng pytest |
| `slurm/` | Chứa script submit job lên Slurm |
| `benchmarks/` | Chứa script chạy benchmark local/container |
| `docs/` | Chứa tài liệu kiến trúc và phương pháp đánh giá |
| `results/` | Nơi lưu kết quả JSON/JSONL |

---

## 3. Luồng chạy chính

Luồng triển khai đầy đủ:

```text
Bước 1: Cài dependencies CPU để test code
Bước 2: Chạy pytest
Bước 3: Build Apptainer image
Bước 4: Chạy kiểm tra GPU trong container
Bước 5: Chạy benchmark AI và quantum
Bước 6: Submit bằng Slurm
Bước 7: Thu thập kết quả để viết báo cáo
```

---

## 4. Giải thích các file code chính

### 4.1 `gpu_check.py`

File này kiểm tra container có nhìn thấy GPU hay không. Nó kiểm tra bằng hai cách:

1. Gọi lệnh `nvidia-smi`.
2. Import PyTorch và kiểm tra `torch.cuda.is_available()`.

Nếu một trong hai cách thành công, có thể xem như GPU đã được expose vào container.

### 4.2 `torch_bench.py`

File này chạy phép nhân ma trận bằng PyTorch. Đây là workload AI đơn giản nhưng hữu ích để kiểm tra:

- GPU có chạy tính toán thật không.
- Runtime là bao nhiêu.
- Memory GPU được cấp phát bao nhiêu.
- Throughput xấp xỉ tính theo TFLOPS.

### 4.3 `qiskit_bench.py`

File này tạo một quantum circuit gồm các cổng Hadamard, RX, RZ và CNOT. Sau đó nó chạy circuit bằng Qiskit Aer simulator. Nếu chọn `--device gpu`, backend sẽ cố gắng dùng GPU.

Mục tiêu là chứng minh container không chỉ chạy AI workload mà còn chạy được quantum simulation workload.

### 4.4 `pennylane_bench.py`

File này là benchmark phụ cho PennyLane. Nếu môi trường có `lightning.gpu`, nó dùng simulator GPU. Nếu không, có thể chạy bằng CPU để kiểm tra logic.

### 4.5 `mpi_hello.py`

File này kiểm tra MPI cơ bản bằng `mpi4py`. Trong đề tài HPC, MPI rất quan trọng vì nhiều mô phỏng khoa học chạy đa tiến trình hoặc đa node.

### 4.6 `run_suite.py`

File này gom nhiều benchmark lại thành một lệnh duy nhất. Nó chạy:

1. GPU check.
2. PyTorch benchmark.
3. Qiskit benchmark.

Kết quả được ghi ra file JSON trong thư mục `results/`.

---

## 5. Cách chạy test case

Trên máy local, chạy:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-cpu.txt
python -m pip install -e .
python -m pytest
```

Các test case được thiết kế để không bắt buộc phải có GPU. Nếu thiếu PyTorch hoặc Qiskit, một số test sẽ được skip hoặc chỉ chạy phần CPU.

---

## 6. Cách build container Apptainer

```bash
apptainer build hpcq-gpu.sif containers/apptainer-gpu-qiskit.def
```

File `.sif` là image hoàn chỉnh của Apptainer. Đây là artifact quan trọng trong báo cáo vì nó thể hiện môi trường có thể tái lập.

---

## 7. Cách chạy container với GPU

```bash
apptainer exec --nv --bind "$PWD":/workspace --pwd /workspace hpcq-gpu.sif \
  python3 -m hpcq.gpu_check --output results/gpu_check.json
```

Ý nghĩa:

| Thành phần | Ý nghĩa |
|---|---|
| `apptainer exec` | Chạy lệnh trong container |
| `--nv` | Expose NVIDIA GPU vào container |
| `--bind "$PWD":/workspace` | Mount source code hiện tại vào container |
| `--pwd /workspace` | Chạy từ thư mục `/workspace` |
| `python3 -m hpcq.gpu_check` | Chạy module kiểm tra GPU |

---

## 8. Cách chạy bằng Slurm

```bash
sbatch slurm/run_gpu_qiskit.sbatch
```

Script này yêu cầu:

```bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
```

Nếu cluster của bạn dùng partition khác, cần sửa `--partition=gpu` thành tên đúng. Ví dụ:

```bash
#SBATCH --partition=a100
```

---

## 9. Kết quả đầu ra

Mỗi benchmark ghi file JSON. Ví dụ:

```text
results/gpu_check.json
results/torch_matmul.json
results/qiskit_aer.json
results/suite.jsonl
```

Bạn có thể dùng các file này để tạo bảng kết quả trong báo cáo.

---

## 10. Nội dung nên viết trong báo cáo

Phần triển khai có thể viết theo cấu trúc:

1. Kiến trúc tổng thể.
2. Lý do chọn Apptainer.
3. Cách build container.
4. Cách expose GPU vào container.
5. Cách tích hợp Slurm.
6. Thiết kế workload AI.
7. Thiết kế workload quantum.
8. Thiết kế benchmark.
9. Kết quả thực nghiệm.
10. Nhận xét về ưu/nhược điểm.

---

## 11. Hạn chế cần nêu rõ

Nếu không có cluster thật, cần nói rõ:

- Chưa đánh giá được InfiniBand/RDMA thật.
- Chưa đánh giá được multi-node NCCL thật.
- MIG/MPS chỉ khảo sát lý thuyết nếu không có A100/H100.
- Cloud QPU là tùy chọn, không bắt buộc nếu không có tài khoản.
- Kết quả quantum là mô phỏng quantum circuit, không phải chạy trên QPU thật.

---

## 12. Kết luận kỹ thuật

Repo này tạo ra một baseline triển khai đủ mạnh cho đồ án. Nó thể hiện được năng lực:

- DevOps/container.
- HPC scheduler.
- GPU computing.
- Quantum software stack.
- Benchmark và reproducibility.

Đây là phần thực hành cốt lõi phù hợp với yêu cầu của đề tài.
