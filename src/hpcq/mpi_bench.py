from __future__ import annotations

import argparse
import socket
import time
from statistics import mean
from typing import Any

from hpcq.result import BenchmarkResult, write_json


def run_mpi_microbench(iterations: int = 100, payload_bytes: int = 1024) -> BenchmarkResult:
    try:
        from mpi4py import MPI
    except Exception as exc:
        return BenchmarkResult(name="mpi_microbench", ok=False, error=f"mpi4py import failed: {exc}")

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    host = socket.gethostname()
    hosts = comm.gather(host, root=0)

    data = bytearray(payload_bytes)
    pingpong_latencies: list[float] = []
    if size >= 2:
        partner = 1 if rank == 0 else 0
        if rank in (0, 1):
            for _ in range(iterations):
                comm.Barrier()
                start = time.perf_counter()
                if rank == 0:
                    comm.Send([data, MPI.BYTE], dest=partner, tag=11)
                    comm.Recv([data, MPI.BYTE], source=partner, tag=12)
                else:
                    comm.Recv([data, MPI.BYTE], source=partner, tag=11)
                    comm.Send([data, MPI.BYTE], dest=partner, tag=12)
                end = time.perf_counter()
                if rank == 0:
                    pingpong_latencies.append((end - start) / 2.0)
    comm.Barrier()

    allreduce_times: list[float] = []
    value = rank + 1.0
    for _ in range(iterations):
        start = time.perf_counter()
        total = comm.allreduce(value, op=MPI.SUM)
        end = time.perf_counter()
        allreduce_times.append(end - start)
    gathered_allreduce = comm.gather(allreduce_times, root=0)

    if rank != 0:
        return BenchmarkResult(name="mpi_microbench_worker", ok=True, metrics={"rank": rank, "size": size})

    allreduce_flat = [x for row in gathered_allreduce for x in row]
    metrics: dict[str, Any] = {
        "world_size": size,
        "hosts": hosts,
        "iterations": iterations,
        "payload_bytes": payload_bytes,
        "single_process_only": size == 1,
        "allreduce_mean_seconds": mean(allreduce_flat) if allreduce_flat else None,
        "allreduce_min_seconds": min(allreduce_flat) if allreduce_flat else None,
        "allreduce_max_seconds": max(allreduce_flat) if allreduce_flat else None,
        "allreduce_check_sum": total,
    }
    if pingpong_latencies:
        metrics.update(
            {
                "pingpong_mean_oneway_seconds": mean(pingpong_latencies),
                "pingpong_min_oneway_seconds": min(pingpong_latencies),
                "pingpong_max_oneway_seconds": max(pingpong_latencies),
                "estimated_pingpong_bandwidth_MBps": (payload_bytes / mean(pingpong_latencies) / 1e6) if mean(pingpong_latencies) > 0 else None,
            }
        )
    return BenchmarkResult(name="mpi_microbench", ok=True, metrics=metrics)


def main() -> int:
    parser = argparse.ArgumentParser(description="mpi4py latency/allreduce microbenchmark for containerized HPC jobs.")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--payload-bytes", type=int, default=1024)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = run_mpi_microbench(args.iterations, args.payload_bytes)
    print(result.to_json())
    if args.output and result.name == "mpi_microbench":
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
