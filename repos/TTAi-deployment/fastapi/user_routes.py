"""
User Authentication Routes for TTAi API
"""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from user_auth import (
    JWT_EXPIRATION_HOURS,
    TokenResponse,
    USER_REPOSITORY,
    UserCreate,
    UserLogin,
    UserResponse,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def build_user_response(user: Dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
        is_active=user["is_active"],
        role=user["role"],
    )


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register new user."""
    try:
        user = create_user(user_data)
        access_token = create_access_token(user)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=build_user_response(user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(exc)}") from exc


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user."""
    try:
        user = authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token = create_access_token(user)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=build_user_response(user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(exc)}") from exc


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_active_user)):
    """Get current user profile."""
    return build_user_response(current_user)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Update user profile."""
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
        raise HTTPException(status_code=500, detail=f"Update failed: {str(exc)}") from exc


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.put("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
):
    """Change user password."""
    try:
        if len(password_data.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters",
            )

        if not verify_password(password_data.current_password, current_user["password_hash"]):
            raise HTTPException(status_code=401, detail="Current password is incorrect")

        USER_REPOSITORY.update_password(
            user_id=current_user["id"],
            password_hash=hash_password(password_data.new_password),
        )
        return {"message": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(exc)}") from exc


@router.post("/logout")
async def logout():
    """Logout user (client-side token invalidation)."""
    return {"message": "Logged out successfully"}


# Deprecated auth/account crossover endpoints kept temporarily for compatibility.
@router.get("/api-keys")
async def get_api_keys(current_user: dict = Depends(get_current_active_user)):
    """Deprecated. Use /api/v1/account/api-keys instead."""
    return {
        "deprecated": True,
        "message": "Use /api/v1/account/api-keys instead of /api/v1/auth/api-keys.",
        "replacement": "/api/v1/account/api-keys",
        "user_id": str(current_user["id"]),
    }


@router.get("/usage/stats")
async def get_usage_stats(
    period: str = "30d",
    current_user: dict = Depends(get_current_active_user),
):
    """Deprecated. Use /api/v1/account/usage/summary instead."""
    return {
        "deprecated": True,
        "message": "Use /api/v1/account/usage/summary instead of /api/v1/auth/usage/stats.",
        "replacement": "/api/v1/account/usage/summary",
        "period": period,
        "user_id": str(current_user["id"]),
    }


@router.get("/billing/summary")
async def get_billing_summary(current_user: dict = Depends(get_current_active_user)):
    """Deprecated. Use /api/v1/account/billing/summary instead."""
    return {
        "deprecated": True,
        "message": "Use /api/v1/account/billing/summary instead of /api/v1/auth/billing/summary.",
        "replacement": "/api/v1/account/billing/summary",
        "user_id": str(current_user["id"]),
    }
