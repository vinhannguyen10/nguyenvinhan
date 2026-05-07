# How to interpret benchmark results

## Important fields

| JSON field | Meaning |
|---|---|
| `ok` | Whether the benchmark completed successfully |
| `error` | Failure reason; keep this in the report if hardware/tool is missing |
| `metrics.elapsed_seconds` | Wall-clock time for the benchmark |
| `metrics.samples_per_second` | AI training throughput |
| `metrics.approx_tflops` | Approximate matrix multiplication throughput |
| `metrics.world_size` | MPI/NCCL number of processes |
| `metrics.estimated_energy_wh` | Estimated GPU energy from sampled power draw |
| `overhead_vs_baseline_percent` | Runtime overhead relative to selected baseline |

## Recommended interpretation

- Lower elapsed time means faster execution.
- Higher samples/second, TFLOPS, bandwidth, or evaluations/second means better throughput.
- Container overhead should be calculated against the same workload and same hardware.
- A failed JSON is still useful evidence if it documents a missing resource, for example no GPU, no Slurm, no CUDA-Q, or no InfiniBand.
