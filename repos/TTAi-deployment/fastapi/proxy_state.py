from __future__ import annotations

import ast
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from proxy_control_state import load_proxy_control_state

PROXY_PORT = 8015
PROXY_ROOT_URL = f"http://127.0.0.1:{PROXY_PORT}"
REQUEST_TIMEOUT = httpx.Timeout(5.0, connect=1.0)
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SIMPLE_PROXY_PATH = WORKSPACE_ROOT / "simple_proxy.py"

DEFAULT_ROLE_MAP = {
    "http://localhost:8000": {"id": "local-fastapi-8000", "role": "stabilization", "node": "vannt-home-zq", "weight": 20, "preferred": False, "enabled": True},
    "http://100.89.201.7:8000": {"id": "remote-workop-8000", "role": "primary-inference", "node": "vannt-work-op", "weight": 80, "preferred": True, "enabled": True},
    "http://localhost:8005": {"id": "local-hybrid-8005", "role": "optional-local-executor", "node": "vannt-home-zq", "weight": 0, "preferred": False, "enabled": False},
}


def _normalize_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


async def _fetch_json(url: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


async def probe_proxy_runtime() -> Dict[str, Any]:
    started = time.time()
    root = await _fetch_json(f"{PROXY_ROOT_URL}/")
    health = await _fetch_json(f"{PROXY_ROOT_URL}/health")
    latency_ms = round((time.time() - started) * 1000, 2)

    if root or health:
        backends = []
        if isinstance(root, dict):
            backends = root.get("backends") or []
        return {
            "live": True,
            "source": "live-probe",
            "status": (health or {}).get("status", "running"),
            "service_name": (root or {}).get("service", "TTAiSimpleProxy"),
            "version": (root or {}).get("version", "unknown"),
            "port": (root or {}).get("port", PROXY_PORT),
            "mode": "unknown",
            "preferred_backend": None,
            "hedge_enabled": (root or {}).get("hedge_enabled"),
            "hedge_delay_seconds": (root or {}).get("hedge_delay_seconds"),
            "healthy_backend_count": (health or {}).get("healthy_count", 0),
            "backend_count": (health or {}).get("total_backends", len(backends)),
            "backends": backends,
            "probe_latency_ms": latency_ms,
            "health": health or {},
        }

    return {
        "live": False,
        "source": "unavailable",
        "status": "stopped",
        "service_name": "TTAiSimpleProxy",
        "version": "unknown",
        "port": PROXY_PORT,
        "mode": "stabilize",
        "preferred_backend": "remote-workop-8000",
        "hedge_enabled": False,
        "hedge_delay_seconds": None,
        "healthy_backend_count": 0,
        "backend_count": 0,
        "backends": [],
        "probe_latency_ms": latency_ms,
        "health": {},
    }


def _extract_backends_from_code() -> List[str]:
    if not SIMPLE_PROXY_PATH.exists():
        return []

    text = SIMPLE_PROXY_PATH.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"BACKENDS\s*:\s*List\[str\]\s*=\s*\[(.*?)\]", text, re.S)
    if not match:
        match = re.search(r"BACKENDS\s*=\s*\[(.*?)\]", text, re.S)
    if not match:
        return []

    raw_body = "[" + match.group(1) + "]"
    try:
        parsed = ast.literal_eval(raw_body)
        if isinstance(parsed, list):
            return [_normalize_url(str(item)) for item in parsed if item]
    except Exception:
        return []
    return []


async def _probe_backend(url: str) -> Dict[str, Any]:
    normalized = _normalize_url(url)
    started = time.time()
    root = await _fetch_json(f"{normalized}/")
    latency_ms = round((time.time() - started) * 1000, 2)

    if root is not None:
        return {
            "healthy": True,
            "latency_ms": latency_ms,
            "error": None,
            "identity": root,
        }

    return {
        "healthy": False,
        "latency_ms": None,
        "error": "Probe failed",
        "identity": None,
    }


async def get_proxy_backends_state() -> Dict[str, Any]:
    runtime = await probe_proxy_runtime()
    control_state = load_proxy_control_state()
    control_backends = control_state.get("backends", {})
    live_backends = [_normalize_url(item) for item in (runtime.get("backends") or [])]
    code_backends = _extract_backends_from_code()

    source = "live-probe" if live_backends else "code-derived"
    urls = live_backends or code_backends
    if live_backends and code_backends and live_backends != code_backends:
        source = "mixed"

    items: List[Dict[str, Any]] = []
    for url in urls:
        meta = DEFAULT_ROLE_MAP.get(url, {
            "id": re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-"),
            "role": "unknown",
            "node": "unknown",
            "weight": 0,
            "preferred": False,
            "enabled": True,
        })
        backend_id = meta["id"]
        overlay = control_backends.get(backend_id, {}) if isinstance(control_backends, dict) else {}
        probe = await _probe_backend(url)
        item = {
            "id": backend_id,
            "url": url,
            "role": meta["role"],
            "node": meta["node"],
            "enabled": overlay.get("enabled", meta["enabled"]),
            "healthy": probe["healthy"],
            "preferred": bool(overlay.get("weight", meta["weight"])) and backend_id == "remote-workop-8000" if control_state.get("mode") == "remote-first" else meta["preferred"],
            "weight": overlay.get("weight", meta["weight"]),
            "latency_ms": probe["latency_ms"],
            "error": probe["error"],
            "identity": probe["identity"],
        }
        items.append(item)

    healthy = sum(1 for item in items if item.get("healthy"))
    enabled = sum(1 for item in items if item.get("enabled"))
    return {
        "summary": {
            "count": len(items),
            "healthy": healthy,
            "enabled": enabled,
            "source": source,
        },
        "items": items,
        "control_state": control_state,
    }


async def get_proxy_runtime_state() -> Dict[str, Any]:
    runtime = await probe_proxy_runtime()
    backends = await get_proxy_backends_state()
    control_state = backends.get("control_state", {})
    preferred = next((item["id"] for item in backends.get("items", []) if item.get("preferred")), runtime.get("preferred_backend"))
    return {
        "summary": {
            "service_status": runtime.get("status", "unknown"),
            "service_name": runtime.get("service_name", "TTAiSimpleProxy"),
            "port": runtime.get("port", PROXY_PORT),
            "mode": control_state.get("mode", runtime.get("mode", "stabilize")),
            "preferred_backend": preferred,
            "hedge_enabled": control_state.get("hedge", {}).get("enabled", runtime.get("hedge_enabled", False)),
            "hedge_delay_seconds": control_state.get("hedge", {}).get("delay_seconds", runtime.get("hedge_delay_seconds")),
            "backend_count": backends.get("summary", {}).get("count", 0),
            "healthy_backend_count": backends.get("summary", {}).get("healthy", 0),
            "last_probe": int(time.time()),
            "probe_latency_ms": runtime.get("probe_latency_ms"),
        },
        "runtime": {
            "live": runtime.get("live", False),
            "source": backends.get("summary", {}).get("source", runtime.get("source", "unknown")),
            "version": runtime.get("version", "unknown"),
            "backends": runtime.get("backends") or [item["url"] for item in backends.get("items", [])],
            "health": runtime.get("health", {}),
            "control_state": control_state,
        },
    }
