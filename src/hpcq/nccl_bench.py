from __future__ import annotations

import argparse
import os
import time
from typing import Any

from hpcq.result import BenchmarkResult, write_json


def run_torch_distributed_nccl(elements: int = 1_000_000, iterations: int = 20, backend: str = "nccl") -> BenchmarkResult:
    try:
        import torch
        import torch.distributed as dist
    except Exception as exc:
        return BenchmarkResult(name="torch_distributed_nccl", ok=False, error=f"PyTorch distributed import failed: {exc}")

    if backend == "nccl" and not torch.cuda.is_available():
        return BenchmarkResult(
            name="torch_distributed_nccl",
            ok=False,
            error="NCCL requested but torch.cuda.is_available() is False. Use --backend gloo for CPU smoke test.",
            metrics={"torch_version": torch.__version__, "nccl_available": dist.is_nccl_available()},
        )
    if backend == "nccl" and not dist.is_nccl_available():
        return BenchmarkResult(name="torch_distributed_nccl", ok=False, error="torch.distributed reports NCCL unavailable.")

    rank = int(os.environ.get("RANK", "0"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    initialized_here = False
    try:
        if not dist.is_initialized():
            if world_size == 1:
                os.environ.setdefault("MASTER_ADDR", "127.0.0.1")
                os.environ.setdefault("MASTER_PORT", "29500")
            dist.init_process_group(backend=backend, rank=rank, world_size=world_size)
            initialized_here = True

        device = torch.device("cuda", local_rank) if backend == "nccl" else torch.device("cpu")
        if device.type == "cuda":
            torch.cuda.set_device(device)
        tensor = torch.ones(elements, device=device)
        for _ in range(3):
            dist.all_reduce(tensor)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        start = time.perf_counter()
        for _ in range(iterations):
            dist.all_reduce(tensor)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        elapsed = time.perf_counter() - start
        bytes_per_iter = tensor.numel() * tensor.element_size()
        metrics: dict[str, Any] = {
            "backend": backend,
            "rank": rank,
            "world_size": world_size,
            "local_rank": local_rank,
            "elements": elements,
            "iterations": iterations,
            "elapsed_seconds": elapsed,
            "seconds_per_allreduce": elapsed / iterations,
            "payload_MB_per_rank": bytes_per_iter / 1e6,
            "approx_effective_MBps_per_rank": (bytes_per_iter * iterations / elapsed / 1e6) if elapsed > 0 else None,
            "tensor_first_value": float(tensor[0].detach().cpu()),
            "torch_version": torch.__version__,
            "nccl_available": dist.is_nccl_available(),
        }
        if device.type == "cuda":
            metrics["gpu_name"] = torch.cuda.get_device_name(device)
        return BenchmarkResult(name="torch_distributed_nccl", ok=True, metrics=metrics)
    except Exception as exc:
        return BenchmarkResult(name="torch_distributed_nccl", ok=False, error=str(exc))
    finally:
        if initialized_here:
            try:
                dist.destroy_process_group()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Torch distributed NCCL/Gloo smoke benchmark.")
    parser.add_argument("--elements", type=int, default=1_000_000)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--backend", choices=["nccl", "gloo"], default="nccl")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_torch_distributed_nccl(args.elements, args.iterations, args.backend)
    print(result.to_json())
    if args.output and int(os.environ.get("RANK", "0")) == 0:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
