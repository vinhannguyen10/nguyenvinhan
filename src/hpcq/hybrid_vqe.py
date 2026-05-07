from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass

import numpy as np

from hpcq.result import BenchmarkResult, write_json


@dataclass
class VQEStep:
    theta: float
    energy: float


def ry(theta: float) -> np.ndarray:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def expectation_z(theta: float) -> float:
    state = ry(theta) @ np.array([1.0 + 0.0j, 0.0 + 0.0j])
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    return float(np.real(np.conjugate(state) @ (z @ state)))


def finite_difference_gradient(theta: float, eps: float = 1e-5) -> float:
    return (expectation_z(theta + eps) - expectation_z(theta - eps)) / (2 * eps)


def run_numpy_vqe(steps: int = 50, learning_rate: float = 0.1, initial_theta: float = 0.2) -> BenchmarkResult:
    theta = initial_theta
    history: list[VQEStep] = []
    start = time.perf_counter()
    for _ in range(steps):
        energy = expectation_z(theta)
        history.append(VQEStep(theta=theta, energy=energy))
        theta -= learning_rate * finite_difference_gradient(theta)
    final_energy = expectation_z(theta)
    elapsed = time.perf_counter() - start
    return BenchmarkResult(
        name="hybrid_vqe_numpy",
        ok=True,
        metrics={
            "model": "one-qubit variational Ry ansatz minimizing <Z>",
            "steps": steps,
            "learning_rate": learning_rate,
            "initial_theta": initial_theta,
            "final_theta": theta,
            "final_energy": final_energy,
            "target_energy": -1.0,
            "absolute_error_to_target": abs(final_energy + 1.0),
            "elapsed_seconds": elapsed,
            "history_head": [step.__dict__ for step in history[:5]],
            "history_tail": [step.__dict__ for step in history[-5:]],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal classical-quantum hybrid VQE-style optimization demo.")
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--initial-theta", type=float, default=0.2)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_numpy_vqe(args.steps, args.learning_rate, args.initial_theta)
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
