from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = WORKSPACE_ROOT / "benchmarks"
BENCHMARK_LATEST_PATH = BENCHMARK_DIR / "proxy_benchmark_latest.json"


def get_latest_proxy_benchmark() -> Dict[str, Any]:
    if not BENCHMARK_LATEST_PATH.exists():
        return {
            "available": False,
            "summary": {
                "last_run": None,
                "status": "not_run",
            },
            "results": None,
            "notes": [
                "Benchmark execution is planned for Phase C",
                "Use this placeholder to wire dashboard visibility first",
            ],
            "path": str(BENCHMARK_LATEST_PATH),
        }

    try:
        data = json.loads(BENCHMARK_LATEST_PATH.read_text(encoding="utf-8"))
        return {
            "available": True,
            "summary": data.get("summary", {}),
            "results": data.get("results"),
            "notes": data.get("notes", []),
            "path": str(BENCHMARK_LATEST_PATH),
        }
    except Exception as exc:
        return {
            "available": False,
            "summary": {
                "last_run": None,
                "status": "invalid",
            },
            "results": None,
            "notes": [f"Failed to load benchmark file: {exc}"],
            "path": str(BENCHMARK_LATEST_PATH),
        }
