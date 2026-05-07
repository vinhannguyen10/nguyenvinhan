from __future__ import annotations

import os
import platform
import resource
import shutil
import subprocess
from pathlib import Path
from typing import Any

from hpcq.result import BenchmarkResult, write_json


def run_command(cmd: list[str], timeout: int = 3) -> dict[str, Any]:
    if shutil.which(cmd[0]) is None:
        return {"ok": False, "returncode": None, "stdout": "", "error": f"command not found: {cmd[0]}"}
    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=timeout,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "error": None if completed.returncode == 0 else completed.stdout.strip(),
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "error": str(exc)}


def read_text(path: str | Path, max_chars: int = 4096) -> str | None:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except Exception:
        return None


def read_first_existing(paths: list[str | Path], max_chars: int = 4096) -> str | None:
    for path in paths:
        value = read_text(path, max_chars=max_chars)
        if value is not None:
            return value.strip()
    return None


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if value in {"", "max"}:
        return None
    try:
        return int(value)
    except Exception:
        return None


def detect_container_runtime() -> dict[str, Any]:
    env = os.environ
    markers = {
        "apptainer_name": env.get("APPTAINER_NAME") or env.get("SINGULARITY_NAME"),
        "apptainer_container": env.get("APPTAINER_CONTAINER") or env.get("SINGULARITY_CONTAINER"),
        "docker_env_file": Path("/.dockerenv").exists(),
        "container_env": env.get("container"),
        "kubernetes_service_host": env.get("KUBERNETES_SERVICE_HOST"),
    }
    cgroup = read_text("/proc/1/cgroup") or ""
    runtime = "bare-metal-or-unknown"
    if markers["apptainer_name"] or markers["apptainer_container"]:
        runtime = "apptainer-or-singularity"
    elif markers["docker_env_file"] or "docker" in cgroup or "kubepods" in cgroup:
        runtime = "docker-or-kubernetes"
    elif "libpod" in cgroup or "podman" in cgroup:
        runtime = "podman"
    return {"runtime_guess": runtime, "markers": markers, "proc_1_cgroup": cgroup[:2048]}


def cgroup_limits() -> dict[str, Any]:
    cgroup2 = Path("/sys/fs/cgroup/cgroup.controllers").exists()
    if cgroup2:
        cpu_max = read_first_existing(["/sys/fs/cgroup/cpu.max"])
        memory_max = read_first_existing(["/sys/fs/cgroup/memory.max"])
        pids_max = read_first_existing(["/sys/fs/cgroup/pids.max"])
        return {
            "version": "v2",
            "cpu.max": cpu_max,
            "memory.max": memory_max,
            "memory.max.bytes": parse_int(memory_max),
            "pids.max": pids_max,
        }
    memory_limit = read_first_existing(["/sys/fs/cgroup/memory/memory.limit_in_bytes"])
    cpu_quota = read_first_existing(["/sys/fs/cgroup/cpu/cpu.cfs_quota_us"])
    cpu_period = read_first_existing(["/sys/fs/cgroup/cpu/cpu.cfs_period_us"])
    return {
        "version": "v1-or-unknown",
        "memory.limit_in_bytes": memory_limit,
        "memory.limit.bytes": parse_int(memory_limit),
        "cpu.cfs_quota_us": cpu_quota,
        "cpu.cfs_period_us": cpu_period,
    }


def slurm_environment() -> dict[str, Any]:
    keys = [
        "SLURM_JOB_ID",
        "SLURM_JOB_NAME",
        "SLURM_JOB_NODELIST",
        "SLURM_JOB_NUM_NODES",
        "SLURM_NTASKS",
        "SLURM_CPUS_PER_TASK",
        "SLURM_GPUS",
        "SLURM_GPUS_ON_NODE",
        "CUDA_VISIBLE_DEVICES",
    ]
    return {key: os.environ.get(key) for key in keys if os.environ.get(key) is not None}


def system_report() -> BenchmarkResult:
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    metrics: dict[str, Any] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "rlimit_nofile": {"soft": soft, "hard": hard},
        "runtime": detect_container_runtime(),
        "cgroups": cgroup_limits(),
        "slurm": slurm_environment(),
        "commands": {
            "nvidia_smi_L": run_command(["nvidia-smi", "-L"]),
            "apptainer_version": run_command(["apptainer", "--version"]),
            "singularity_version": run_command(["singularity", "--version"]),
            "docker_version": run_command(["docker", "--version"]),
            "podman_version": run_command(["podman", "--version"]),
            "srun_version": run_command(["srun", "--version"]),
            "ibv_devinfo": run_command(["ibv_devinfo", "-l"]),
        },
    }
    return BenchmarkResult(name="system_report", ok=True, metrics=metrics)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Collect host/container/HPC runtime diagnostics.")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    result = system_report()
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
