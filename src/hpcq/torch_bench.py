from __future__ import annotations

import argparse
import time
from typing import Literal

from hpcq.result import BenchmarkResult, write_json

DeviceChoice = Literal["auto", "cpu", "cuda"]


def select_device(choice: DeviceChoice):
    import torch

    if choice == "cpu":
        return torch.device("cpu")
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested CUDA, but torch.cuda.is_available() is False.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def run_torch_matmul_benchmark(
    size: int = 4096,
    iterations: int = 10,
    warmup: int = 2,
    device_choice: DeviceChoice = "auto",
) -> BenchmarkResult:
    try:
        import torch

        device = select_device(device_choice)
        dtype = torch.float32
        a = torch.randn((size, size), device=device, dtype=dtype)
        b = torch.randn((size, size), device=device, dtype=dtype)

        for _ in range(warmup):
            _ = a @ b
        if device.type == "cuda":
            torch.cuda.synchronize()

        start = time.perf_counter()
        for _ in range(iterations):
            c = a @ b
        if device.type == "cuda":
            torch.cuda.synchronize()
        end = time.perf_counter()

        elapsed = end - start
        ops = 2 * (size ** 3) * iterations
        tflops = ops / elapsed / 1e12 if elapsed > 0 else 0.0
        metrics = {
            "torch_version": torch.__version__,
            "device": str(device),
            "matrix_size": size,
            "iterations": iterations,
            "warmup": warmup,
            "elapsed_seconds": elapsed,
            "seconds_per_iteration": elapsed / iterations,
            "approx_tflops": tflops,
            "result_checksum": float(c.flatten()[0].detach().cpu()),
        }
        if device.type == "cuda":
            metrics["gpu_name"] = torch.cuda.get_device_name(device)
            metrics["max_memory_allocated_mb"] = torch.cuda.max_memory_allocated(device) / 1024**2
        return BenchmarkResult(name="torch_matmul", ok=True, metrics=metrics)
    except Exception as exc:
        return BenchmarkResult(name="torch_matmul", ok=False, error=str(exc))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PyTorch matrix multiplication benchmark.")
    parser.add_argument("--size", type=int, default=4096)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_torch_matmul_benchmark(
        size=args.size,
        iterations=args.iterations,
        warmup=args.warmup,
        device_choice=args.device,
    )
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
