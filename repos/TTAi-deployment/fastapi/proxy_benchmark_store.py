from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from proxy_benchmark_models import (
    BenchmarkRun,
    BenchmarkRunStatus,
    BenchmarkResultItem,
    BenchmarkRunSummary,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = WORKSPACE_ROOT / "state" / "proxy_benchmark.db"


def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                test_cases_json TEXT NOT NULL,
                results_json TEXT,
                summary_json TEXT,
                error_message TEXT,
                duration_seconds INTEGER DEFAULT 10
            )
        """)
        # Add column if missing (migration)
        try:
            conn.execute("ALTER TABLE benchmark_runs ADD COLUMN duration_seconds INTEGER DEFAULT 10")
        except sqlite3.OperationalError:
            pass  # column already exists
        conn.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_runs_started_at ON benchmark_runs(started_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_runs_status ON benchmark_runs(status)")
        conn.commit()
    finally:
        conn.close()


def save_benchmark_run(run: BenchmarkRun) -> None:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO benchmark_runs
            (run_id, started_at, completed_at, status, test_cases_json, results_json, summary_json, error_message, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.started_at.isoformat(),
                run.completed_at.isoformat() if run.completed_at else None,
                run.status.value,
                json.dumps([tc.dict() for tc in run.test_cases], ensure_ascii=False),
                json.dumps([r.dict() for r in run.results], ensure_ascii=False) if run.results else None,
                run.summary.json() if run.summary else None,
                run.error_message,
                run.duration_seconds,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def load_benchmark_run(run_id: str) -> Optional[BenchmarkRun]:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(
            "SELECT started_at, completed_at, status, test_cases_json, results_json, summary_json, error_message, duration_seconds "
            "FROM benchmark_runs WHERE run_id = ?",
            (run_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        started_at, completed_at, status_str, test_cases_json, results_json, summary_json, error_message, duration_seconds = row
        test_cases = []
        if test_cases_json:
            test_cases = json.loads(test_cases_json)
        results = []
        if results_json:
            results = json.loads(results_json)
        summary = None
        if summary_json:
            summary = json.loads(summary_json)
        return BenchmarkRun(
            run_id=run_id,
            started_at=datetime.fromisoformat(started_at),
            completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
            status=BenchmarkRunStatus(status_str),
            test_cases=test_cases,
            results=[BenchmarkResultItem(**r) for r in results] if results else [],
            summary=BenchmarkRunSummary(**summary) if summary else None,
            error_message=error_message,
            duration_seconds=duration_seconds or 10,
        )
    finally:
        conn.close()


def update_benchmark_run_status(run_id: str, status: BenchmarkRunStatus, error_message: Optional[str] = None) -> None:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        if status == BenchmarkRunStatus.COMPLETED:
            conn.execute(
                "UPDATE benchmark_runs SET status = ?, completed_at = ?, error_message = ? WHERE run_id = ?",
                (status.value, datetime.utcnow().isoformat(), error_message, run_id),
            )
        else:
            conn.execute(
                "UPDATE benchmark_runs SET status = ?, error_message = ? WHERE run_id = ?",
                (status.value, error_message, run_id),
            )
        conn.commit()
    finally:
        conn.close()


def update_benchmark_run_results(run_id: str, results: List[BenchmarkResultItem], summary: BenchmarkRunSummary) -> None:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            "UPDATE benchmark_runs SET results_json = ?, summary_json = ? WHERE run_id = ?",
            (
                json.dumps([r.dict() for r in results], ensure_ascii=False),
                summary.json(),
                run_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_benchmark_runs(limit: int = 10) -> List[BenchmarkRun]:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute(
            "SELECT run_id, started_at, completed_at, status, test_cases_json, results_json, summary_json, error_message "
            "FROM benchmark_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        runs = []
        for row in cur.fetchall():
            run_id, started_at, completed_at, status_str, test_cases_json, results_json, summary_json, error_message = row
            test_cases = []
            if test_cases_json:
                test_cases = json.loads(test_cases_json)
            results = []
            if results_json:
                results = json.loads(results_json)
            summary = None
            if summary_json:
                summary = json.loads(summary_json)
            runs.append(
                BenchmarkRun(
                    run_id=run_id,
                    started_at=datetime.fromisoformat(started_at),
                    completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
                    status=BenchmarkRunStatus(status_str),
                    test_cases=test_cases,
                    results=[BenchmarkResultItem(**r) for r in results] if results else [],
                    summary=BenchmarkRunSummary(**summary) if summary else None,
                    error_message=error_message,
                    duration_seconds=row[7] if len(row) > 7 else 10,
                )
            )
        return runs
    finally:
        conn.close()
