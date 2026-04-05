import os
import secrets
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
DEFAULT_DEV_ADMIN_TOKEN = "ttai-dev-admin-token"


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


def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate admin bearer token for control/admin routes."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    provided_token = credentials.credentials
    expected_token = get_configured_admin_token()

    if not secrets.compare_digest(provided_token, expected_token):
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return {
        "username": "admin",
        "is_admin": True,
        "auth_mode": get_admin_auth_mode(),
    }
