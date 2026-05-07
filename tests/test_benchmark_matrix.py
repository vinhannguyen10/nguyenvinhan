import json
from pathlib import Path

from hpcq.benchmark_matrix import add_overhead, collect_result_rows


def test_benchmark_matrix_collects_and_adds_overhead(tmp_path: Path):
    base = tmp_path / "baremetal_cpu"
    cont = tmp_path / "apptainer_gpu"
    base.mkdir()
    cont.mkdir()
    (base / "a.json").write_text(json.dumps({"name": "toy", "ok": True, "metrics": {"elapsed_seconds": 10.0}}))
    (cont / "a.json").write_text(json.dumps({"name": "toy", "ok": True, "metrics": {"elapsed_seconds": 11.0}}))
    rows = collect_result_rows([base, cont])
    enriched = add_overhead(rows, baseline_runtime="baremetal_cpu")
    overheads = [r.get("overhead_vs_baseline_percent") for r in enriched if r.get("runtime") == "apptainer_gpu"]
    assert overheads == [10.0]
