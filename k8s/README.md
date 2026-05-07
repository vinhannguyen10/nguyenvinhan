# Kubernetes comparison arm

This folder is not the primary HPC path. It exists to compare the operational model of Kubernetes with the Slurm + Apptainer path.

Required cluster-side components for a real GPU/RDMA test:

1. NVIDIA GPU Operator or NVIDIA device plugin.
2. Container runtime configured for NVIDIA GPUs.
3. Optional SR-IOV/RDMA operator if InfiniBand/RDMA devices must be exposed to pods.
4. Persistent storage or object storage for benchmark outputs.

Minimal smoke test:

```bash
kubectl apply -f k8s/gpu-quantum-job.yaml
kubectl logs job/hpcq-gpu-quantum-smoke
```
