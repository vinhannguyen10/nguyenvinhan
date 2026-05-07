# MPI, UCX, OFED, and RDMA notes

For HPC containers, MPI compatibility is often harder than basic GPU visibility. There are two common approaches:

1. **Hybrid host MPI model**: use host MPI launcher and bind host MPI/UCX/verbs libraries into the container.
2. **Container MPI model**: install MPI inside the container and ensure ABI/network compatibility with the host fabric.

Recommended checks:

```bash
ibv_devinfo -l
ucx_info -v
srun -N 2 -n 4 apptainer exec --bind "$PWD":/workspace hpcq-gpu.sif python3 -m hpcq.mpi_bench
```

For a report, separate the result into:

- point-to-point latency/bandwidth;
- collective allreduce time;
- whether the run was single-node or multi-node;
- whether RDMA/InfiniBand devices were visible.
