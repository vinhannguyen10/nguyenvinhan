from pathlib import Path

from hpcq.result import BenchmarkResult, append_jsonl, write_json


def test_benchmark_result_serializes(tmp_path: Path):
    result = BenchmarkResult(name="unit", ok=True, metrics={"x": 1})
    assert '"name": "unit"' in result.to_json()
    path = write_json(result, tmp_path / "result.json")
    assert path.exists()
    assert "unit" in path.read_text(encoding="utf-8")


def test_append_jsonl(tmp_path: Path):
    result = BenchmarkResult(name="unit", ok=True)
    path = append_jsonl(result, tmp_path / "suite.jsonl")
    append_jsonl(result, path)
    assert len(path.read_text(encoding="utf-8").strip().splitlines()) == 2
