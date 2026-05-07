from __future__ import annotations

import argparse
import time
from typing import Literal

from hpcq.result import BenchmarkResult, write_json

DeviceChoice = Literal["auto", "cpu", "gpu"]


def choose_device(device_choice: DeviceChoice, wires: int):
    import pennylane as qml

    if device_choice == "gpu":
        return qml.device("lightning.gpu", wires=wires)
    if device_choice == "cpu":
        return qml.device("default.qubit", wires=wires)
    try:
        return qml.device("lightning.gpu", wires=wires)
    except Exception:
        return qml.device("default.qubit", wires=wires)


def run_pennylane_benchmark(n_qubits: int = 20, depth: int = 4, device_choice: DeviceChoice = "auto") -> BenchmarkResult:
    try:
        import pennylane as qml
        import numpy as np

        dev = choose_device(device_choice, wires=n_qubits)

        @qml.qnode(dev)
        def circuit(params):
            for layer in range(depth):
                for wire in range(n_qubits):
                    qml.Hadamard(wires=wire)
                    qml.RX(params[layer, wire], wires=wire)
                for wire in range(n_qubits - 1):
                    qml.CNOT(wires=[wire, wire + 1])
            return qml.expval(qml.PauliZ(0))

        params = np.full((depth, n_qubits), 0.123, dtype=float)
        start = time.perf_counter()
        value = circuit(params)
        end = time.perf_counter()
        return BenchmarkResult(
            name="pennylane",
            ok=True,
            metrics={
                "n_qubits": n_qubits,
                "depth": depth,
                "requested_device": device_choice,
                "device_short_name": getattr(dev, "short_name", str(dev)),
                "elapsed_seconds": end - start,
                "expectation_value": float(value),
            },
        )
    except Exception as exc:
        return BenchmarkResult(name="pennylane", ok=False, error=str(exc))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PennyLane quantum benchmark.")
    parser.add_argument("--n-qubits", type=int, default=20)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--device", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_pennylane_benchmark(args.n_qubits, args.depth, args.device)
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
