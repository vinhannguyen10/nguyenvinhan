from __future__ import annotations

import argparse
from pathlib import Path

from hpcq.cirq_bench import run_cirq_ghz_benchmark
from hpcq.cudaq_bench import run_cudaq_bell
from hpcq.hybrid_vqe import run_numpy_vqe
from hpcq.pennylane_bench import run_pennylane_benchmark
from hpcq.qaoa_bench import run_qaoa_grid_benchmark
from hpcq.qiskit_bench import run_qiskit_benchmark
from hpcq.result import BenchmarkResult, append_jsonl, write_json


def run_quantum_suite(
    output_dir: str | Path = "results/quantum",
    device: str = "auto",
    qiskit_qubits: int = 16,
    cirq_qubits: int = 12,
    include_pennylane: bool = True,
    include_cudaq: bool = False,
) -> list[BenchmarkResult]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results: list[BenchmarkResult] = [
        run_qiskit_benchmark(n_qubits=qiskit_qubits, depth=4, shots=512, device_choice=device),
        run_cirq_ghz_benchmark(n_qubits=cirq_qubits, repetitions=512),
        run_numpy_vqe(steps=60, learning_rate=0.12),
        run_qaoa_grid_benchmark(grid_size=32),
    ]
    if include_pennylane:
        results.append(run_pennylane_benchmark(n_qubits=max(4, min(12, qiskit_qubits)), depth=3, device_choice=device))
    if include_cudaq:
        results.append(run_cudaq_bell(shots=512))
    for result in results:
        write_json(result, out / f"{result.name}.json")
        append_jsonl(result, out / "quantum_suite.jsonl")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Qiskit/Cirq/PennyLane/CUDA-Q hybrid quantum suite.")
    parser.add_argument("--output-dir", default="results/quantum")
    parser.add_argument("--device", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--qiskit-qubits", type=int, default=16)
    parser.add_argument("--cirq-qubits", type=int, default=12)
    parser.add_argument("--no-pennylane", action="store_true")
    parser.add_argument("--include-cudaq", action="store_true")
    args = parser.parse_args()
    results = run_quantum_suite(
        output_dir=args.output_dir,
        device=args.device,
        qiskit_qubits=args.qiskit_qubits,
        cirq_qubits=args.cirq_qubits,
        include_pennylane=not args.no_pennylane,
        include_cudaq=args.include_cudaq,
    )
    for result in results:
        print(result.to_json())
    return 0 if all(r.ok for r in results if r.name != "cudaq_bell") else 2


if __name__ == "__main__":
    raise SystemExit(main())
