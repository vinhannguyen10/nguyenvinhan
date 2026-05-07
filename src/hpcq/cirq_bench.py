from __future__ import annotations

import argparse
import time

from hpcq.result import BenchmarkResult, write_json


def run_cirq_ghz_benchmark(n_qubits: int = 12, repetitions: int = 1024) -> BenchmarkResult:
    try:
        import cirq
    except Exception as exc:
        return BenchmarkResult(name="cirq_ghz", ok=False, error=f"cirq import failed: {exc}")

    try:
        qubits = cirq.LineQubit.range(n_qubits)
        circuit = cirq.Circuit()
        circuit.append(cirq.H(qubits[0]))
        for i in range(n_qubits - 1):
            circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))
        circuit.append(cirq.measure(*qubits, key="m"))
        simulator = cirq.Simulator()
        start = time.perf_counter()
        result = simulator.run(circuit, repetitions=repetitions)
        elapsed = time.perf_counter() - start
        histogram = result.histogram(key="m")
        top_counts = sorted(histogram.items(), key=lambda item: item[1], reverse=True)[:8]
        metrics = {
            "n_qubits": n_qubits,
            "repetitions": repetitions,
            "elapsed_seconds": elapsed,
            "top_counts": [(format(k, f"0{n_qubits}b"), int(v)) for k, v in top_counts],
            "num_observed_states": len(histogram),
        }
        return BenchmarkResult(name="cirq_ghz", ok=True, metrics=metrics)
    except Exception as exc:
        return BenchmarkResult(name="cirq_ghz", ok=False, error=str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="Cirq GHZ circuit benchmark.")
    parser.add_argument("--n-qubits", type=int, default=12)
    parser.add_argument("--repetitions", type=int, default=1024)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_cirq_ghz_benchmark(args.n_qubits, args.repetitions)
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
