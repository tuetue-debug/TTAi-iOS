from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BenchmarkTestCaseId(str, Enum):
    T1 = "T1"  # direct local 8000
    T2 = "T2"  # direct remote 8000
    T3 = "T3"  # proxy 8015 stabilize
    T4 = "T4"  # proxy 8015 remote-first
    T5 = "T5"  # proxy 8015 stabilize concurrency 2
    T6 = "T6"  # proxy 8015 remote-first concurrency 2


class BenchmarkRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BenchmarkTestCase(BaseModel):
    id: BenchmarkTestCaseId
    target: str
    mode: Optional[str] = None
    concurrency: int = Field(default=1, ge=1, le=10)
    description: str = ""


class BenchmarkResultItem(BaseModel):
    test_case_id: BenchmarkTestCaseId
    target: str
    mode: Optional[str] = None
    concurrency: int
    requests: int = 0
    errors: int = 0
    latency_avg_ms: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0


class BenchmarkRunSummary(BaseModel):
    direct_local_latency: float = 0.0
    direct_remote_latency: float = 0.0
    proxy_stabilize_latency: float = 0.0
    proxy_remote_first_latency: float = 0.0
    overhead_stabilize: float = 0.0
    overhead_remote_first: float = 0.0
    recommendation: str = ""


class BenchmarkRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: BenchmarkRunStatus = BenchmarkRunStatus.PENDING
    test_cases: List[BenchmarkTestCase] = Field(default_factory=list)
    results: List[BenchmarkResultItem] = Field(default_factory=list)
    summary: Optional[BenchmarkRunSummary] = None
    error_message: Optional[str] = None
    duration_seconds: int = Field(default=10, ge=5, le=60)


class BenchmarkRunRequest(BaseModel):
    test_cases: List[BenchmarkTestCaseId] = Field(
        default_factory=lambda: [
            BenchmarkTestCaseId.T1,
            BenchmarkTestCaseId.T2,
            BenchmarkTestCaseId.T3,
            BenchmarkTestCaseId.T4,
        ]
    )
    concurrency: int = Field(default=1, ge=1, le=10)
    duration_seconds: int = Field(default=10, ge=5, le=60)


class BenchmarkRunResponse(BaseModel):
    ok: bool
    run_id: str
    message: str


class BenchmarkStatusResponse(BaseModel):
    run_id: str
    status: BenchmarkRunStatus
    progress: float = 0.0
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class BenchmarkResultsResponse(BaseModel):
    run_id: str
    status: BenchmarkRunStatus
    results: List[BenchmarkResultItem]
    summary: Optional[BenchmarkRunSummary] = None


class BenchmarkListResponse(BaseModel):
    runs: List[BenchmarkStatusResponse]
    total: int
    limit: int
