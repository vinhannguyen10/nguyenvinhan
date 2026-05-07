from __future__ import annotations

import argparse
import socket
import time

from hpcq.result import BenchmarkResult, write_json


def run_mpi_hello() -> BenchmarkResult:
    try:
        from mpi4py import MPI

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        host = socket.gethostname()
        start = time.perf_counter()
        gathered = comm.gather({"rank": rank, "size": size, "host": host}, root=0)
        comm.Barrier()
        end = time.perf_counter()
        if rank == 0:
            return BenchmarkResult(
                name="mpi_hello",
                ok=True,
                metrics={
                    "world_size": size,
                    "gathered": gathered,
                    "barrier_elapsed_seconds": end - start,
                },
            )
        return BenchmarkResult(name="mpi_hello_worker", ok=True, metrics={"rank": rank, "size": size})
    except Exception as exc:
        return BenchmarkResult(name="mpi_hello", ok=False, error=str(exc))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MPI hello test for containerized Slurm jobs.")
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_mpi_hello()
    print(result.to_json())
    if args.output and result.name == "mpi_hello":
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
