# MIG, MPS, and Kubernetes notes

## MIG

MIG is useful when a single large NVIDIA GPU must be divided into isolated GPU instances for different users or jobs. In a thesis evaluation, use MIG only if the cluster has supported GPUs such as A100/H100 and the administrator permits MIG mode.

Suggested evidence:

```bash
bash scripts/mig_report.sh results/mig_report.txt
```

Then run the normal GPU suite with `CUDA_VISIBLE_DEVICES` pointing to the MIG device allocated by Slurm or Kubernetes.

## MPS

MPS is useful for MPI-style applications where many processes share one GPU. The script `slurm/run_mps_two_tasks.sbatch` starts MPS and launches two containerized PyTorch workloads on one allocated GPU.

## Kubernetes comparison

Kubernetes is not the main path for this thesis, but it is useful for comparing cloud-native operations. For GPU support, the cluster normally needs the NVIDIA GPU Operator or device plugin. For RDMA, SR-IOV configuration is site-specific, so this repository only provides an example manifest.
