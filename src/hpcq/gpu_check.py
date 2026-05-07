from __future__ import annotations

import argparse
import shutil
import subprocess
from typing import Any

from hpcq.result import BenchmarkResult, write_json


def run_command(cmd: list[str], timeout: int = 20) -> tuple[bool, str]:
    if shutil.which(cmd[0]) is None:
        return False, f"command not found: {cmd[0]}"
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        return completed.returncode == 0, completed.stdout.strip()
    except Exception as exc:
        return False, str(exc)


def check_torch() -> dict[str, Any]:
    info: dict[str, Any] = {"installed": False, "cuda_available": False}
    try:
        import torch
    except Exception as exc:
        info["error"] = str(exc)
        return info

    info["installed"] = True
    info["version"] = torch.__version__
    info["cuda_available"] = bool(torch.cuda.is_available())
    info["cuda_version"] = getattr(torch.version, "cuda", None)
    info["device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
    if torch.cuda.is_available():
        info["devices"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    return info


def run_gpu_check() -> BenchmarkResult:
    smi_ok, smi_output = run_command([
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total,power.limit",
        "--format=csv,noheader",
    ])
    torch_info = check_torch()
    ok = smi_ok or bool(torch_info.get("cuda_available"))
    return BenchmarkResult(
        name="gpu_check",
        ok=ok,
        metrics={
            "nvidia_smi_ok": smi_ok,
            "nvidia_smi_output": smi_output,
            "torch": torch_info,
        },
        error=None if ok else "No NVIDIA GPU was visible from nvidia-smi or PyTorch CUDA.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check GPU visibility inside or outside a container.")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_gpu_check()
    print(result.to_json())
    if args.output:
        write_json(result, args.output)
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
