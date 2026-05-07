from __future__ import annotations

import argparse
import time
from typing import Literal

from hpcq.result import BenchmarkResult, write_json

DeviceChoice = Literal["auto", "cpu", "gpu"]


def build_entangling_circuit(n_qubits: int, depth: int, measure: bool = True):
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n_qubits)
    for layer in range(depth):
        for q in range(n_qubits):
            qc.h(q)
            qc.rx(0.05 * (layer + 1), q)
            qc.rz(0.03 * (q + 1), q)
        for q in range(n_qubits - 1):
            qc.cx(q, q + 1)
        if n_qubits > 2:
            qc.cx(n_qubits - 1, 0)
    if measure:
        qc.measure_all()
    return qc


def make_simulator(device_choice: DeviceChoice, method: str):
    from qiskit_aer import AerSimulator

    if device_choice == "gpu":
        return AerSimulator(method=method, device="GPU")
    if device_choice == "cpu":
        return AerSimulator(method=method, device="CPU")
    try:
        return AerSimulator(method=method, device="GPU")
    except Exception:
        return AerSimulator(method=method, device="CPU")


def run_qiskit_benchmark(
    n_qubits: int = 20,
    depth: int = 8,
    shots: int = 1024,
    method: str = "statevector",
    device_choice: DeviceChoice = "auto",
) -> BenchmarkResult:
    try:
        from qiskit import transpile

        qc = build_entangling_circuit(n_qubits=n_qubits, depth=depth, measure=True)
        simulator = make_simulator(device_choice=device_choice, method=method)
        compiled = transpile(qc, simulator)

        start = time.perf_counter()
        result = simulator.run(compiled, shots=shots).result()
        end = time.perf_counter()

        counts = result.get_counts()
        metadata = result.results[0].metadata if result.results else {}
        metrics = {
            "n_qubits": n_qubits,
            "depth_parameter": depth,
            "shots": shots,
            "method": method,
            "requested_device": device_choice,
            "elapsed_seconds": end - start,
            "num_count_states": len(counts),
            "sample_counts": list(counts.items())[:5],
            "backend_name": getattr(simulator, "name", "AerSimulator"),
            "metadata": metadata,
        }
        return BenchmarkResult(name="qiskit_aer", ok=True, metrics=metrics)
    except Exception as exc:
        return BenchmarkResult(name="qiskit_aer", ok=False, error=str(exc))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Qiskit Aer quantum circuit benchmark.")
    parser.add_argument("--n-qubits", type=int, default=20)
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--method", default="statevector")
    parser.add_argument("--device", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_qiskit_benchmark(
        n_qubits=args.n_qubits,
        depth=args.depth,
        shots=args.shots,
        method=args.method,
        device_choice=args.device,
    )
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
