from __future__ import annotations

import argparse
import time
from typing import Literal

from hpcq.result import BenchmarkResult, write_json

DeviceChoice = Literal["auto", "cpu", "cuda"]


def _select_device(torch, choice: DeviceChoice):
    if choice == "cpu":
        return torch.device("cpu")
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested CUDA, but torch.cuda.is_available() is False.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class _TinyCNNFactory:
    """Small CNN factory kept inside a class so torch import is optional."""

    @staticmethod
    def build(torch):
        nn = torch.nn
        return nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(16, 10),
        )


def run_ai_train_benchmark(
    samples: int = 4096,
    batch_size: int = 128,
    epochs: int = 2,
    image_size: int = 28,
    device_choice: DeviceChoice = "auto",
    seed: int = 1234,
) -> BenchmarkResult:
    """Train a small CNN on synthetic image data.

    This benchmark avoids network downloads, so it can run on offline HPC login/compute nodes.
    It is intentionally small and is meant as an AI workload smoke/performance test, not as a
    machine-learning accuracy benchmark.
    """
    try:
        import torch
    except Exception as exc:
        return BenchmarkResult(name="ai_tiny_cnn_train", ok=False, error=f"PyTorch import failed: {exc}")

    try:
        torch.manual_seed(seed)
        device = _select_device(torch, device_choice)
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)

        x = torch.randn(samples, 1, image_size, image_size, device=device)
        y = torch.randint(0, 10, (samples,), device=device)
        model = _TinyCNNFactory.build(torch).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        criterion = torch.nn.CrossEntropyLoss()

        if device.type == "cuda":
            torch.cuda.synchronize(device)
        start = time.perf_counter()
        total_loss = 0.0
        total_correct = 0
        total_seen = 0
        for _epoch in range(epochs):
            permutation = torch.randperm(samples, device=device)
            for offset in range(0, samples, batch_size):
                idx = permutation[offset : offset + batch_size]
                xb = x[idx]
                yb = y[idx]
                optimizer.zero_grad(set_to_none=True)
                logits = model(xb)
                loss = criterion(logits, yb)
                loss.backward()
                optimizer.step()
                with torch.no_grad():
                    total_loss += float(loss.detach().cpu()) * int(yb.numel())
                    total_correct += int((logits.argmax(dim=1) == yb).sum().detach().cpu())
                    total_seen += int(yb.numel())
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        elapsed = time.perf_counter() - start

        metrics = {
            "torch_version": torch.__version__,
            "device": str(device),
            "samples": samples,
            "batch_size": batch_size,
            "epochs": epochs,
            "image_size": image_size,
            "elapsed_seconds": elapsed,
            "samples_per_second": (samples * epochs / elapsed) if elapsed > 0 else None,
            "final_mean_loss": total_loss / total_seen if total_seen else None,
            "synthetic_accuracy": total_correct / total_seen if total_seen else None,
            "num_parameters": sum(p.numel() for p in model.parameters()),
        }
        if device.type == "cuda":
            metrics.update(
                {
                    "gpu_name": torch.cuda.get_device_name(device),
                    "peak_memory_allocated_mb": torch.cuda.max_memory_allocated(device) / 1024**2,
                    "cuda_runtime_version": torch.version.cuda,
                }
            )
        return BenchmarkResult(name="ai_tiny_cnn_train", ok=True, metrics=metrics)
    except Exception as exc:
        return BenchmarkResult(name="ai_tiny_cnn_train", ok=False, error=str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic tiny-CNN AI training benchmark for GPU/CPU containers.")
    parser.add_argument("--samples", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--image-size", type=int, default=28)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_ai_train_benchmark(
        samples=args.samples,
        batch_size=args.batch_size,
        epochs=args.epochs,
        image_size=args.image_size,
        device_choice=args.device,
    )
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
