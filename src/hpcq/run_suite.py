from __future__ import annotations

import argparse
from pathlib import Path

from hpcq.gpu_check import run_gpu_check
from hpcq.hybrid_vqe import run_numpy_vqe
from hpcq.qiskit_bench import run_qiskit_benchmark
from hpcq.result import BenchmarkResult, append_jsonl, write_json
from hpcq.sysinfo import system_report
from hpcq.torch_bench import run_torch_matmul_benchmark


def _write_results(results: list[BenchmarkResult], out: Path) -> None:
    for result in results:
        write_json(result, out / f"{result.name}.json")
        append_jsonl(result, out / "suite.jsonl")


def run_suite(
    output_dir: str | Path = "results",
    device: str = "auto",
    matrix_size: int = 2048,
    qiskit_qubits: int = 18,
    qiskit_depth: int = 6,
    dry_run: bool = False,
    include_system: bool = True,
    include_vqe: bool = True,
    include_gpu_check: bool = True,
    include_pennylane: bool = False,
    include_mpi: bool = False,
    include_nccl: bool = False,
    include_energy: bool = False,
    include_cudaq: bool = False,
    include_ai: bool = False,
    include_cirq: bool = False,
    include_qaoa: bool = False,
) -> list[BenchmarkResult]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if dry_run:
        result = BenchmarkResult(
            name="dry_run",
            ok=True,
            metrics={
                "output_dir": str(out),
                "device": device,
                "matrix_size": matrix_size,
                "qiskit_qubits": qiskit_qubits,
                "qiskit_depth": qiskit_depth,
                "include_system": include_system,
                "include_vqe": include_vqe,
                "include_gpu_check": include_gpu_check,
                "include_pennylane": include_pennylane,
                "include_mpi": include_mpi,
                "include_nccl": include_nccl,
                "include_energy": include_energy,
                "include_cudaq": include_cudaq,
                "include_ai": include_ai,
                "include_cirq": include_cirq,
                "include_qaoa": include_qaoa,
            },
        )
        _write_results([result], out)
        return [result]

    torch_device = "auto" if device == "auto" else ("cuda" if device == "gpu" else "cpu")
    quantum_device = "auto" if device == "auto" else ("gpu" if device == "gpu" else "cpu")
    results: list[BenchmarkResult] = []
    if include_system:
        results.append(system_report())
    if include_gpu_check:
        results.append(run_gpu_check())
    results.extend(
        [
            run_torch_matmul_benchmark(size=matrix_size, iterations=5, warmup=1, device_choice=torch_device),
            run_qiskit_benchmark(n_qubits=qiskit_qubits, depth=qiskit_depth, shots=512, device_choice=quantum_device),
        ]
    )
    if include_vqe:
        results.append(run_numpy_vqe(steps=40, learning_rate=0.15))
    if include_ai:
        from hpcq.ai_train_bench import run_ai_train_benchmark

        results.append(run_ai_train_benchmark(samples=2048, batch_size=128, epochs=2, device_choice=torch_device))
    if include_cirq:
        from hpcq.cirq_bench import run_cirq_ghz_benchmark

        results.append(run_cirq_ghz_benchmark(n_qubits=min(12, max(4, qiskit_qubits)), repetitions=512))
    if include_qaoa:
        from hpcq.qaoa_bench import run_qaoa_grid_benchmark

        results.append(run_qaoa_grid_benchmark(grid_size=32))
    if include_pennylane:
        from hpcq.pennylane_bench import run_pennylane_benchmark

        results.append(run_pennylane_benchmark(n_qubits=max(4, qiskit_qubits), depth=4, device_choice=quantum_device))
    if include_mpi:
        from hpcq.mpi_bench import run_mpi_microbench

        results.append(run_mpi_microbench(iterations=25, payload_bytes=4096))
    if include_nccl:
        from hpcq.nccl_bench import run_torch_distributed_nccl

        results.append(run_torch_distributed_nccl(elements=256_000, iterations=5, backend="nccl" if device != "cpu" else "gloo"))
    if include_energy:
        from hpcq.energy import monitor_power

        results.append(monitor_power(seconds=3.0, interval=0.5))
    if include_cudaq:
        from hpcq.cudaq_bench import run_cudaq_bell

        results.append(run_cudaq_bell(shots=256))
    _write_results(results, out)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the HPC GPU Quantum benchmark suite.")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--device", choices=["auto", "cpu", "gpu"], default="auto")
    parser.add_argument("--matrix-size", type=int, default=2048)
    parser.add_argument("--qiskit-qubits", type=int, default=18)
    parser.add_argument("--qiskit-depth", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-system", action="store_true")
    parser.add_argument("--no-vqe", action="store_true")
    parser.add_argument("--no-gpu-check", action="store_true")
    parser.add_argument("--include-pennylane", action="store_true")
    parser.add_argument("--include-mpi", action="store_true")
    parser.add_argument("--include-nccl", action="store_true")
    parser.add_argument("--include-energy", action="store_true")
    parser.add_argument("--include-cudaq", action="store_true")
    parser.add_argument("--include-ai", action="store_true")
    parser.add_argument("--include-cirq", action="store_true")
    parser.add_argument("--include-qaoa", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_suite(
        output_dir=args.output_dir,
        device=args.device,
        matrix_size=args.matrix_size,
        qiskit_qubits=args.qiskit_qubits,
        qiskit_depth=args.qiskit_depth,
        dry_run=args.dry_run,
        include_system=not args.no_system,
        include_vqe=not args.no_vqe,
        include_gpu_check=not args.no_gpu_check,
        include_pennylane=args.include_pennylane,
        include_mpi=args.include_mpi,
        include_nccl=args.include_nccl,
        include_energy=args.include_energy,
        include_cudaq=args.include_cudaq,
        include_ai=args.include_ai,
        include_cirq=args.include_cirq,
        include_qaoa=args.include_qaoa,
    )
    for result in results:
        print(result.to_json())
    return 0 if all(r.ok for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
