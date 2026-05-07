from __future__ import annotations

import argparse
import json
from pathlib import Path


def flatten(prefix, value, output):
    if isinstance(value, dict):
        for k, v in value.items():
            flatten(f"{prefix}.{k}" if prefix else k, v, output)
    else:
        output[prefix] = value


def load_results(results_dir: Path):
    rows = []
    for path in sorted(results_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        row = {"file": str(path)}
        flatten("", data, row)
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect JSON benchmark outputs into a CSV-like table.")
    parser.add_argument("results_dir", nargs="?", default="results")
    args = parser.parse_args()
    rows = load_results(Path(args.results_dir))
    if not rows:
        print("No JSON results found.")
        return 1
    keys = sorted({k for row in rows for k in row})
    print(",".join(keys))
    for row in rows:
        print(",".join(str(row.get(k, "")).replace(",", ";") for k in keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
