from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _flatten(prefix: str, value: Any, out: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(f"{prefix}.{k}" if prefix else str(k), v, out)
    elif isinstance(value, list):
        out[prefix] = json.dumps(value, ensure_ascii=False)
    else:
        out[prefix] = value


def collect_result_rows(base_dirs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in base_dirs:
        for path in sorted(base.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            row: dict[str, Any] = {
                "runtime": base.name,
                "experiment_dir": str(base),
                "file": str(path),
            }
            _flatten("", data, row)
            rows.append(row)
    return rows


def _runtime_elapsed_by_name(rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    for row in rows:
        name = str(row.get("name", ""))
        runtime = str(row.get("runtime", ""))
        elapsed = row.get("metrics.elapsed_seconds")
        if name and runtime and isinstance(elapsed, (int, float)):
            out[(runtime, name)] = float(elapsed)
    return out


def add_overhead(rows: list[dict[str, Any]], baseline_runtime: str = "baremetal_cpu") -> list[dict[str, Any]]:
    elapsed = _runtime_elapsed_by_name(rows)
    enriched = []
    for row in rows:
        row = dict(row)
        name = str(row.get("name", ""))
        runtime = str(row.get("runtime", ""))
        current = row.get("metrics.elapsed_seconds")
        baseline = elapsed.get((baseline_runtime, name))
        if isinstance(current, (int, float)) and baseline and baseline > 0 and runtime != baseline_runtime:
            row["overhead_vs_baseline_percent"] = (float(current) - baseline) / baseline * 100.0
        enriched.append(row)
    return enriched


def write_csv(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({k for row in rows for k in row})
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], output: Path) -> None:
    columns = [
        "runtime",
        "name",
        "ok",
        "metrics.elapsed_seconds",
        "metrics.samples_per_second",
        "metrics.approx_tflops",
        "metrics.world_size",
        "metrics.estimated_energy_wh",
        "overhead_vs_baseline_percent",
        "error",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "|".join(["---"] * len(columns)) + "|\n")
        for row in rows:
            f.write("| " + " | ".join(str(row.get(c, "")).replace("\n", " ") for c in columns) + " |\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create comparison CSV/Markdown from multiple runtime result folders.")
    parser.add_argument("results_dirs", nargs="+", help="Runtime result folders, e.g. results/baremetal_cpu results/apptainer_gpu")
    parser.add_argument("--baseline-runtime", default="baremetal_cpu")
    parser.add_argument("--csv", default="results/comparison/summary.csv")
    parser.add_argument("--md", default="results/comparison/summary.md")
    args = parser.parse_args()
    rows = collect_result_rows([Path(p) for p in args.results_dirs])
    rows = add_overhead(rows, baseline_runtime=args.baseline_runtime)
    if not rows:
        print("No JSON result files found.")
        return 1
    write_csv(rows, Path(args.csv))
    write_markdown(rows, Path(args.md))
    print(f"Wrote {len(rows)} rows to {args.csv} and {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
