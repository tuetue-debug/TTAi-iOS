"""
Account Routes for TTAi API
Provides truthful account/profile/usage surfaces separated from auth/session routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from user_auth import get_current_active_user
from user_routes import build_user_response
from user_auth import USER_REPOSITORY
from usage_store import read_usage_events, filter_usage_events, summarize_usage_events
from billing_store import summarize_billing_usage, check_quota_allowance

router = APIRouter(prefix="/api/v1/account", tags=["account"])


class UpdateAccountProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


@router.get("/profile")
async def get_account_profile(current_user: dict = Depends(get_current_active_user)):
    """Return authenticated user's account profile."""
    return build_user_response(current_user)


@router.put("/profile")
async def update_account_profile(
    update_data: UpdateAccountProfileRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Update authenticated user's account profile."""
    try:
        updated_user = USER_REPOSITORY.update_user_profile(
            user_id=current_user["id"],
            name=update_data.name,
            email=update_data.email,
        )
        return build_user_response(updated_user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Account profile update failed: {str(exc)}") from exc


@router.get("/usage/summary")
async def get_account_usage_summary(
    limit: int = Query(default=500, ge=1, le=5000),
    current_user: dict = Depends(get_current_active_user),
):
    """Return summarized usage for the authenticated user."""
    try:
        events = read_usage_events(limit=limit)
        filtered = filter_usage_events(events, user_id=str(current_user["id"]))
        return {
            "user_id": str(current_user["id"]),
            "summary": summarize_usage_events(filtered),
            "count": len(filtered),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Account usage summary failed: {str(exc)}") from exc


@router.get("/usage/events")
async def get_account_usage_events(
    limit: int = Query(default=50, ge=1, le=500),
    status: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_active_user),
):
    """Return recent usage events for the authenticated user."""
    try:
        events = read_usage_events(limit=max(limit * 5, 200))
        filtered = filter_usage_events(
            events,
            user_id=str(current_user["id"]),
            status=status,
        )
        filtered = filtered[:limit]
        return {
            "user_id": str(current_user["id"]),
            "items": filtered,
            "count": len(filtered),
            "filters": {
                "status": status,
                "limit": limit,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Account usage events failed: {str(exc)}") from exc


@router.get("/billing/summary")
async def get_account_billing_summary(
    limit: int = Query(default=500, ge=1, le=5000),
    current_user: dict = Depends(get_current_active_user),
):
    """Return billing summary for the authenticated user."""
    try:
        events = read_usage_events(limit=limit)
        filtered = filter_usage_events(events, user_id=str(current_user["id"]))
        return {
            "user_id": str(current_user["id"]),
            "summary": summarize_billing_usage(filtered),
            "count": len(filtered),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Account billing summary failed: {str(exc)}") from exc


@router.get("/billing/limits")
async def get_account_billing_limits(
    current_user: dict = Depends(get_current_active_user),
):
    """Return quota/limit state for the authenticated user."""
    try:
        quota_status = check_quota_allowance(user_id=str(current_user["id"]))
        return {
            "user_id": str(current_user["id"]),
            "quota_status": quota_status,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Account billing limits failed: {str(exc)}") from exc
