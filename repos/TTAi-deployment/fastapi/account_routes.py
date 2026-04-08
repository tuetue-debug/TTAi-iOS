"""
Account Routes for TTAi API
Provides truthful account/profile surfaces separated from auth/session routes.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from user_auth import get_current_active_user
from user_routes import build_user_response
from user_auth import USER_REPOSITORY

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
