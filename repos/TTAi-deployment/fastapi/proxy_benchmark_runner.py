from __future__ import annotations

import asyncio
import statistics
import time
from typing import Dict, List, Optional, Tuple

import httpx

from proxy_benchmark_models import (
    BenchmarkTestCaseId,
    BenchmarkRun,
    BenchmarkRunStatus,
    BenchmarkResultItem,
    BenchmarkRunSummary,
)
from proxy_benchmark_store import update_benchmark_run_results, update_benchmark_run_status
from proxy_control_state import load_proxy_control_state

CHAT_PAYLOAD = {
    "messages": [
        {"role": "user", "content": "Xin chào, bạn có thể giới thiệu về TTAi không?"}
    ],
    "model": "gemma3:4b-remote",
    "stream": False,
}

TEST_CASE_MAP: Dict[BenchmarkTestCaseId, Dict[str, str]] = {
    BenchmarkTestCaseId.T1: {
        "target": "http://localhost:8000",
        "mode": None,
        "description": "Direct local 8000",
    },
    BenchmarkTestCaseId.T2: {
        "target": "http://100.89.201.7:8000",
        "mode": None,
        "description": "Direct remote 8000",
    },
    BenchmarkTestCaseId.T3: {
        "target": "http://localhost:8015",
        "mode": "stabilize",
        "description": "Proxy 8015 stabilize mode",
    },
    BenchmarkTestCaseId.T4: {
        "target": "http://localhost:8015",
        "mode": "remote-first",
        "description": "Proxy 8015 remote-first mode",
    },
    BenchmarkTestCaseId.T5: {
        "target": "http://localhost:8015",
        "mode": "stabilize",
        "description": "Proxy 8015 stabilize concurrency 2",
    },
    BenchmarkTestCaseId.T6: {
        "target": "http://localhost:8015",
        "mode": "remote-first",
        "description": "Proxy 8015 remote-first concurrency 2",
    },
}


async def _send_chat_request(client: httpx.AsyncClient, url: str) -> Tuple[float, bool]:
    start = time.perf_counter()
    try:
        resp = await client.post(f"{url}/chat/completions", json=CHAT_PAYLOAD, timeout=30.0)
        elapsed = time.perf_counter() - start
        success = resp.status_code == 200
        return elapsed * 1000, success
    except Exception:
        elapsed = time.perf_counter() - start
        return elapsed * 1000, False


async def _run_test_case(
    test_case_id: BenchmarkTestCaseId,
    concurrency: int,
    duration_seconds: int,
) -> BenchmarkResultItem:
    config = TEST_CASE_MAP[test_case_id]
    target = config["target"]
    mode = config["mode"]

    if mode:
        # temporarily set proxy mode for this test case
        from proxy_control_state import set_proxy_mode
        set_proxy_mode(mode)
        await asyncio.sleep(0.5)

    latencies: List[float] = []
    errors = 0
    total_requests = 0
    start_time = time.perf_counter()

    async with httpx.AsyncClient() as client:
        while time.perf_counter() - start_time < duration_seconds:
            tasks = [_send_chat_request(client, target) for _ in range(concurrency)]
            results = await asyncio.gather(*tasks, return_exceptions=False)
            for latency, success in results:
                latencies.append(latency)
                total_requests += 1
                if not success:
                    errors += 1
            await asyncio.sleep(0.05)

    elapsed = time.perf_counter() - start_time
    throughput = total_requests / elapsed if elapsed > 0 else 0.0
    error_rate = errors / total_requests if total_requests > 0 else 0.0

    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)
    p50 = latencies_sorted[n // 2] if n > 0 else 0.0
    p95 = latencies_sorted[int(n * 0.95)] if n > 0 else 0.0
    p99 = latencies_sorted[int(n * 0.99)] if n > 0 else 0.0

    return BenchmarkResultItem(
        test_case_id=test_case_id,
        target=target,
        mode=mode,
        concurrency=concurrency,
        requests=total_requests,
        errors=errors,
        latency_avg_ms=statistics.mean(latencies) if latencies else 0.0,
        latency_p50_ms=p50,
        latency_p95_ms=p95,
        latency_p99_ms=p99,
        throughput_rps=throughput,
        error_rate=error_rate,
    )


def _compute_summary(results: List[BenchmarkResultItem]) -> BenchmarkRunSummary:
    direct_local = next((r for r in results if r.test_case_id == BenchmarkTestCaseId.T1), None)
    direct_remote = next((r for r in results if r.test_case_id == BenchmarkTestCaseId.T2), None)
    proxy_stabilize = next((r for r in results if r.test_case_id == BenchmarkTestCaseId.T3), None)
    proxy_remote_first = next((r for r in results if r.test_case_id == BenchmarkTestCaseId.T4), None)

    direct_local_latency = direct_local.latency_avg_ms if direct_local else 0.0
    direct_remote_latency = direct_remote.latency_avg_ms if direct_remote else 0.0
    proxy_stabilize_latency = proxy_stabilize.latency_avg_ms if proxy_stabilize else 0.0
    proxy_remote_first_latency = proxy_remote_first.latency_avg_ms if proxy_remote_first else 0.0

    overhead_stabilize = proxy_stabilize_latency - min(direct_local_latency, direct_remote_latency)
    overhead_remote_first = proxy_remote_first_latency - min(direct_local_latency, direct_remote_latency)

    recommendation = ""
    if overhead_remote_first < 100:
        recommendation = "Proxy overhead < 100ms in remote-first mode — acceptable for production"
    elif overhead_remote_first < 300:
        recommendation = "Proxy overhead < 300ms — consider restoring 8015 with monitoring"
    else:
        recommendation = "Proxy overhead > 300ms — avoid restoring 8015 for now"

    return BenchmarkRunSummary(
        direct_local_latency=direct_local_latency,
        direct_remote_latency=direct_remote_latency,
        proxy_stabilize_latency=proxy_stabilize_latency,
        proxy_remote_first_latency=proxy_remote_first_latency,
        overhead_stabilize=overhead_stabilize,
        overhead_remote_first=overhead_remote_first,
        recommendation=recommendation,
    )


async def run_benchmark_suite(
    run: BenchmarkRun,
    progress_callback: Optional[callable] = None,
) -> None:
    try:
        update_benchmark_run_status(run.run_id, BenchmarkRunStatus.RUNNING)
        results: List[BenchmarkResultItem] = []
        total_cases = len(run.test_cases)
        for idx, test_case in enumerate(run.test_cases):
            if progress_callback:
                progress_callback((idx + 1) / total_cases)
            result = await _run_test_case(
                test_case.id,
                test_case.concurrency,
                run.duration_seconds,
            )
            results.append(result)
        summary = _compute_summary(results)
        update_benchmark_run_results(run.run_id, results, summary)
        update_benchmark_run_status(run.run_id, BenchmarkRunStatus.COMPLETED)
    except Exception as exc:
        update_benchmark_run_status(run.run_id, BenchmarkRunStatus.FAILED, str(exc))
        raise
