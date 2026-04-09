"""Canonical usage/billing/quota read helpers for TTAi FastAPI.

Phase-1 truth layer over the JSONL ledger.
This centralizes scan window, filtering, and summary semantics so
admin/account/control surfaces stop drifting from one another.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from billing_store import check_quota_allowance, summarize_billing_usage
from usage_store import read_usage_events, filter_usage_events, summarize_usage_events


DEFAULT_SCAN_MULTIPLIER = 20
DEFAULT_SCAN_FLOOR = 5000


class UsageTruthService:
    def _scan_limit(self, limit: int, multiplier: int = DEFAULT_SCAN_MULTIPLIER, floor: int = DEFAULT_SCAN_FLOOR) -> int:
        return max(limit * multiplier, floor)

    def query_events(
        self,
        *,
        limit: int,
        scan_limit: Optional[int] = None,
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
    ) -> Dict:
        effective_scan_limit = scan_limit or self._scan_limit(limit)
        events = read_usage_events(limit=effective_scan_limit)
        filtered = filter_usage_events(
            events,
            user_id=user_id,
            status=status,
            provider=provider,
            model=model,
            request_path=request_path,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            quota_billable=quota_billable,
            billing_billable=billing_billable,
            billable_mode=billable_mode,
        )
        items = filtered[:limit]
        return {
            "items": items,
            "count": len(items),
            "matched": len(filtered),
            "scanned": effective_scan_limit,
            "filters": {
                "user_id": user_id,
                "status": status,
                "provider": provider,
                "model": model,
                "request_path": request_path,
                "tenant_id": tenant_id,
                "api_key_id": api_key_id,
                "quota_billable": quota_billable,
                "billing_billable": billing_billable,
                "billable_mode": billable_mode,
            },
        }

    def usage_summary(self, *, limit: int, **filters) -> Dict:
        result = self.query_events(limit=limit, **filters)
        return {
            **result,
            "summary": summarize_usage_events(result["items"]),
        }

    def billing_summary(self, *, limit: int, **filters) -> Dict:
        result = self.query_events(limit=limit, **filters)
        return {
            **result,
            "summary": summarize_billing_usage(result["items"]),
        }

    def quota_status(self, *, user_id: Optional[str], tenant_id: Optional[str] = None, api_key_id: Optional[str] = None) -> Dict:
        effective_user_id = user_id or "anonymous"
        quota_status = check_quota_allowance(
            user_id=effective_user_id,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
        )
        return {
            "scope": {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "api_key_id": api_key_id,
            },
            "quota_status": quota_status,
        }


USAGE_TRUTH = UsageTruthService()
