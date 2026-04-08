"""
User Authentication Routes for TTAi API
"""
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from user_auth import (
    JWT_EXPIRATION_HOURS,
    REFRESH_TOKEN_EXPIRATION_DAYS,
    TokenResponse,
    USER_REPOSITORY,
    UserCreate,
    UserLogin,
    UserResponse,
    authenticate_user,
    create_access_token,
    create_refresh_token,
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
        refresh_token = create_refresh_token(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token["refresh_token"],
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            refresh_expires_in=REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600,
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
        refresh_token = create_refresh_token(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token["refresh_token"],
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            refresh_expires_in=REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600,
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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    all_sessions: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(payload: RefreshTokenRequest):
    """Issue a new access token from a valid refresh token."""
    try:
        user = USER_REPOSITORY.verify_refresh_token(payload.refresh_token)
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        USER_REPOSITORY.revoke_refresh_token(payload.refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token["refresh_token"],
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            refresh_expires_in=REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600,
            user=build_user_response(user),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(exc)}") from exc


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """Issue password reset token if the email exists."""
    try:
        result = USER_REPOSITORY.create_password_reset_token(email=str(payload.email))
        response = {
            "message": "If the account exists, password reset instructions have been prepared.",
            "issued": result.get("issued", False),
        }
        if result.get("issued"):
            response["reset_token"] = result.get("reset_token")
            response["expires_in"] = result.get("expires_in")
            response["expires_at"] = result.get("expires_at")
        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Forgot password failed: {str(exc)}") from exc


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    """Consume reset token and set a new password."""
    try:
        if len(payload.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        USER_REPOSITORY.consume_password_reset_token(
            token=payload.token,
            new_password=payload.new_password,
        )
        return {
            "message": "Password reset successfully",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reset password failed: {str(exc)}") from exc


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


@router.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_active_user)):
    """List refresh-token backed auth sessions for the current user."""
    return {
        "user_id": str(current_user["id"]),
        "items": USER_REPOSITORY.list_active_refresh_sessions(user_id=str(current_user["id"])),
    }


@router.post("/logout")
async def logout(
    payload: Optional[LogoutRequest] = None,
    current_user: dict = Depends(get_current_active_user),
):
    """Logout user. Supports current refresh token or all sessions revocation."""
    revoked = False
    revoked_count = 0

    if payload and payload.all_sessions:
        revoked_count = USER_REPOSITORY.revoke_all_refresh_tokens_for_user(user_id=str(current_user["id"]))
    elif payload and payload.refresh_token:
        revoked = USER_REPOSITORY.revoke_refresh_token(payload.refresh_token)
        revoked_count = 1 if revoked else 0

    return {
        "message": "Logged out successfully",
        "refresh_token_revoked": revoked,
        "revoked_sessions": revoked_count,
        "all_sessions": bool(payload.all_sessions) if payload else False,
    }


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
