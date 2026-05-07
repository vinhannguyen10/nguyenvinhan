from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import time
from pathlib import Path
from statistics import mean
from typing import Any

from hpcq.result import BenchmarkResult, write_json


def parse_power_csv(text: str) -> list[float]:
    values: list[float] = []
    for row in csv.reader(text.splitlines()):
        for cell in row:
            cell = cell.strip().lower().replace("w", "").strip()
            try:
                values.append(float(cell))
                break
            except ValueError:
                continue
    return values


def sample_nvidia_power() -> list[float]:
    if shutil.which("nvidia-smi") is None:
        return []
    cmd = [
        "nvidia-smi",
        "--query-gpu=power.draw",
        "--format=csv,noheader,nounits",
    ]
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False, timeout=5)
    if completed.returncode != 0:
        return []
    return parse_power_csv(completed.stdout)


def monitor_power(seconds: float = 5.0, interval: float = 0.5) -> BenchmarkResult:
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    while time.perf_counter() - start < seconds:
        t = time.perf_counter() - start
        powers = sample_nvidia_power()
        rows.append({"t_seconds": t, "power_watts": powers})
        time.sleep(interval)
    flattened = [p for row in rows for p in row["power_watts"]]
    elapsed = time.perf_counter() - start
    metrics = {
        "elapsed_seconds": elapsed,
        "interval_seconds": interval,
        "samples": rows,
        "num_power_samples": len(flattened),
        "mean_power_watts": mean(flattened) if flattened else None,
        "max_power_watts": max(flattened) if flattened else None,
        "estimated_energy_wh": (mean(flattened) * elapsed / 3600.0) if flattened else None,
    }
    ok = bool(flattened)
    return BenchmarkResult(
        name="gpu_power_monitor",
        ok=ok,
        metrics=metrics,
        error=None if ok else "nvidia-smi power sampling unavailable; run on an allocated NVIDIA GPU node.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample GPU power through nvidia-smi and estimate Wh.")
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = monitor_power(args.seconds, args.interval)
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
