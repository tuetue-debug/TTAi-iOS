"""API key auth dependencies for TTAi FastAPI."""
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException

from api_key_store import API_KEY_REPOSITORY


async def get_api_key_identity(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """Resolve API key identity from X-API-Key or Bearer-style API key."""
    raw_api_key = x_api_key

    if not raw_api_key and authorization:
        if authorization.lower().startswith("bearer "):
            candidate = authorization.split(" ", 1)[1].strip()
            if candidate.startswith("sk-ttai-"):
                raw_api_key = candidate

    if not raw_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    return API_KEY_REPOSITORY.authenticate_api_key(raw_api_key)
