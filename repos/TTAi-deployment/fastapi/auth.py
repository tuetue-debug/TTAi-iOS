import os
import secrets
from fastapi import HTTPException, Depends, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)
DEFAULT_DEV_ADMIN_TOKEN = "ttai-dev-admin-token"
CONTROL_SESSION_COOKIE = "ttai_control_session"


def get_configured_admin_token() -> str:
    """Resolve admin bearer token from environment for control/admin routes."""
    return (
        os.getenv("TTAI_ADMIN_TOKEN")
        or os.getenv("FASTAPI_ADMIN_TOKEN")
        or DEFAULT_DEV_ADMIN_TOKEN
    )


def get_admin_auth_mode() -> str:
    token = get_configured_admin_token()
    if token == DEFAULT_DEV_ADMIN_TOKEN:
        return "development_fallback"
    return "env_configured"


def validate_admin_token(provided_token: str) -> bool:
    expected_token = get_configured_admin_token()
    return bool(provided_token) and secrets.compare_digest(provided_token, expected_token)


def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate admin bearer token for control/admin routes."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    provided_token = credentials.credentials
    if not validate_admin_token(provided_token):
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return {
        "username": "admin",
        "is_admin": True,
        "auth_mode": get_admin_auth_mode(),
    }


def get_current_control_user(control_session: str | None = Cookie(default=None, alias=CONTROL_SESSION_COOKIE)):
    """Validate cookie-backed control session for browser control UI routes."""
    if not control_session:
        raise HTTPException(status_code=401, detail="Control session required")

    if not validate_admin_token(control_session):
        raise HTTPException(status_code=403, detail="Invalid control session")

    return {
        "username": "admin",
        "is_admin": True,
        "auth_mode": get_admin_auth_mode(),
        "session_type": "cookie",
    }


def should_use_secure_cookie() -> bool:
    """Enable Secure cookies automatically outside local HTTP development."""
    env_value = (os.getenv("TTAI_CONTROL_COOKIE_SECURE") or "").strip().lower()
    if env_value in {"1", "true", "yes", "on"}:
        return True
    if env_value in {"0", "false", "no", "off"}:
        return False

    env_name = (os.getenv("ENV") or os.getenv("APP_ENV") or os.getenv("TTAI_ENV") or "").strip().lower()
    if env_name in {"prod", "production", "staging"}:
        return True

    return False
