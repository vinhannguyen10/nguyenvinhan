from hpcq.hybrid_vqe import expectation_z, run_numpy_vqe


def test_expectation_z_known_values():
    assert abs(expectation_z(0.0) - 1.0) < 1e-9


def test_numpy_vqe_converges_toward_minus_one():
    result = run_numpy_vqe(steps=60, learning_rate=0.15, initial_theta=0.2)
    assert result.ok
    assert result.metrics["final_energy"] < -0.9
