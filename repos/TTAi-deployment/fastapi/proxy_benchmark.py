from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from proxy_benchmark_models import (
    BenchmarkRun,
    BenchmarkRunStatus,
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    BenchmarkStatusResponse,
    BenchmarkResultsResponse,
    BenchmarkListResponse,
    BenchmarkTestCase,
    BenchmarkTestCaseId,
)
from proxy_benchmark_runner import run_benchmark_suite
from proxy_benchmark_store import (
    save_benchmark_run,
    load_benchmark_run,
    update_benchmark_run_status,
    list_benchmark_runs,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = WORKSPACE_ROOT / "benchmarks"
BENCHMARK_LATEST_PATH = BENCHMARK_DIR / "proxy_benchmark_latest.json"

_ACTIVE_RUNS: Dict[str, asyncio.Task] = {}


def get_latest_proxy_benchmark() -> Dict[str, Any]:
    runs = list_benchmark_runs(limit=1)
    if not runs:
        return {
            "available": False,
            "summary": {
                "last_run": None,
                "status": "not_run",
                "overhead_ms": None,
                "recommendation": "Run benchmark to compare direct vs proxy performance",
            },
            "results": None,
            "notes": [
                "Benchmark execution is planned for Phase C",
                "Use this placeholder to wire dashboard visibility first",
            ],
            "path": str(BENCHMARK_LATEST_PATH),
        }
    latest = runs[0]
    return {
        "available": True,
        "summary": {
            "last_run": latest.started_at.isoformat(),
            "status": latest.status.value,
            "overhead_ms": latest.summary.overhead_remote_first if latest.summary else None,
            "recommendation": latest.summary.recommendation if latest.summary else "No recommendation yet",
        },
        "results": [r.dict() for r in latest.results] if latest.results else None,
        "notes": [],
        "path": str(BENCHMARK_LATEST_PATH),
    }


async def start_benchmark_run(request: BenchmarkRunRequest) -> BenchmarkRunResponse:
    test_cases = []
    for tc_id in request.test_cases:
        test_cases.append(
            BenchmarkTestCase(
                id=tc_id,
                target="",
                mode=None,
                concurrency=request.concurrency,
                description="",
            )
        )
    run = BenchmarkRun(
        test_cases=test_cases,
        duration_seconds=request.duration_seconds,
    )
    save_benchmark_run(run)
    task = asyncio.create_task(_run_benchmark_task(run))
    _ACTIVE_RUNS[run.run_id] = task
    return BenchmarkRunResponse(
        ok=True,
        run_id=run.run_id,
        message=f"Benchmark started with {len(test_cases)} test cases",
    )


async def _run_benchmark_task(run: BenchmarkRun) -> None:
    try:
        await run_benchmark_suite(run)
    finally:
        _ACTIVE_RUNS.pop(run.run_id, None)


def get_benchmark_status(run_id: str) -> Optional[BenchmarkStatusResponse]:
    run = load_benchmark_run(run_id)
    if not run:
        return None
    progress = 0.0
    if run.status == BenchmarkRunStatus.RUNNING:
        progress = 0.5
    elif run.status == BenchmarkRunStatus.COMPLETED:
        progress = 1.0
    return BenchmarkStatusResponse(
        run_id=run.run_id,
        status=run.status,
        progress=progress,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message,
    )


def get_benchmark_results(run_id: str) -> Optional[BenchmarkResultsResponse]:
    run = load_benchmark_run(run_id)
    if not run:
        return None
    return BenchmarkResultsResponse(
        run_id=run.run_id,
        status=run.status,
        results=run.results,
        summary=run.summary,
    )


def cancel_benchmark_run(run_id: str) -> bool:
    task = _ACTIVE_RUNS.get(run_id)
    if task:
        task.cancel()
        _ACTIVE_RUNS.pop(run_id, None)
    update_benchmark_run_status(run_id, BenchmarkRunStatus.CANCELLED, "Cancelled by operator")
    return True


def list_benchmark_runs_response(limit: int = 10) -> BenchmarkListResponse:
    runs = list_benchmark_runs(limit)
    status_responses = []
    for run in runs:
        progress = 0.0
        if run.status == BenchmarkRunStatus.RUNNING:
            progress = 0.5
        elif run.status == BenchmarkRunStatus.COMPLETED:
            progress = 1.0
        status_responses.append(
            BenchmarkStatusResponse(
                run_id=run.run_id,
                status=run.status,
                progress=progress,
                started_at=run.started_at,
                completed_at=run.completed_at,
                error_message=run.error_message,
            )
        )
    return BenchmarkListResponse(
        runs=status_responses,
        total=len(status_responses),
        limit=limit,
    )
