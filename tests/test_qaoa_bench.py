from hpcq.qaoa_bench import maxcut_expectation_from_angles, run_qaoa_grid_benchmark


def test_qaoa_expectation_bounds():
    value = maxcut_expectation_from_angles(0.1, 0.2)
    assert 0.0 <= value <= 1.0


def test_qaoa_grid_smoke():
    result = run_qaoa_grid_benchmark(grid_size=4)
    assert result.ok
    assert result.metrics["num_evaluations"] == 16
    assert 0.0 <= result.metrics["best"]["expectation"] <= 1.0
