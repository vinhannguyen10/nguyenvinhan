from hpcq.sysinfo import cgroup_limits, detect_container_runtime, system_report


def test_system_report_is_safe_without_hpc():
    result = system_report()
    assert result.ok
    assert "platform" in result.metrics
    assert "runtime" in result.metrics


def test_cgroup_limits_returns_version():
    info = cgroup_limits()
    assert "version" in info


def test_runtime_detection_has_guess():
    info = detect_container_runtime()
    assert "runtime_guess" in info
