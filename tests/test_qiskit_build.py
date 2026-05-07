import pytest


qiskit = pytest.importorskip("qiskit")

from hpcq.qiskit_bench import build_entangling_circuit, run_qiskit_benchmark


def test_build_entangling_circuit_has_measurements():
    circuit = build_entangling_circuit(n_qubits=3, depth=2, measure=True)
    assert circuit.num_qubits == 3
    assert circuit.num_clbits == 3
    assert circuit.depth() > 0


def test_qiskit_cpu_benchmark_small():
    pytest.importorskip("qiskit_aer")
    result = run_qiskit_benchmark(n_qubits=2, depth=1, shots=32, device_choice="cpu")
    assert result.ok, result.error
    assert result.metrics["n_qubits"] == 2
