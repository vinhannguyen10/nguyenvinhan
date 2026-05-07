from pathlib import Path

from hpcq.run_suite import run_suite


def test_run_suite_dry_run(tmp_path: Path):
    results = run_suite(output_dir=tmp_path, dry_run=True)
    assert len(results) == 1
    assert results[0].ok
    assert (tmp_path / "dry_run.json").exists()
    assert (tmp_path / "suite.jsonl").exists()
