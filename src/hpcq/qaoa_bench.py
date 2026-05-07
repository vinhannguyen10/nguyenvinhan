from __future__ import annotations

import argparse
import math
import time
from typing import Any

import numpy as np

from hpcq.result import BenchmarkResult, write_json


def maxcut_expectation_from_angles(gamma: float, beta: float) -> float:
    """Toy 2-node MaxCut QAOA p=1 expectation using a direct statevector simulation.

    Hamiltonian cost is C=(1-Z0 Z1)/2. This gives a lightweight hybrid classical-quantum
    workload without requiring Qiskit/PennyLane. Larger QAOA experiments are provided by
    optional SDK benchmarks.
    """
    state = np.zeros(4, dtype=np.complex128)
    state[0] = 1.0
    h = np.array([[1, 1], [1, -1]], dtype=np.complex128) / math.sqrt(2.0)
    h2 = np.kron(h, h)
    state = h2 @ state
    costs = np.array([0, 1, 1, 0], dtype=np.float64)
    state = np.exp(-1j * gamma * costs) * state
    rx = np.array(
        [[math.cos(beta), -1j * math.sin(beta)], [-1j * math.sin(beta), math.cos(beta)]],
        dtype=np.complex128,
    )
    state = np.kron(rx, rx) @ state
    probabilities = np.abs(state) ** 2
    return float(np.dot(probabilities, costs))


def run_qaoa_grid_benchmark(grid_size: int = 32) -> BenchmarkResult:
    start = time.perf_counter()
    best: dict[str, Any] = {"expectation": -1.0, "gamma": None, "beta": None}
    values = []
    for gamma in np.linspace(0.0, math.pi, grid_size):
        for beta in np.linspace(0.0, math.pi / 2.0, grid_size):
            value = maxcut_expectation_from_angles(float(gamma), float(beta))
            values.append(value)
            if value > best["expectation"]:
                best = {"expectation": value, "gamma": float(gamma), "beta": float(beta)}
    elapsed = time.perf_counter() - start
    return BenchmarkResult(
        name="qaoa_maxcut_grid",
        ok=True,
        metrics={
            "problem": "2-node MaxCut",
            "grid_size": grid_size,
            "num_evaluations": grid_size * grid_size,
            "elapsed_seconds": elapsed,
            "evaluations_per_second": (grid_size * grid_size / elapsed) if elapsed > 0 else None,
            "best": best,
            "mean_expectation": float(np.mean(values)),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Small QAOA MaxCut grid-search benchmark.")
    parser.add_argument("--grid-size", type=int, default=32)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_qaoa_grid_benchmark(args.grid_size)
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
