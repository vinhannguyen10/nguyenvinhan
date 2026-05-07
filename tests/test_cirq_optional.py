import pytest

from hpcq.cirq_bench import run_cirq_ghz_benchmark


def test_cirq_optional_returns_result():
    result = run_cirq_ghz_benchmark(n_qubits=3, repetitions=8)
    if not result.ok and result.error and "cirq import failed" in result.error:
        pytest.skip("cirq is optional in the CPU test environment")
    assert result.ok
    assert result.metrics["n_qubits"] == 3
