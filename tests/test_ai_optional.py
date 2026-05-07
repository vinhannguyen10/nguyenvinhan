import os

import pytest

from hpcq.ai_train_bench import run_ai_train_benchmark


def test_ai_train_cli_optional_signature_only():
    assert callable(run_ai_train_benchmark)


@pytest.mark.skipif(os.environ.get("RUN_TORCH_TESTS") != "1", reason="torch benchmark test is optional and can be slow in CI")
def test_ai_train_optional_torch_runtime():
    result = run_ai_train_benchmark(samples=32, batch_size=8, epochs=1, device_choice="cpu")
    assert result.ok
    assert result.metrics["samples"] == 32
