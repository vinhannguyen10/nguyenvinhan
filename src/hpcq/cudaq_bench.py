from __future__ import annotations

import argparse
import time

from hpcq.result import BenchmarkResult, write_json


def run_cudaq_bell(shots: int = 1000) -> BenchmarkResult:
    try:
        import cudaq
    except Exception as exc:
        return BenchmarkResult(name="cudaq_bell", ok=False, error=f"cudaq import failed: {exc}")

    try:
        @cudaq.kernel
        def bell():
            q = cudaq.qvector(2)
            h(q[0])
            x.ctrl(q[0], q[1])
            mz(q)

        start = time.perf_counter()
        counts = cudaq.sample(bell, shots_count=shots)
        elapsed = time.perf_counter() - start
        return BenchmarkResult(
            name="cudaq_bell",
            ok=True,
            metrics={
                "shots": shots,
                "elapsed_seconds": elapsed,
                "counts": dict(counts),
                "target": str(cudaq.get_target()) if hasattr(cudaq, "get_target") else None,
            },
        )
    except Exception as exc:
        return BenchmarkResult(name="cudaq_bell", ok=False, error=str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="CUDA-Q Bell-state smoke benchmark.")
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_cudaq_bell(args.shots)
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
