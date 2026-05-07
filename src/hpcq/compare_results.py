from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def flatten(prefix: str, value: Any, output: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            flatten(f"{prefix}.{key}" if prefix else str(key), child, output)
    elif isinstance(value, list):
        output[prefix] = json.dumps(value, ensure_ascii=False)
    else:
        output[prefix] = value


def load_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in paths:
        for path in sorted(base.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            row: dict[str, Any] = {"file": str(path), "experiment_dir": str(base)}
            flatten("", data, row)
            rows.append(row)
    return rows


def write_csv(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    keys = sorted({key for row in rows for key in row})
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], output: Path) -> None:
    columns = [
        "name",
        "ok",
        "metrics.elapsed_seconds",
        "metrics.device",
        "metrics.requested_device",
        "metrics.world_size",
        "metrics.mean_power_watts",
        "error",
        "file",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        f.write("| " + " | ".join(columns) + " |\n")
        f.write("|" + "|".join(["---"] * len(columns)) + "|\n")
        for row in rows:
            f.write("| " + " | ".join(str(row.get(c, "")).replace("\n", " ") for c in columns) + " |\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Flatten benchmark JSON files into CSV and Markdown tables.")
    parser.add_argument("results_dirs", nargs="*", default=["results"])
    parser.add_argument("--csv", default="results/summary.csv")
    parser.add_argument("--md", default="results/summary.md")
    args = parser.parse_args()
    rows = load_rows([Path(p) for p in args.results_dirs])
    if not rows:
        print("No JSON results found.")
        return 1
    write_csv(rows, Path(args.csv))
    write_markdown(rows, Path(args.md))
    print(f"Wrote {len(rows)} rows to {args.csv} and {args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
