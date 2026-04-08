"""Usage event storage helpers for TTAi FastAPI."""
from collections import Counter
import json
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USAGE_EVENTS_PATH = DATA_DIR / "usage_events.jsonl"
USAGE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)


def read_usage_events(limit: int = 100) -> List[Dict]:
    if not USAGE_EVENTS_PATH.exists():
        return []
    lines = USAGE_EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))



def filter_usage_events(
    events: List[Dict],
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    request_path: Optional[str] = None,
    tenant_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    quota_billable: Optional[bool] = None,
    billing_billable: Optional[bool] = None,
    billable_mode: Optional[str] = None,
):
    filtered = events
    if user_id:
        filtered = [e for e in filtered if (e.get("user_id") or "") == user_id]
    if status:
        filtered = [e for e in filtered if (e.get("status") or "") == status]
    if provider:
        filtered = [e for e in filtered if (e.get("provider") or "") == provider]
    if model:
        filtered = [e for e in filtered if (e.get("model") or "") == model]
    if request_path:
        filtered = [e for e in filtered if (e.get("request_path") or "") == request_path]
    if tenant_id:
        filtered = [e for e in filtered if (e.get("tenant_id") or "") == tenant_id]
    if api_key_id:
        filtered = [e for e in filtered if (e.get("api_key_id") or "") == api_key_id]
    if quota_billable is not None:
        filtered = [e for e in filtered if e.get("quota_billable") is quota_billable]
    if billing_billable is not None:
        filtered = [e for e in filtered if e.get("billing_billable") is billing_billable]
    if billable_mode:
        filtered = [e for e in filtered if (e.get("billable_mode") or "") == billable_mode]
    return filtered



def summarize_usage_events(events: List[Dict]) -> Dict:
    total = len(events)
    success = sum(1 for e in events if e.get("status") == "success")
    fallbacks = sum(1 for e in events if e.get("fallback_used"))
    total_tokens = sum(int(e.get("total_tokens_est") or 0) for e in events)
    avg_latency = round(sum(float(e.get("processing_time") or 0) for e in events) / total, 3) if total else 0
    providers = Counter(e.get("provider") or "unknown" for e in events)
    provider_types = Counter(e.get("provider_type") or "unknown" for e in events)
    users = Counter(e.get("user_id") or "anonymous" for e in events)
    statuses = Counter(e.get("status") or "unknown" for e in events)
    return {
        "total_events": total,
        "success_events": success,
        "error_events": total - success,
        "fallback_events": fallbacks,
        "total_tokens_est": total_tokens,
        "avg_processing_time": avg_latency,
        "top_providers": providers.most_common(10),
        "top_provider_types": provider_types.most_common(10),
        "top_users": users.most_common(10),
        "status_breakdown": dict(statuses),
    }
