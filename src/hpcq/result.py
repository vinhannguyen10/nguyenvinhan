from __future__ import annotations

import json
import platform
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkResult:
    name: str
    ok: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    timestamp_utc: float = field(default_factory=time.time)
    hostname: str = field(default_factory=platform.node)
    python: str = field(default_factory=platform.python_version)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_json(result: BenchmarkResult, path: str | Path) -> Path:
    p = ensure_parent(path)
    p.write_text(result.to_json() + "\n", encoding="utf-8")
    return p


def append_jsonl(result: BenchmarkResult, path: str | Path) -> Path:
    p = ensure_parent(path)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), sort_keys=True) + "\n")
    return p
