import pytest


torch = pytest.importorskip("torch")

from hpcq.torch_bench import run_torch_matmul_benchmark


def test_torch_cpu_benchmark_small():
    result = run_torch_matmul_benchmark(size=32, iterations=1, warmup=0, device_choice="cpu")
    assert result.ok, result.error
    assert result.metrics["device"] == "cpu"
    assert result.metrics["matrix_size"] == 32
