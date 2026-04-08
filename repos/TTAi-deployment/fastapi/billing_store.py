"""Billing and quota helpers for TTAi FastAPI."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from usage_store import read_usage_events

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BILLING_CONFIG_PATH = DATA_DIR / "billing_config.json"


def load_billing_config() -> Dict:
    if not BILLING_CONFIG_PATH.exists():
        return {
            "version": "0.0.0",
            "api_keys": {},
            "tenants": {},
            "user_rules": {
                "non_billable_prefixes": [
                    "metering_",
                    "smoke_",
                    "cost_estimation_",
                    "test_",
                    "debug_",
                    "internal_",
                ],
                "non_billable_exact": ["anonymous", "admin", "system"],
            },
        }
    try:
        with open(BILLING_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as exc:
        logger.warning("Failed to load billing config: %s, using defaults", exc)
        return {
            "version": "0.0.0",
            "api_keys": {},
            "tenants": {},
            "user_rules": {
                "non_billable_prefixes": [
                    "metering_",
                    "smoke_",
                    "cost_estimation_",
                    "test_",
                    "debug_",
                    "internal_",
                ],
                "non_billable_exact": ["anonymous", "admin", "system"],
            },
        }



def get_quota_policy(user_id: Optional[str], api_key_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict:
    user_id = (user_id or "anonymous").strip().lower()
    api_key_id = (api_key_id or "").strip().lower()
    tenant_id = (tenant_id or "").strip().lower()
    config = load_billing_config()
    quota_config = config.get("quota", {})

    if api_key_id:
        api_key_policy = quota_config.get("api_keys", {}).get(api_key_id)
        if api_key_policy is not None:
            policy = dict(api_key_policy)
            policy["quota_mode"] = "api_key_quota_v1"
            return policy

    if tenant_id:
        tenant_policy = quota_config.get("tenants", {}).get(tenant_id)
        if tenant_policy is not None:
            policy = dict(tenant_policy)
            policy["quota_mode"] = "tenant_quota_v1"
            return policy

    default_policy = dict(quota_config.get("default", {}))
    default_policy["quota_mode"] = "default_quota_v1"
    return default_policy



def get_quota_usage(events: List[Dict]) -> Dict:
    return {
        "requests": len([e for e in events if e.get("status") == "success"]),
        "tokens_est": sum(int(e.get("total_tokens_est") or 0) for e in events if e.get("status") == "success"),
        "estimated_cost": round(sum(float(e.get("estimated_cost") or 0.0) for e in events if e.get("status") == "success"), 8),
    }



def check_quota_allowance(user_id: Optional[str], api_key_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict:
    policy = get_quota_policy(user_id=user_id, api_key_id=api_key_id, tenant_id=tenant_id)
    if not policy.get("enabled", False):
        return {
            "allowed": True,
            "quota_enabled": False,
            "quota_mode": policy.get("quota_mode"),
            "policy": policy,
            "usage": {"requests": 0, "tokens_est": 0, "estimated_cost": 0.0},
            "remaining": {
                "requests": None,
                "tokens_est": None,
                "estimated_cost": None,
            },
            "reason": None,
        }

    all_events = read_usage_events(limit=5000)
    filtered_events = all_events
    if api_key_id:
        filtered_events = [e for e in filtered_events if (e.get("api_key_id") or "") == api_key_id]
    elif tenant_id:
        filtered_events = [e for e in filtered_events if (e.get("tenant_id") or "") == tenant_id]
    else:
        filtered_events = [e for e in filtered_events if (e.get("user_id") or "") == (user_id or "anonymous")]

    usage = get_quota_usage(filtered_events)
    max_requests = policy.get("max_requests")
    max_tokens_est = policy.get("max_tokens_est")
    max_estimated_cost = policy.get("max_estimated_cost")
    remaining = {
        "requests": max(max_requests - usage["requests"], 0) if max_requests is not None else None,
        "tokens_est": max(max_tokens_est - usage["tokens_est"], 0) if max_tokens_est is not None else None,
        "estimated_cost": round(max(float(max_estimated_cost) - usage["estimated_cost"], 0.0), 8) if max_estimated_cost is not None else None,
    }

    if max_requests is not None and usage["requests"] >= max_requests:
        return {
            "allowed": False,
            "quota_enabled": True,
            "quota_mode": policy.get("quota_mode"),
            "policy": policy,
            "usage": usage,
            "remaining": remaining,
            "reason": "max_requests_exceeded",
        }
    if max_tokens_est is not None and usage["tokens_est"] >= max_tokens_est:
        return {
            "allowed": False,
            "quota_enabled": True,
            "quota_mode": policy.get("quota_mode"),
            "policy": policy,
            "usage": usage,
            "remaining": remaining,
            "reason": "max_tokens_est_exceeded",
        }
    if max_estimated_cost is not None and usage["estimated_cost"] >= float(max_estimated_cost):
        return {
            "allowed": False,
            "quota_enabled": True,
            "quota_mode": policy.get("quota_mode"),
            "policy": policy,
            "usage": usage,
            "remaining": remaining,
            "reason": "max_estimated_cost_exceeded",
        }

    return {
        "allowed": True,
        "quota_enabled": True,
        "quota_mode": policy.get("quota_mode"),
        "policy": policy,
        "usage": usage,
        "remaining": remaining,
        "reason": None,
    }



def summarize_billing_usage(events: List[Dict]) -> Dict:
    if not events:
        return {
            "billable_events": 0,
            "non_billable_events": 0,
            "estimated_cost": 0.0,
            "tenant_breakdown": {},
            "user_breakdown": {},
            "provider_breakdown": {},
            "model_breakdown": {},
            "billable_mode_breakdown": {},
            "currency": "USD",
        }

    billable_events = 0
    non_billable_events = 0
    estimated_cost = 0.0
    tenant_costs = {}
    user_costs = {}
    provider_costs = {}
    model_costs = {}
    billable_mode_counts = {}

    for e in events:
        is_billable = e.get("billing_billable", False)
        cost = float(e.get("estimated_cost") or 0.0)
        billable_mode = e.get("billable_mode") or "unknown"

        billable_mode_counts[billable_mode] = billable_mode_counts.get(billable_mode, 0) + 1

        if is_billable:
            billable_events += 1
            estimated_cost += cost
        else:
            non_billable_events += 1

        tenant_id = e.get("tenant_id")
        if tenant_id:
            tenant_costs[tenant_id] = tenant_costs.get(tenant_id, 0.0) + cost

        user_id = e.get("user_id")
        if user_id:
            user_costs[user_id] = user_costs.get(user_id, 0.0) + cost

        provider = e.get("provider")
        if provider:
            provider_costs[provider] = provider_costs.get(provider, 0.0) + cost

        model = e.get("model")
        if model:
            model_costs[model] = model_costs.get(model, 0.0) + cost

    def sort_dict_by_value(data: Dict) -> Dict:
        return dict(sorted(data.items(), key=lambda item: item[1], reverse=True))

    return {
        "billable_events": billable_events,
        "non_billable_events": non_billable_events,
        "estimated_cost": round(estimated_cost, 8),
        "tenant_breakdown": sort_dict_by_value(tenant_costs),
        "user_breakdown": sort_dict_by_value(user_costs),
        "provider_breakdown": sort_dict_by_value(provider_costs),
        "model_breakdown": sort_dict_by_value(model_costs),
        "billable_mode_breakdown": sort_dict_by_value(billable_mode_counts),
        "currency": "USD",
    }
