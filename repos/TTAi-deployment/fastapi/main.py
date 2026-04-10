from fastapi import FastAPI, HTTPException, Depends, Query, Header, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import os
import httpx
import json
import logging
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import asynccontextmanager

# Import services
from ollama_service import ollama_service
from load_balancer import load_balancer, QueryComplexity, ProviderType
from query_classifier import query_classifier, ClassificationResult
from model_manager import model_manager, startup_warmup, shutdown_cleanup
from analytics import analytics_tracker
from auth import get_current_admin_user, get_current_control_user, validate_admin_token, CONTROL_SESSION_COOKIE, should_use_secure_cookie
from user_auth import UserCreate, UserLogin, authenticate_user, create_user as create_portal_user, create_access_token, create_refresh_token, verify_token, USER_REPOSITORY
from user_routes import router as user_auth_router
from account_routes import router as account_router
from usage_store import read_usage_events, filter_usage_events, summarize_usage_events
from billing_store import load_billing_config, check_quota_allowance, summarize_billing_usage
from usage_truth import USAGE_TRUTH
from proxy_state import get_proxy_runtime_state, get_proxy_backends_state
from proxy_benchmark import get_latest_proxy_benchmark
from api_key_auth import get_api_key_identity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USAGE_EVENTS_PATH = DATA_DIR / "usage_events.jsonl"
BILLING_CONFIG_PATH = DATA_DIR / "billing_config.json"
LEARN_QUEUE_PATH = DATA_DIR / "learn_queue.jsonl"
ARCHIVE_DIR = DATA_DIR / "archive"
USAGE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)

def write_usage_event(event: Dict):
    with open(USAGE_EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


CONTROL_ACTIONS_LOG_PATH = BASE_DIR / "data" / "control_actions.jsonl"


def write_control_action(action: Dict):
    CONTROL_ACTIONS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTROL_ACTIONS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(action, ensure_ascii=False) + "\n")


def read_control_actions(limit: int = 100) -> List[Dict]:
    if not CONTROL_ACTIONS_LOG_PATH.exists():
        return []
    lines = CONTROL_ACTIONS_LOG_PATH.read_text(encoding="utf-8").splitlines()
    actions = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            actions.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(actions))

COST_RULES_PER_1K_TOKENS = {
    "cliproxy/gpt-mini": 0.0003,
    "cliproxy/gemini-pro": 0.00035,
    "cliproxy/deepseek-chat": 0.00027,
    "gpt-5.2": 0.0020,
    "gemma3:4b": 0.0,
    "qwen3:4b": 0.0,
    "deepseek-r1:8b": 0.0,
}


def estimate_cost(model_name: Optional[str], total_tokens_est: int, provider_type: Optional[str]) -> Dict:
    model_name = model_name or ""
    provider_type = provider_type or "unknown"

    if not total_tokens_est:
        return {
            "estimated_cost": 0.0,
            "cost_estimate_mode": "zero_no_tokens"
        }

    matched_rate = COST_RULES_PER_1K_TOKENS.get(model_name)
    if matched_rate is not None:
        return {
            "estimated_cost": round((total_tokens_est / 1000.0) * matched_rate, 8),
            "cost_estimate_mode": "static_per_1k_tokens_v1"
        }

    if provider_type in ["ollama_local", "ollama_remote"]:
        return {
            "estimated_cost": 0.0,
            "cost_estimate_mode": "assumed_zero_self_hosted_v1"
        }

    if provider_type == "cli_proxy":
        fallback_rate = 0.0003
        return {
            "estimated_cost": round((total_tokens_est / 1000.0) * fallback_rate, 8),
            "cost_estimate_mode": "static_cli_proxy_fallback_v1"
        }

    return {
        "estimated_cost": None,
        "cost_estimate_mode": None
    }


def classify_billable_flags(user_id: Optional[str], api_key_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict:
    user_id = (user_id or "anonymous").strip().lower()
    api_key_id = (api_key_id or "").strip().lower()
    tenant_id = (tenant_id or "").strip().lower()
    
    config = load_billing_config()
    
    # 1. API key rule (highest priority)
    if api_key_id:
        api_key_info = config.get("api_keys", {}).get(api_key_id)
        if api_key_info is not None:
            billable = api_key_info.get("billable", True)
            return {
                "quota_billable": billable,
                "billing_billable": billable,
                "billable_mode": "api_key_config_v3",
            }
        # Fallback to prefix rule if not in config
        is_non_billable_api_key = any(api_key_id.startswith(prefix) for prefix in ("test_", "internal_", "dev_"))
        return {
            "quota_billable": not is_non_billable_api_key,
            "billing_billable": not is_non_billable_api_key,
            "billable_mode": "api_key_rule_v2",
        }
    
    # 2. Tenant rule
    if tenant_id:
        tenant_info = config.get("tenants", {}).get(tenant_id)
        if tenant_info is not None:
            billable = tenant_info.get("billable", True)
            return {
                "quota_billable": billable,
                "billing_billable": billable,
                "billable_mode": "tenant_config_v3",
            }
        # Fallback to prefix rule if not in config
        is_non_billable_tenant = any(tenant_id.startswith(prefix) for prefix in ("internal_", "dev_", "test_", "staging_"))
        return {
            "quota_billable": not is_non_billable_tenant,
            "billing_billable": not is_non_billable_tenant,
            "billable_mode": "tenant_rule_v2",
        }
    
    # 3. User ID rule
    user_rules = config.get("user_rules", {})
    non_billable_prefixes = tuple(user_rules.get("non_billable_prefixes", []))
    non_billable_exact = set(user_rules.get("non_billable_exact", []))
    
    is_non_billable = user_id in non_billable_exact or any(user_id.startswith(prefix) for prefix in non_billable_prefixes)
    
    return {
        "quota_billable": not is_non_billable,
        "billing_billable": not is_non_billable,
        "billable_mode": "user_id_rule_v1",
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    # Startup
    logger.info("TTAi Super Model Hybrid API starting up...")
    
    # Warm up models
    warmup_results = await startup_warmup()
    logger.info(f"Model warm-up complete: {sum(1 for v in warmup_results.values() if v)}/{len(warmup_results)} successful")
    
    # Check Ollama health
    is_healthy = await ollama_service.health_check()
    if is_healthy:
        logger.info("Ollama service is healthy")
    else:
        logger.warning("Ollama service is not available")
    
    yield
    
    # Shutdown
    logger.info("TTAi Super Model Hybrid API shutting down...")
    await shutdown_cleanup()
    ollama_service.cleanup()

app = FastAPI(
    title="TTAi Super Model Hybrid API", 
    version="2.0.0",
    lifespan=lifespan
)

# Include user/account routes
app.include_router(user_auth_router)
app.include_router(account_router)

# Mount Control Dashboard
CONTROL_FRONTEND_PATH = BASE_DIR.parent / "control-frontend"
if CONTROL_FRONTEND_PATH.exists():
    app.mount("/control", StaticFiles(directory=str(CONTROL_FRONTEND_PATH), html=True), name="control")
    logger.info(f"Mounted control frontend at /control from {CONTROL_FRONTEND_PATH}")
else:
    logger.warning(f"Control frontend directory not found: {CONTROL_FRONTEND_PATH}")

# Mount API Portal Preview
API_PORTAL_DIST_PATH = BASE_DIR / "portal" / "dist"
API_PORTAL_ASSETS_PATH = API_PORTAL_DIST_PATH / "assets"
API_PORTAL_FAVICON_PATH = API_PORTAL_DIST_PATH / "favicon.svg"
if API_PORTAL_DIST_PATH.exists():
    app.mount("/portal", StaticFiles(directory=str(API_PORTAL_DIST_PATH), html=True), name="api-portal")
    if API_PORTAL_ASSETS_PATH.exists():
        app.mount("/assets", StaticFiles(directory=str(API_PORTAL_ASSETS_PATH)), name="api-portal-assets")
    logger.info(f"Mounted API portal preview at /portal from {API_PORTAL_DIST_PATH}")
else:
    logger.warning(f"API portal dist directory not found: {API_PORTAL_DIST_PATH}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONTROL_LOGIN_HTML = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>TTAi Control Login</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; background:#0b1020; color:#e5e7eb; display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }
    .card { width:min(420px, 92vw); background:#131a2b; border:1px solid #24304a; border-radius:16px; padding:28px; box-shadow:0 20px 60px rgba(0,0,0,.35); }
    h1 { margin:0 0 8px; font-size:24px; }
    p { color:#94a3b8; margin:0 0 20px; }
    input { width:100%; box-sizing:border-box; padding:12px 14px; border-radius:10px; border:1px solid #334155; background:#0f172a; color:#e5e7eb; margin-bottom:12px; }
    button { width:100%; padding:12px 14px; border:none; border-radius:10px; background:#2563eb; color:white; font-weight:600; cursor:pointer; }
    .error { color:#fca5a5; min-height:20px; margin-top:10px; }
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>TTAi Control</h1>
    <p>Enter admin token to open the control console.</p>
    <form id=\"login-form\">
      <input id=\"token\" type=\"password\" placeholder=\"Admin token\" autocomplete=\"current-password\" required />
      <button type=\"submit\">Open Control Dashboard</button>
      <div id=\"error\" class=\"error\"></div>
    </form>
  </div>
  <script>
    document.getElementById('login-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const token = document.getElementById('token').value;
      const errorEl = document.getElementById('error');
      errorEl.textContent = '';
      const response = await fetch('/control-auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });
      if (response.ok) {
        window.location.href = '/control/';
        return;
      }
      const payload = await response.json().catch(() => ({}));
      errorEl.textContent = payload.detail || 'Login failed';
    });
  </script>
</body>
</html>
"""

PORTAL_SESSION_COOKIE = "ttai_portal_session"
PORTAL_REFRESH_COOKIE = "ttai_portal_refresh"


def build_portal_user_response(user: Dict) -> Dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"].isoformat() if hasattr(user.get("created_at"), "isoformat") else user.get("created_at"),
        "updated_at": user["updated_at"].isoformat() if hasattr(user.get("updated_at"), "isoformat") else user.get("updated_at"),
        "is_active": user.get("is_active", True),
        "role": user.get("role", "user"),
        "email_verified": user.get("email_verified", False),
        "email_verified_at": user["email_verified_at"].isoformat() if user.get("email_verified_at") and hasattr(user.get("email_verified_at"), "isoformat") else user.get("email_verified_at"),
    }


def resolve_portal_user(portal_session: str | None) -> Dict:
    if not portal_session:
        raise HTTPException(status_code=401, detail="Portal session required")
    try:
        payload = verify_token(portal_session)
        user = USER_REPOSITORY.get_user_by_id(str(payload.get("sub")))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid portal session") from exc
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid portal user")
    return user


class ControlLoginRequest(BaseModel):
    token: str


class ControlActionRequest(BaseModel):
    action: str
    target: Optional[str] = None
    timeout: int = 30


class PortalSignupRequest(BaseModel):
    name: str
    email: str
    password: str


class PortalLoginRequest(BaseModel):
    email: str
    password: str


def clear_learn_queue_file() -> Dict:
    if not LEARN_QUEUE_PATH.exists():
        return {"ok": True, "message": "Learn queue already empty", "cleared_items": 0}

    existing_lines = LEARN_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
    cleared_items = len([line for line in existing_lines if line.strip()])
    if cleared_items == 0:
        LEARN_QUEUE_PATH.write_text("", encoding="utf-8")
        return {"ok": True, "message": "Learn queue already empty", "cleared_items": 0}

    backup_path = ARCHIVE_DIR / f"learn_queue_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl.bak"
    backup_path.write_text("\n".join(existing_lines) + ("\n" if existing_lines else ""), encoding="utf-8")
    LEARN_QUEUE_PATH.write_text("", encoding="utf-8")
    return {
        "ok": True,
        "message": f"Cleared {cleared_items} learn queue items",
        "cleared_items": cleared_items,
        "backup_path": str(backup_path),
    }


def archive_usage_events_file() -> Dict:
    if not USAGE_EVENTS_PATH.exists() or USAGE_EVENTS_PATH.stat().st_size == 0:
        return {"ok": True, "message": "No usage events to archive", "archived_lines": 0}

    existing_lines = USAGE_EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    archived_lines = len([line for line in existing_lines if line.strip()])
    if archived_lines == 0:
        USAGE_EVENTS_PATH.write_text("", encoding="utf-8")
        return {"ok": True, "message": "No usage events to archive", "archived_lines": 0}

    archive_path = ARCHIVE_DIR / f"usage_events_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    archive_path.write_text("\n".join(existing_lines) + ("\n" if existing_lines else ""), encoding="utf-8")
    USAGE_EVENTS_PATH.write_text("", encoding="utf-8")
    return {
        "ok": True,
        "message": f"Archived {archived_lines} usage events",
        "archived_lines": archived_lines,
        "archive_path": str(archive_path),
    }


CONTROL_ACTION_DEFINITIONS = {
    "provider_enable": {
        "group": "providers",
        "requires_target": True,
        "sensitivity": "medium",
        "label": "Enable Provider",
    },
    "provider_disable": {
        "group": "providers",
        "requires_target": True,
        "sensitivity": "high",
        "label": "Disable Provider",
    },
    "model_warmup": {
        "group": "models",
        "requires_target": True,
        "sensitivity": "low",
        "label": "Warm Up Model",
    },
    "model_warmup_all": {
        "group": "models",
        "requires_target": False,
        "sensitivity": "medium",
        "label": "Warm Up All Models",
    },
    "health_refresh": {
        "group": "system",
        "requires_target": False,
        "sensitivity": "low",
        "label": "Refresh Health",
    },
    "clear_learn_queue": {
        "group": "system",
        "requires_target": False,
        "sensitivity": "high",
        "label": "Clear Learn Queue",
    },
    "archive_events": {
        "group": "system",
        "requires_target": False,
        "sensitivity": "medium",
        "label": "Archive Usage Events",
    },
}


def is_control_action_allowed(action_name: str) -> bool:
    destructive_actions = {"clear_learn_queue", "archive_events"}
    if action_name not in destructive_actions:
        return True

    env_value = (os.getenv("TTAI_ENABLE_DESTRUCTIVE_CONTROL_ACTIONS") or "").strip().lower()
    return env_value in {"1", "true", "yes", "on"}


def get_available_control_actions() -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {"providers": [], "models": [], "system": []}
    for action_name, meta in CONTROL_ACTION_DEFINITIONS.items():
        grouped.setdefault(meta["group"], []).append({
            "action": action_name,
            **meta,
            "enabled": is_control_action_allowed(action_name),
        })
    return grouped


def build_control_response(ok: bool, action: str, message: str, **extra) -> Dict:
    return {
        "ok": ok,
        "action": action,
        "message": message,
        **extra,
    }

@app.get("/control-login", response_class=HTMLResponse)
async def control_login_page():
    return CONTROL_LOGIN_HTML

@app.post("/control-auth/login")
async def control_auth_login(payload: ControlLoginRequest, response: Response):
    if not validate_admin_token(payload.token):
        raise HTTPException(status_code=403, detail="Invalid admin token")

    response.set_cookie(
        key=CONTROL_SESSION_COOKIE,
        value=payload.token,
        httponly=True,
        samesite="lax",
        secure=should_use_secure_cookie(),
        max_age=60 * 60 * 12,
        path="/",
    )
    return {"ok": True}

@app.post("/control-auth/logout")
async def control_auth_logout(response: Response, current_user = Depends(get_current_control_user)):
    response.delete_cookie(CONTROL_SESSION_COOKIE, path="/")
    return {"ok": True}

@app.get("/control-auth/session")
async def control_auth_session(current_user = Depends(get_current_control_user)):
    return {
        "ok": True,
        "user": current_user,
        "cookie": {
            "name": CONTROL_SESSION_COOKIE,
            "secure": should_use_secure_cookie(),
            "samesite": "lax",
        },
    }


@app.post("/auth/signup")
async def portal_auth_signup(payload: PortalSignupRequest, response: Response):
    user = create_portal_user(UserCreate(name=payload.name, email=payload.email, password=payload.password))
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    response.set_cookie(
        key=PORTAL_SESSION_COOKIE,
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=should_use_secure_cookie(),
        max_age=60 * 60 * 24,
        path="/",
    )
    response.set_cookie(
        key=PORTAL_REFRESH_COOKIE,
        value=refresh_token["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=should_use_secure_cookie(),
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return {"ok": True, "user": build_portal_user_response(user)}


@app.post("/auth/login")
async def portal_auth_login(payload: PortalLoginRequest, response: Response):
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    response.set_cookie(
        key=PORTAL_SESSION_COOKIE,
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=should_use_secure_cookie(),
        max_age=60 * 60 * 24,
        path="/",
    )
    response.set_cookie(
        key=PORTAL_REFRESH_COOKIE,
        value=refresh_token["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=should_use_secure_cookie(),
        max_age=60 * 60 * 24 * 30,
        path="/",
    )
    return {"ok": True, "user": build_portal_user_response(user)}


@app.post("/auth/logout")
async def portal_auth_logout(response: Response, portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE), portal_refresh: str | None = Cookie(default=None, alias=PORTAL_REFRESH_COOKIE)):
    if portal_refresh:
        try:
            USER_REPOSITORY.revoke_refresh_token(portal_refresh)
        except Exception:
            pass
    response.delete_cookie(PORTAL_SESSION_COOKIE, path="/")
    response.delete_cookie(PORTAL_REFRESH_COOKIE, path="/")
    return {"ok": True}


@app.get("/auth/me")
async def portal_auth_me(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    return {"ok": True, "user": build_portal_user_response(user)}


@app.get("/portal-api/overview")
async def portal_account_overview(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    user_id = str(user["id"])
    usage = USAGE_TRUTH.usage_summary(limit=500, user_id=user_id)
    billing = USAGE_TRUTH.billing_summary(limit=500, user_id=user_id)
    limits = USAGE_TRUTH.quota_status(user_id=user_id)
    api_keys = []
    try:
        from api_key_store import API_KEY_REPOSITORY
        api_keys = API_KEY_REPOSITORY.list_user_api_keys(user_id)
    except Exception:
        api_keys = []
    return {
        "ok": True,
        "user": build_portal_user_response(user),
        "usage": usage,
        "billing": billing,
        "limits": limits,
        "api_keys": {
            "items": api_keys,
            "count": len(api_keys),
        },
    }


class PortalCreateApiKeyRequest(BaseModel):
    name: str
    scopes: List[str] = []


@app.get("/portal-api/api-keys")
async def portal_list_api_keys(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    from api_key_store import API_KEY_REPOSITORY
    items = API_KEY_REPOSITORY.list_user_api_keys(str(user["id"]))
    return {"ok": True, "items": items, "count": len(items)}


@app.post("/portal-api/api-keys")
async def portal_create_api_key(payload: PortalCreateApiKeyRequest, portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    from api_key_store import API_KEY_REPOSITORY
    created = API_KEY_REPOSITORY.create_api_key(user_id=str(user["id"]), name=payload.name, scopes=payload.scopes)
    return {"ok": True, "item": created}


@app.delete("/portal-api/api-keys/{key_id}")
async def portal_revoke_api_key(key_id: str, portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    from api_key_store import API_KEY_REPOSITORY
    revoked = API_KEY_REPOSITORY.revoke_api_key(user_id=str(user["id"]), api_key_id=key_id)
    return {"ok": True, "item": revoked}


@app.get("/portal-api/docs")
async def portal_docs_payload(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    return {
        "ok": True,
        "user": build_portal_user_response(user),
        "base_url": "https://api.tuetue.vn",
        "quickstart": {
            "curl": "curl -X POST https://api.tuetue.vn/chat -H 'Authorization: Bearer sk-ttai-...' -H 'Content-Type: application/json' -d '{\"message\":\"Hello from TTAi\"}'",
            "javascript": "const res = await fetch('https://api.tuetue.vn/chat', { method: 'POST', headers: { 'Authorization': 'Bearer sk-ttai-...', 'Content-Type': 'application/json' }, body: JSON.stringify({ message: 'Hello from TTAi' }) });",
            "python": "import requests\nrequests.post('https://api.tuetue.vn/chat', headers={'Authorization': 'Bearer sk-ttai-...'}, json={'message': 'Hello from TTAi'})",
        },
        "endpoints": [
            {"name": "Chat", "method": "POST", "path": "/chat", "description": "Primary chat/completion endpoint for TTAi API consumers."},
            {"name": "Auth Me", "method": "GET", "path": "/auth/me", "description": "Returns current portal user session."},
            {"name": "List API Keys", "method": "GET", "path": "/portal-api/api-keys", "description": "List API keys for the authenticated portal user."},
            {"name": "Create API Key", "method": "POST", "path": "/portal-api/api-keys", "description": "Create a new user-scoped API key."},
            {"name": "Usage Summary", "method": "GET", "path": "/api/v1/account/usage/summary", "description": "Read usage summary for the authenticated account."},
        ],
    }


class PortalProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


@app.get("/portal-api/profile")
async def portal_profile_get(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    return {"ok": True, "user": build_portal_user_response(user)}


@app.put("/portal-api/profile")
async def portal_profile_update(payload: PortalProfileUpdateRequest, portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    updated_user = USER_REPOSITORY.update_user_profile(user_id=str(user["id"]), name=payload.name, email=payload.email)
    return {"ok": True, "user": build_portal_user_response(updated_user)}


@app.get("/portal-api/social-auth/providers")
async def portal_social_auth_providers(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    linked = {item["provider"]: item for item in USER_REPOSITORY.list_oauth_accounts(user_id=str(user["id"]))}
    providers = []
    for provider in ["google", "github", "apple"]:
        providers.append({
            "provider": provider,
            "enabled": False,
            "status": "linked" if provider in linked else "available",
            "linked_email": linked.get(provider, {}).get("provider_email"),
            "message": "OAuth callback wiring not configured yet" if provider not in linked else "Provider linked in local auth store",
        })
    return {"ok": True, "items": providers}


class PortalSocialLinkRequest(BaseModel):
    provider: str
    provider_user_id: str
    provider_email: Optional[str] = None


@app.post("/portal-api/social-auth/link")
async def portal_social_auth_link(payload: PortalSocialLinkRequest, portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)):
    user = resolve_portal_user(portal_session)
    provider = (payload.provider or "").strip().lower()
    if provider not in {"google", "github", "apple"}:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    linked = USER_REPOSITORY.link_oauth_account(
        user_id=str(user["id"]),
        provider=provider,
        provider_user_id=payload.provider_user_id,
        provider_email=payload.provider_email,
    )
    return {"ok": True, "item": linked}

# Models
class ChatRequest(BaseModel):
    message: str
    model: str = ""  # Auto-select if empty
    use_memory: bool = True  # Use RAG memory retrieval
    user_id: str = "anonymous"  # User identifier for analytics
    tenant_id: Optional[str] = None
    api_key_id: Optional[str] = None

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    model_used: str
    provider_type: str
    processing_time: float
    classification: Dict
    needs_context: bool

class OllamaRequest(BaseModel):
    prompt: str
    model: str = "gemma3:4b"
    stream: bool = False

class OllamaResponse(BaseModel):
    response: str
    model: str
    created_at: str
    done: bool

class OllamaChatRequest(BaseModel):
    messages: List[dict]
    model: str = "gemma3:4b"
    stream: bool = False

class ModelInfo(BaseModel):
    name: str
    model: str
    size: int
    details: dict

class ClassificationRequest(BaseModel):
    query: str

class ClassificationResponse(BaseModel):
    complexity: str
    confidence: float
    language: str
    needs_context: bool
    estimated_tokens: int
    features: Dict[str, float]

class LoadBalancerMetrics(BaseModel):
    total_requests: int
    provider_distribution: Dict[str, Dict]
    health_status: Dict[str, bool]

class ModelStatusResponse(BaseModel):
    name: str
    status: str
    last_warmup: Optional[float]
    warmup_time: Optional[float]
    error_count: int
    is_ready: bool

# Route group constants
API_V1_CHAT = "/api/v1/chat"
API_V1_CLASSIFY = "/api/v1/classify"
API_V1_CLASSIFY_BATCH = "/api/v1/classify/batch"
API_V1_SYSTEM_HEALTH = "/api/v1/system/health"
API_V1_SYSTEM_HEALTH_DETAILED = "/api/v1/system/health/detailed"
API_V1_SYSTEM_LOADBALANCER_METRICS = "/api/v1/system/loadbalancer/metrics"
API_V1_SYSTEM_LOADBALANCER_PROVIDERS = "/api/v1/system/loadbalancer/providers"
API_V1_SYSTEM_LOADBALANCER_DISABLE = "/api/v1/system/loadbalancer/providers/{provider_name}/disable"
API_V1_SYSTEM_LOADBALANCER_ENABLE = "/api/v1/system/loadbalancer/providers/{provider_name}/enable"
API_V1_MODELS_STATUS = "/api/v1/models/status"
API_V1_MODELS_STATUS_ITEM = "/api/v1/models/status/{model_name}"
API_V1_MODELS_WARMUP_ITEM = "/api/v1/models/warmup/{model_name}"
API_V1_MODELS_WARMUP_ALL = "/api/v1/models/warmup/all"
API_V1_USERS = "/api/v1/users"
API_V1_OLLAMA_MODELS = "/api/v1/ollama/models"
API_V1_OLLAMA_HEALTH = "/api/v1/ollama/health"
API_V1_OLLAMA_GENERATE = "/api/v1/ollama/generate"
API_V1_OLLAMA_CHAT = "/api/v1/ollama/chat"
API_V1_HYBRID_CHAT = "/api/v1/hybrid/chat"
API_V1_TEST_CLASSIFICATION = "/api/v1/test/classification"
API_V1_TEST_LOADBALANCER = "/api/v1/test/loadbalancer"
API_V1_ADMIN_USAGE_EVENTS = "/api/v1/admin/usage/events"
API_V1_ADMIN_USAGE_SUMMARY = "/api/v1/admin/usage/summary"
API_V1_ADMIN_USAGE_USER = "/api/v1/admin/usage/users/{target_user_id}"
API_V1_ADMIN_USAGE_BILLING_SUMMARY = "/api/v1/admin/usage/billing-summary"
API_V1_ADMIN_OVERVIEW = "/api/v1/admin/overview"
API_V1_ADMIN_ERRORS_SUMMARY = "/api/v1/admin/errors/summary"
API_V1_ADMIN_QUOTA_BLOCKED = "/api/v1/admin/quota/blocked"
API_V1_ADMIN_BILLING_CONFIG = "/api/v1/admin/billing/config"
API_V1_ADMIN_QUOTA_STATUS = "/api/v1/admin/quota/status"
API_V1_ADMIN_QUOTA_STATUS_USER = "/api/v1/admin/quota/status/users/{target_user_id}"

# Health check
@app.get("/")
async def root(request: Request):
    host = (request.headers.get("host") or "").split(":", 1)[0].lower()
    if host == "console.tuetue.vn" and API_PORTAL_DIST_PATH.exists():
        return FileResponse(API_PORTAL_DIST_PATH / "index.html")
    return {
        "status": "ok", 
        "service": "TTAi Super Model Hybrid API", 
        "version": "2.0.0",
        "features": [
            "Load Balancing (60/30/10)",
            "Query Classification",
            "Model Warm-up",
            "Ollama Integration",
            "CLI Proxy Fallback"
        ]
    }

@app.get("/favicon.svg", include_in_schema=False)
async def portal_favicon(request: Request):
    host = (request.headers.get("host") or "").split(":", 1)[0].lower()
    if host == "console.tuetue.vn" and API_PORTAL_FAVICON_PATH.exists():
        return FileResponse(API_PORTAL_FAVICON_PATH)
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/health")
@app.get(API_V1_SYSTEM_HEALTH)
async def health():
    """Comprehensive health check"""
    ollama_healthy = await ollama_service.health_check()
    
    # Check model warm-up status
    model_status = model_manager.get_all_status()
    warm_models = sum(1 for status in model_status.values() if status and status["is_ready"])
    
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "services": {
            "ollama": ollama_healthy,
            "models_warm": f"{warm_models}/{len(model_status)}",
            "load_balancer": True,
            "query_classifier": True
        },
        "timestamp": json.dumps(datetime.now().isoformat())
    }

@app.get("/health/detailed")
@app.get(API_V1_SYSTEM_HEALTH_DETAILED)
async def health_detailed():
    """Detailed health check with all components"""
    ollama_healthy = await ollama_service.health_check()
    model_status = model_manager.get_all_status()
    
    return {
        "ollama": {
            "healthy": ollama_healthy,
            "models": await ollama_service.list_models() if ollama_healthy else []
        },
        "models": model_status,
        "load_balancer": load_balancer.get_metrics(),
        "system": {
            "version": "2.0.0",
            "uptime": "TODO",  # Would need to track startup time
            "memory_usage": "TODO"
        }
    }

# AI Chat endpoint with Load Balancing
@app.post("/api/chat", response_model=ChatResponse)
@app.post(API_V1_CHAT, response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    x_ttai_api_key_id: Optional[str] = Header(default=None),
    x_ttai_tenant_id: Optional[str] = Header(default=None),
):
    """
    Intelligent chat endpoint with load balancing and query classification
    
    Features:
    1. Query classification (Simple/Medium/Complex)
    2. Load balancing (60/30/10 strategy)
    3. Model warm-up integration
    4. Memory retrieval (RAG) if needed
    """
    import time
    start_time = time.time()
    request_id = str(uuid.uuid4())
    request_api_key_id = request.api_key_id or x_ttai_api_key_id
    request_tenant_id = request.tenant_id or x_ttai_tenant_id
    resolved_user_id = request.user_id or "anonymous"

    api_key_identity = None
    x_api_key_value = http_request.headers.get("x-api-key")
    auth_header = http_request.headers.get("authorization")
    if x_api_key_value or (auth_header and auth_header.lower().startswith("bearer sk-ttai-")):
        api_key_identity = await get_api_key_identity(
            x_api_key=x_api_key_value,
            authorization=auth_header,
        )
        request_api_key_id = api_key_identity["api_key"].get("id")
        if resolved_user_id == "anonymous":
            resolved_user_id = str(api_key_identity["user"].get("id"))

    fallback_used = False
    final_status = "success"
    final_http_status = 200
    provider = None
    provider_type = "unknown"
    classification = None
    response_text = ""
    error_detail = None
    
    try:
        # Step 1: Classify query
        classification = query_classifier.classify(request.message)
        logger.info(f"Query classified as {classification.complexity.value} "
                   f"(confidence: {classification.confidence:.2f})")

        # Step 1.5: Quota enforcement
        user_id = resolved_user_id
        quota_check = check_quota_allowance(
            user_id=user_id,
            api_key_id=request_api_key_id,
            tenant_id=request_tenant_id,
        )
        if not quota_check["allowed"]:
            processing_time = time.time() - start_time
            final_status = "quota_exceeded"
            final_http_status = 429
            error_detail = quota_check["reason"]
            input_tokens_est = estimate_tokens(request.message)
            cost_info = estimate_cost(None, input_tokens_est, provider_type)
            billable_flags = classify_billable_flags(user_id=user_id, api_key_id=request_api_key_id, tenant_id=request_tenant_id)
            usage_event = {
                "event_id": str(uuid.uuid4()),
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "channel": "api_chat",
                "request_path": "/api/chat",
                "user_id": user_id,
                "tenant_id": request_tenant_id,
                "api_key_id": request_api_key_id,
                "provider": None,
                "model": None,
                "provider_type": provider_type,
                "classification_complexity": classification.complexity.value if classification else None,
                "classification_confidence": classification.confidence if classification else None,
                "classification_language": classification.language if classification else None,
                "needs_context": classification.needs_context if classification else None,
                "input_chars": len(request.message or ""),
                "output_chars": 0,
                "input_tokens_est": input_tokens_est,
                "output_tokens_est": 0,
                "total_tokens_est": input_tokens_est,
                "token_count_mode": "estimated_chars_div_4",
                "estimated_cost": cost_info["estimated_cost"],
                "cost_estimate_mode": cost_info["cost_estimate_mode"],
                "quota_billable": billable_flags["quota_billable"],
                "billing_billable": billable_flags["billing_billable"],
                "billable_mode": billable_flags["billable_mode"],
                "quota_enabled": quota_check["quota_enabled"],
                "quota_mode": quota_check["quota_mode"],
                "quota_reason": quota_check["reason"],
                "quota_policy": quota_check["policy"],
                "quota_usage": quota_check["usage"],
                "processing_time": processing_time,
                "fallback_used": False,
                "fallback_target": None,
                "status": final_status,
                "http_status": final_http_status,
                "error": error_detail,
                "source": "repos/TTAi-deployment/fastapi/main.py"
            }
            write_usage_event(usage_event)
            raise HTTPException(status_code=429, detail={
                "error": "quota_exceeded",
                "reason": quota_check["reason"],
                "quota_mode": quota_check["quota_mode"],
                "usage": quota_check["usage"],
                "policy": quota_check["policy"],
            })
        
        # Step 2: Memory retrieval if needed
        context = None
        if request.use_memory and classification.needs_context:
            # TODO: Implement RAG memory retrieval
            logger.info("Query needs context, but RAG not fully implemented yet")
            # context = await memory_retrieval(request.message)
        
        # Step 3: Select provider using load balancer
        if request.model:
            # Use specified model
            provider = next(
                (p for provider_list in load_balancer.providers.values() 
                 for p in provider_list if p.name == request.model),
                None
            )
            if not provider:
                raise HTTPException(status_code=400, detail=f"Model {request.model} not found")
        else:
            # Auto-select based on classification
            provider = await load_balancer.select_provider(classification)
        
        # Step 4: Check if model is warm
        if not model_manager.is_model_ready(provider.name):
            logger.warning(f"Model {provider.name} is not warm, attempting warm-up...")
            await model_manager.warmup_model(provider.name, timeout=20)
        
        # Step 5: Process with selected provider
        response_text = ""
        provider_type = provider.provider_type.value
        
        if provider.provider_type.value in ["ollama_local", "ollama_remote"]:
            # Use Ollama with fallback on failure
            try:
                result = await ollama_service.generate(
                    model=provider.model,
                    prompt=request.message,
                    stream=False
                )
                response_text = result.get("response", "")
            except Exception as e:
                logger.error(f"Ollama failed for {provider.name}: {e}")
                
                # Try fallback to CLI Proxy
                fallback_provider = None
                for p_type in [ProviderType.CLI_PROXY, ProviderType.GPT_DIRECT]:
                    for p in load_balancer.providers[p_type]:
                        if p.enabled and await load_balancer.check_health(p):
                            fallback_provider = p
                            break
                    if fallback_provider:
                        break
                
                if fallback_provider:
                    logger.info(f"Falling back to {fallback_provider.name}")
                    fallback_used = True
                    provider = fallback_provider
                    provider_type = provider.provider_type.value
                    
                    # Retry with fallback provider
                    if provider.provider_type.value == "cli_proxy":
                        # Use CLI Proxy
                        default_cli_proxy = "https://127.0.0.1:8317"
                        cli_proxy_url = os.getenv("CLI_PROXY_URL", default_cli_proxy).rstrip("/") or default_cli_proxy
                        cli_proxy_key = os.getenv("CLI_PROXY_API_KEY", "").strip()
                        
                        headers = {"Content-Type": "application/json"}
                        if cli_proxy_key:
                            headers["Authorization"] = f"Bearer {cli_proxy_key}"
                        
                        proxy_model = provider.endpoint
                        if proxy_model.startswith("cliproxy/"):
                            proxy_model = proxy_model.split("/", 1)[1]
                        if proxy_model == "gpt-5.1-codex":
                            proxy_model = "gpt-mini"
                        
                        async with httpx.AsyncClient(timeout=provider.timeout, verify=False) as client:
                            response = await client.post(
                                f"{cli_proxy_url}/v1/chat/completions",
                                json={
                                    "model": proxy_model,
                                    "messages": [{"role": "user", "content": request.message}],
                                    "stream": False
                                },
                                headers=headers
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                            else:
                                response_text = f"CLIProxy error: {response.status_code}"
                    else:
                        # GPT direct or other providers
                        response_text = f"[{provider.name} response placeholder - Ollama fallback]"
                else:
                    response_text = "Xin lỗi, hệ thống AI tạm thời gặp sự cố. Vui lòng thử lại sau."
            
        elif provider.provider_type.value == "cli_proxy":
            # Use CLI Proxy
            default_cli_proxy = "https://127.0.0.1:8317"
            cli_proxy_url = os.getenv("CLI_PROXY_URL", default_cli_proxy).rstrip("/") or default_cli_proxy
            cli_proxy_key = os.getenv("CLI_PROXY_API_KEY", "").strip()
            
            headers = {"Content-Type": "application/json"}
            if cli_proxy_key:
                headers["Authorization"] = f"Bearer {cli_proxy_key}"
            
            proxy_model = provider.endpoint
            if proxy_model.startswith("cliproxy/"):
                proxy_model = proxy_model.split("/", 1)[1]
            if proxy_model == "gpt-5.1-codex":
                proxy_model = "gpt-mini"
            
            async with httpx.AsyncClient(timeout=provider.timeout, verify=False) as client:
                response = await client.post(
                    f"{cli_proxy_url}/v1/chat/completions",
                    json={
                        "model": proxy_model,
                        "messages": [{"role": "user", "content": request.message}],
                        "stream": False
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "No response")
                else:
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"CLIProxy error: {response.text}"
                    )
        
        else:
            # GPT direct or other providers
            # TODO: Implement direct GPT API call
            response_text = f"[{provider.name} response placeholder]"
        
        # Step 6: Calculate processing time
        processing_time = time.time() - start_time
        
        # Step 7: Track analytics
        user_id = resolved_user_id
        response_data = {
            "response": response_text,
            "processing_time": processing_time,
            "model_used": provider.name,
            "provider_type": provider_type
        }
        
        analytics_tracker.track_interaction(
            user_id=user_id,
            request=request.message,
            response_data=response_data,
            classification=classification.to_dict()
        )

        input_tokens_est = estimate_tokens(request.message)
        output_tokens_est = estimate_tokens(response_text)
        total_tokens_est = input_tokens_est + output_tokens_est
        cost_info = estimate_cost(provider.model, total_tokens_est, provider_type)
        billable_flags = classify_billable_flags(user_id=user_id, api_key_id=request_api_key_id, tenant_id=request_tenant_id)
        usage_event = {
            "event_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": "api_chat",
            "request_path": "/api/chat",
            "user_id": user_id,
            "tenant_id": request_tenant_id,
            "api_key_id": request_api_key_id,
            "provider": provider.name,
            "model": provider.model,
            "provider_type": provider_type,
            "classification_complexity": classification.complexity.value,
            "classification_confidence": classification.confidence,
            "classification_language": classification.language,
            "needs_context": classification.needs_context,
            "input_chars": len(request.message or ""),
            "output_chars": len(response_text or ""),
            "input_tokens_est": input_tokens_est,
            "output_tokens_est": output_tokens_est,
            "total_tokens_est": total_tokens_est,
            "token_count_mode": "estimated_chars_div_4",
            "estimated_cost": cost_info["estimated_cost"],
            "cost_estimate_mode": cost_info["cost_estimate_mode"],
            "quota_billable": billable_flags["quota_billable"],
            "billing_billable": billable_flags["billing_billable"],
            "billable_mode": billable_flags["billable_mode"],
            "processing_time": processing_time,
            "fallback_used": fallback_used,
            "fallback_target": provider.name if fallback_used else None,
            "status": final_status,
            "http_status": final_http_status,
            "error": error_detail,
            "source": "repos/TTAi-deployment/fastapi/main.py"
        }
        write_usage_event(usage_event)
        
        # Step 8: Return response
        return ChatResponse(
            response=response_text,
            model_used=provider.name,
            provider_type=provider_type,
            processing_time=processing_time,
            classification=classification.to_dict(),
            needs_context=classification.needs_context
        )
        
    except HTTPException as e:
        if final_status == "quota_exceeded" or e.status_code == 429:
            raise
        final_status = "error"
        final_http_status = e.status_code
        error_detail = str(e.detail)
        processing_time = time.time() - start_time
        user_id = resolved_user_id
        input_tokens_est = estimate_tokens(request.message)
        total_tokens_est = input_tokens_est
        event_model = provider.model if provider else None
        cost_info = estimate_cost(event_model, total_tokens_est, provider_type)
        billable_flags = classify_billable_flags(user_id=user_id, api_key_id=request_api_key_id, tenant_id=request_tenant_id)
        usage_event = {
            "event_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": "api_chat",
            "request_path": "/api/chat",
            "user_id": user_id,
            "tenant_id": request_tenant_id,
            "api_key_id": request_api_key_id,
            "provider": provider.name if provider else None,
            "model": event_model,
            "provider_type": provider_type,
            "classification_complexity": classification.complexity.value if classification else None,
            "classification_confidence": classification.confidence if classification else None,
            "classification_language": classification.language if classification else None,
            "needs_context": classification.needs_context if classification else None,
            "input_chars": len(request.message or ""),
            "output_chars": 0,
            "input_tokens_est": input_tokens_est,
            "output_tokens_est": 0,
            "total_tokens_est": total_tokens_est,
            "token_count_mode": "estimated_chars_div_4",
            "estimated_cost": cost_info["estimated_cost"],
            "cost_estimate_mode": cost_info["cost_estimate_mode"],
            "quota_billable": billable_flags["quota_billable"],
            "billing_billable": billable_flags["billing_billable"],
            "billable_mode": billable_flags["billable_mode"],
            "processing_time": processing_time,
            "fallback_used": fallback_used,
            "fallback_target": provider.name if fallback_used and provider else None,
            "status": final_status,
            "http_status": final_http_status,
            "error": error_detail,
            "source": "repos/TTAi-deployment/fastapi/main.py"
        }
        write_usage_event(usage_event)
        raise
    except Exception as e:
        final_status = "error"
        final_http_status = 500
        error_detail = str(e)
        processing_time = time.time() - start_time
        user_id = resolved_user_id
        input_tokens_est = estimate_tokens(request.message)
        total_tokens_est = input_tokens_est
        event_model = provider.model if provider else None
        cost_info = estimate_cost(event_model, total_tokens_est, provider_type)
        billable_flags = classify_billable_flags(user_id=user_id, api_key_id=request_api_key_id, tenant_id=request_tenant_id)
        usage_event = {
            "event_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": "api_chat",
            "request_path": "/api/chat",
            "user_id": user_id,
            "tenant_id": request_tenant_id,
            "api_key_id": request_api_key_id,
            "provider": provider.name if provider else None,
            "model": event_model,
            "provider_type": provider_type,
            "classification_complexity": classification.complexity.value if classification else None,
            "classification_confidence": classification.confidence if classification else None,
            "classification_language": classification.language if classification else None,
            "needs_context": classification.needs_context if classification else None,
            "input_chars": len(request.message or ""),
            "output_chars": 0,
            "input_tokens_est": input_tokens_est,
            "output_tokens_est": 0,
            "total_tokens_est": total_tokens_est,
            "token_count_mode": "estimated_chars_div_4",
            "estimated_cost": cost_info["estimated_cost"],
            "cost_estimate_mode": cost_info["cost_estimate_mode"],
            "quota_billable": billable_flags["quota_billable"],
            "billing_billable": billable_flags["billing_billable"],
            "billable_mode": billable_flags["billable_mode"],
            "processing_time": processing_time,
            "fallback_used": fallback_used,
            "fallback_target": provider.name if fallback_used and provider else None,
            "status": final_status,
            "http_status": final_http_status,
            "error": error_detail,
            "source": "repos/TTAi-deployment/fastapi/main.py"
        }
        write_usage_event(usage_event)
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# Admin usage metering read endpoints
@app.get("/api/admin/usage/events")
@app.get(API_V1_ADMIN_USAGE_EVENTS)
async def admin_usage_events(
    limit: int = Query(default=100, ge=1, le=1000),
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
    result = USAGE_TRUTH.query_events(
        limit=limit,
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
    return {
        "count": result["count"],
        "matched": result["matched"],
        "scanned": result["scanned"],
        "filters": result["filters"],
        "events": result["items"],
    }


@app.get("/api/admin/usage/summary")
@app.get(API_V1_ADMIN_USAGE_SUMMARY)
async def admin_usage_summary(
    limit: int = Query(default=500, ge=1, le=5000),
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
    result = USAGE_TRUTH.usage_summary(
        limit=limit,
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
    return {
        "filters": result["filters"],
        "summary": result["summary"],
        "count": result["count"],
        "matched": result["matched"],
        "scanned": result["scanned"],
    }


@app.get("/api/admin/usage/users/{target_user_id}")
@app.get(API_V1_ADMIN_USAGE_USER)
async def admin_usage_by_user(
    target_user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
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
    result = USAGE_TRUTH.usage_summary(
        limit=limit,
        user_id=target_user_id,
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
    return {
        "user_id": target_user_id,
        "count": result["count"],
        "matched": result["matched"],
        "scanned": result["scanned"],
        "filters": result["filters"],
        "summary": result["summary"],
        "events": result["items"],
    }

# Query Classification endpoints
@app.post("/api/classify", response_model=ClassificationResponse)
@app.post(API_V1_CLASSIFY, response_model=ClassificationResponse)
async def classify_query(request: ClassificationRequest):
    """Classify a query without processing it"""
    classification = query_classifier.classify(request.query)
    return ClassificationResponse(**classification.to_dict())

@app.post("/api/classify/batch")
@app.post(API_V1_CLASSIFY_BATCH)
async def classify_batch(queries: List[str]):
    """Classify multiple queries at once"""
    results = query_classifier.batch_classify(queries)
    stats = query_classifier.get_classification_stats(queries)
    return {
        "results": [r.to_dict() for r in results],
        "statistics": stats
    }

# Load Balancer endpoints
@app.get("/api/loadbalancer/metrics", response_model=LoadBalancerMetrics)
@app.get(API_V1_SYSTEM_LOADBALANCER_METRICS, response_model=LoadBalancerMetrics)
async def get_loadbalancer_metrics():
    """Get load balancer metrics"""
    return LoadBalancerMetrics(**load_balancer.get_metrics())

@app.get("/api/loadbalancer/providers")
@app.get(API_V1_SYSTEM_LOADBALANCER_PROVIDERS)
async def get_providers():
    """Get list of all available providers"""
    providers = []
    for provider_type, provider_list in load_balancer.providers.items():
        for provider in provider_list:
            providers.append({
                "name": provider.name,
                "type": provider.provider_type.value,
                "model": provider.model,
                "endpoint": provider.endpoint,
                "weight": provider.weight,
                "timeout": provider.timeout,
                "enabled": provider.enabled
            })
    return {"providers": providers}

@app.post("/api/loadbalancer/providers/{provider_name}/disable")
@app.post(API_V1_SYSTEM_LOADBALANCER_DISABLE)
async def disable_provider(provider_name: str, current_user = Depends(get_current_admin_user)):
    """Disable a provider"""
    success = load_balancer.disable_provider(provider_name)
    if success:
        return {"message": f"Provider {provider_name} disabled"}
    else:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

@app.post("/api/loadbalancer/providers/{provider_name}/enable")
@app.post(API_V1_SYSTEM_LOADBALANCER_ENABLE)
async def enable_provider(provider_name: str, current_user = Depends(get_current_admin_user)):
    """Enable a provider"""
    success = load_balancer.enable_provider(provider_name)
    if success:
        return {"message": f"Provider {provider_name} enabled"}
    else:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

# Model Management endpoints
@app.get("/api/models/status")
@app.get(API_V1_MODELS_STATUS)
async def get_models_status():
    """Get status of all models"""
    return model_manager.get_all_status()

@app.get("/api/models/status/{model_name}", response_model=ModelStatusResponse)
@app.get(API_V1_MODELS_STATUS_ITEM, response_model=ModelStatusResponse)
async def get_model_status(model_name: str):
    """Get status of a specific model"""
    status = model_manager.get_model_status(model_name)
    if status:
        return ModelStatusResponse(**status)
    else:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

@app.post("/api/models/warmup/{model_name}")
@app.post(API_V1_MODELS_WARMUP_ITEM)
async def warmup_model(model_name: str, timeout: int = 30, current_user = Depends(get_current_admin_user)):
    """Manually warm up a model"""
    success = await model_manager.warmup_model(model_name, timeout)
    if success:
        return {"message": f"Model {model_name} warmed up successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to warm up model {model_name}")

@app.post("/api/models/warmup/all")
@app.post(API_V1_MODELS_WARMUP_ALL)
async def warmup_all_models(timeout_per_model: int = 30, current_user = Depends(get_current_admin_user)):
    """Warm up all models"""
    results = await model_manager.warmup_all(timeout_per_model)
    successful = sum(1 for success in results.values() if success)
    return {
        "message": f"Warmed up {successful}/{len(results)} models",
        "results": results
    }

# User management endpoints (placeholder)
@app.get("/api/users")
@app.get(API_V1_USERS)
async def get_users():
    return {"users": []}

@app.post("/api/users")
@app.post(API_V1_USERS)
async def create_user():
    return {"message": "User created (placeholder)"}

# Ollama endpoints (Step 7 - Hybrid AI Pipeline)
@app.get("/api/v1/auth/api-key/me")
async def get_api_key_authenticated_identity(identity = Depends(get_api_key_identity)):
    """Resolve current identity from API key for verification/testing."""
    return {
        "user": {
            "id": identity["user"]["id"],
            "email": identity["user"]["email"],
            "name": identity["user"]["name"],
            "role": identity["user"]["role"],
        },
        "api_key": identity["api_key"],
    }


@app.get("/api/ollama/models")
@app.get(API_V1_OLLAMA_MODELS)
async def get_ollama_models():
    """Get list of available Ollama models"""
    try:
        models = await ollama_service.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Ollama models: {str(e)}")

@app.get("/api/ollama/health")
@app.get(API_V1_OLLAMA_HEALTH)
async def ollama_health():
    """Check Ollama service health"""
    is_healthy = await ollama_service.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy", "service": "ollama"}

@app.post("/api/ollama/generate", response_model=OllamaResponse)
@app.post(API_V1_OLLAMA_GENERATE, response_model=OllamaResponse)
async def ollama_generate(request: OllamaRequest):
    """Generate text using Ollama model"""
    try:
        result = await ollama_service.generate(
            model=request.model,
            prompt=request.prompt,
            stream=request.stream
        )
        return OllamaResponse(
            response=result.get("response", ""),
            model=request.model,
            created_at=result.get("created_at", ""),
            done=result.get("done", True)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama generation failed: {str(e)}")

@app.post("/api/ollama/chat")
@app.post(API_V1_OLLAMA_CHAT)
async def ollama_chat(request: OllamaChatRequest):
    """Chat completion using Ollama"""
    try:
        result = await ollama_service.chat(
            model=request.model,
            messages=request.messages,
            stream=request.stream
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama chat failed: {str(e)}")

# Legacy hybrid endpoint (backward compatibility)
@app.post("/api/hybrid/chat", response_model=ChatResponse)
@app.post(API_V1_HYBRID_CHAT, response_model=ChatResponse)
async def hybrid_chat(request: ChatRequest):
    """
    Legacy hybrid endpoint - uses new load balancing system
    """
    return await chat(request)

# Test endpoints
@app.get("/api/test/classification")
@app.get(API_V1_TEST_CLASSIFICATION)
async def test_classification():
    """Test query classification with sample queries"""
    test_queries = [
        "Xin chào",
        "Thời tiết hôm nay thế nào?",
        "Giải thích về machine learning",
        "Viết function Python để xử lý JSON và kết nối database MySQL",
        "How are you today?",
        "Explain the theory of relativity",
        "Create a React component with TypeScript and Tailwind CSS"
    ]
    
    results = query_classifier.batch_classify(test_queries)
    stats = query_classifier.get_classification_stats(test_queries)
    
    return {
        "test_queries": test_queries,
        "classifications": [r.to_dict() for r in results],
        "statistics": stats
    }

@app.get("/api/test/loadbalancer")
@app.get(API_V1_TEST_LOADBALANCER)
async def test_loadbalancer():
    return {"message": "Load balancer test endpoint"}


# Control Dashboard Proxy
from fastapi import HTTPException, Depends
import httpx

CONTROL_DASHBOARD_URL = "http://localhost:8090"
CONTROL_DASHBOARD_TOKEN = "ttai-control-token"

@app.get("/api/v1/admin/control-dashboard/health-summary")
async def get_control_dashboard_health_summary(current_user = Depends(get_current_admin_user)):
    """Proxy to control dashboard health-summary endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{CONTROL_DASHBOARD_URL}/health-summary",
                headers={"X-Control-Token": CONTROL_DASHBOARD_TOKEN}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Collector unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Collector error: {e.response.text}")

@app.get("/api/v1/admin/control-dashboard/providers")
async def get_control_dashboard_providers(current_user = Depends(get_current_admin_user)):
    """Proxy to control dashboard providers endpoint"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{CONTROL_DASHBOARD_URL}/providers",
                headers={"X-Control-Token": CONTROL_DASHBOARD_TOKEN}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Collector unavailable: {str(e)}")

@app.get("/api/v1/admin/control-dashboard")
async def get_control_dashboard_root(current_user = Depends(get_current_admin_user)):
    """Main control dashboard endpoint - returns health-summary by default"""
    return await get_control_dashboard_health_summary(current_user)

@app.get("/api/v1/admin/usage/events")
async def get_usage_events(limit: int = Query(50, ge=1, le=500), current_user = Depends(get_current_admin_user)):
    """Read latest local usage events from phase-1 JSONL ledger"""
    return {
        "events": read_usage_events(limit),
        "count": len(read_usage_events(limit)),
        "source": str(USAGE_EVENTS_PATH)
    }

@app.get("/api/v1/admin/usage/summary")
async def get_usage_summary(limit: int = Query(200, ge=1, le=2000), current_user = Depends(get_current_admin_user)):
    """Get lightweight usage summary from phase-1 JSONL ledger"""
    events = read_usage_events(limit)
    return {
        "summary": summarize_usage_events(events),
        "source": str(USAGE_EVENTS_PATH),
        "window_event_count": len(events)
    }

async def test_loadbalancer():
    """Test load balancer with sample classifications"""
    test_cases = [
        ("simple", QueryComplexity.SIMPLE),
        ("medium", QueryComplexity.MEDIUM),
        ("complex", QueryComplexity.COMPLEX)
    ]
    
    results = []
    for name, complexity in test_cases:
        classification = ClassificationResult(
            complexity=complexity,
            confidence=0.9,
            language="vi",
            needs_context=False,
            estimated_tokens=50,
            features={}
        )
        
        provider = load_balancer.select_provider(classification)
        results.append({
            "complexity": name,
            "selected_provider": provider.name,
            "provider_type": provider.provider_type.value,
            "model": provider.model
        })
    
    return {
        "test_cases": results,
        "metrics": load_balancer.get_metrics()
    }

# Import datetime for health endpoint
from datetime import datetime
# Control Dashboard
from control_dashboard import collector_service

# Quota status endpoints
@app.get("/api/admin/quota/status")
@app.get(API_V1_ADMIN_QUOTA_STATUS)
async def admin_quota_status(
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    current_user = Depends(get_current_admin_user),
):
    return USAGE_TRUTH.quota_status(
        user_id=user_id,
        tenant_id=tenant_id,
        api_key_id=api_key_id,
    )

@app.get("/api/admin/quota/status/users/{target_user_id}")
@app.get(API_V1_ADMIN_QUOTA_STATUS_USER)
async def admin_quota_status_by_user(
    target_user_id: str,
    tenant_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    current_user = Depends(get_current_admin_user),
):
    return USAGE_TRUTH.quota_status(
        user_id=target_user_id,
        tenant_id=tenant_id,
        api_key_id=api_key_id,
    )

# Billing summary endpoint
@app.get("/api/admin/usage/billing-summary")
@app.get(API_V1_ADMIN_USAGE_BILLING_SUMMARY)
async def admin_billing_summary(
    limit: int = Query(default=500, ge=1, le=5000),
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
    current_user = Depends(get_current_admin_user),
):
    result = USAGE_TRUTH.billing_summary(
        limit=limit,
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
    return {
        "filters": result["filters"],
        "summary": result["summary"],
        "count": result["count"],
        "matched": result["matched"],
        "scanned": result["scanned"],
    }

@app.get(API_V1_ADMIN_OVERVIEW)
async def admin_overview(
    usage_limit: int = Query(default=200, ge=1, le=5000),
    recent_events_limit: int = Query(default=20, ge=1, le=100),
    current_user = Depends(get_current_admin_user),
):
    recent_events = read_usage_events(limit=usage_limit)
    usage_summary = summarize_usage_events(recent_events)
    billing_summary = summarize_billing_usage(recent_events)
    health_summary = await health()
    detailed_health = await health_detailed()

    blocked_events = [
        event for event in recent_events
        if event.get("status") == "quota_exceeded" or event.get("http_status") == 429
    ]

    recent_errors = [
        {
            "timestamp": event.get("timestamp"),
            "request_id": event.get("request_id"),
            "provider": event.get("provider"),
            "model": event.get("model"),
            "status": event.get("status"),
            "http_status": event.get("http_status"),
            "error": event.get("error"),
        }
        for event in recent_events
        if event.get("status") not in (None, "success")
    ][:recent_events_limit]

    quota_highlights = {
        "blocked_event_count": len(blocked_events),
        "recent_blocked": [
            {
                "timestamp": event.get("timestamp"),
                "user_id": event.get("user_id"),
                "tenant_id": event.get("tenant_id"),
                "api_key_id": event.get("api_key_id"),
                "reason": event.get("error") or event.get("status"),
            }
            for event in blocked_events[:recent_events_limit]
        ],
    }

    return {
        "health": {
            "summary": health_summary,
            "detailed": {
                "ollama": detailed_health.get("ollama"),
                "load_balancer": detailed_health.get("load_balancer"),
                "system": detailed_health.get("system"),
            },
        },
        "usage": {
            "summary": usage_summary,
            "recent_events": recent_events[:recent_events_limit],
            "window_event_count": len(recent_events),
        },
        "billing": {
            "summary": billing_summary,
        },
        "quota": quota_highlights,
        "alerts": {
            "recent_errors": recent_errors,
        },
    }

@app.get(API_V1_ADMIN_ERRORS_SUMMARY)
async def admin_errors_summary(
    limit: int = Query(default=200, ge=1, le=5000),
    top_n: int = Query(default=10, ge=1, le=50),
    current_user = Depends(get_current_admin_user),
):
    events = read_usage_events(limit=limit)
    error_events = [
        event for event in events
        if event.get("status") not in (None, "success")
    ]

    status_counts = Counter(event.get("status") or "unknown" for event in error_events)
    http_status_counts = Counter(str(event.get("http_status") or "unknown") for event in error_events)
    provider_counts = Counter(event.get("provider") or "unknown" for event in error_events)
    model_counts = Counter(event.get("model") or "unknown" for event in error_events)

    error_signature_counts = Counter(
        f"{event.get('status') or 'unknown'}|{event.get('http_status') or 'unknown'}|{event.get('provider') or 'unknown'}|{event.get('model') or 'unknown'}|{extract_error_message(event)[:120]}"
        for event in error_events
    )

    recent_errors = [
        {
            "timestamp": event.get("timestamp"),
            "request_id": event.get("request_id"),
            "user_id": event.get("user_id"),
            "tenant_id": event.get("tenant_id"),
            "api_key_id": event.get("api_key_id"),
            "provider": event.get("provider"),
            "model": event.get("model"),
            "status": event.get("status"),
            "http_status": event.get("http_status"),
            "error": extract_error_message(event),
        }
        for event in error_events[:top_n]
    ]

    return {
        "window_event_count": len(events),
        "error_event_count": len(error_events),
        "status_breakdown": dict(status_counts.most_common(top_n)),
        "http_status_breakdown": dict(http_status_counts.most_common(top_n)),
        "provider_breakdown": dict(provider_counts.most_common(top_n)),
        "model_breakdown": dict(model_counts.most_common(top_n)),
        "top_error_signatures": [
            {"signature": signature, "count": count}
            for signature, count in error_signature_counts.most_common(top_n)
        ],
        "recent_errors": recent_errors,
    }

@app.get(API_V1_ADMIN_QUOTA_BLOCKED)
async def admin_quota_blocked(
    limit: int = Query(default=200, ge=1, le=5000),
    recent_limit: int = Query(default=20, ge=1, le=100),
    current_user = Depends(get_current_admin_user),
):
    events = read_usage_events(limit=limit)
    blocked_events = [
        event for event in events
        if event.get("status") == "quota_exceeded" or event.get("http_status") == 429
    ]

    tenant_counts = Counter(event.get("tenant_id") or "unknown" for event in blocked_events)
    api_key_counts = Counter(event.get("api_key_id") or "unknown" for event in blocked_events)
    user_counts = Counter(event.get("user_id") or "unknown" for event in blocked_events)
    reason_counts = Counter(extract_quota_reason(event) for event in blocked_events)

    recent_blocked = [
        {
            "timestamp": event.get("timestamp"),
            "request_id": event.get("request_id"),
            "user_id": event.get("user_id"),
            "tenant_id": event.get("tenant_id"),
            "api_key_id": event.get("api_key_id"),
            "quota_mode": event.get("quota_mode"),
            "quota_reason": extract_quota_reason(event),
            "http_status": event.get("http_status"),
        }
        for event in blocked_events[:recent_limit]
    ]

    return {
        "window_event_count": len(events),
        "blocked_event_count": len(blocked_events),
        "tenant_breakdown": dict(tenant_counts.most_common(20)),
        "api_key_breakdown": dict(api_key_counts.most_common(20)),
        "user_breakdown": dict(user_counts.most_common(20)),
        "reason_breakdown": dict(reason_counts.most_common(20)),
        "recent_blocked": recent_blocked,
    }

# Control frontend proxy endpoints (same-origin, no bearer in browser JS)
@app.get("/control-api/overview")
async def control_overview(
    usage_limit: int = Query(default=200, ge=1, le=5000),
    recent_events_limit: int = Query(default=20, ge=1, le=100),
    current_user = Depends(get_current_control_user),
):
    usage_result = USAGE_TRUTH.usage_summary(limit=usage_limit)
    billing_result = USAGE_TRUTH.billing_summary(limit=usage_limit)
    recent_events = usage_result.get("items", [])
    usage_summary = usage_result.get("summary", {})
    billing_summary = billing_result.get("summary", {})
    health_summary = await health()
    detailed_health = await health_detailed()

    blocked_events = [
        event for event in recent_events
        if event.get("status") == "quota_exceeded" or event.get("http_status") == 429
    ]

    recent_errors = [
        {
            "timestamp": event.get("timestamp"),
            "request_id": event.get("request_id"),
            "provider": event.get("provider"),
            "model": event.get("model"),
            "status": event.get("status"),
            "http_status": event.get("http_status"),
            "error": extract_error_message(event),
        }
        for event in recent_events
        if event.get("status") not in (None, "success")
    ][:recent_events_limit]

    return {
        "health": {
            "summary": health_summary,
            "detailed": {
                "ollama": detailed_health.get("ollama"),
                "load_balancer": detailed_health.get("load_balancer"),
                "system": detailed_health.get("system"),
            },
        },
        "usage": {
            "summary": usage_summary,
            "count": usage_result.get("count", 0),
            "matched": usage_result.get("matched", 0),
            "scanned": usage_result.get("scanned", 0),
            "filters": usage_result.get("filters", {}),
            "recent_events": recent_events[:recent_events_limit],
            "window_event_count": len(recent_events),
        },
        "billing": {
            "summary": billing_summary,
            "count": billing_result.get("count", 0),
            "matched": billing_result.get("matched", 0),
            "scanned": billing_result.get("scanned", 0),
            "filters": billing_result.get("filters", {}),
        },
        "quota": {
            "blocked_event_count": len(blocked_events),
            "recent_blocked": [
                {
                    "timestamp": event.get("timestamp"),
                    "user_id": event.get("user_id"),
                    "tenant_id": event.get("tenant_id"),
                    "api_key_id": event.get("api_key_id"),
                    "reason": extract_quota_reason(event),
                }
                for event in blocked_events[:recent_events_limit]
            ],
            "tenant_breakdown": dict(Counter(event.get("tenant_id") or "unknown" for event in blocked_events).most_common(20)),
            "api_key_breakdown": dict(Counter(event.get("api_key_id") or "unknown" for event in blocked_events).most_common(20)),
            "reason_breakdown": dict(Counter(extract_quota_reason(event) for event in blocked_events).most_common(20)),
        },
        "alerts": {
            "recent_errors": recent_errors,
        },
    }

@app.get("/control-api/quota")
async def control_quota(
    limit: int = Query(default=200, ge=1, le=5000),
    recent_limit: int = Query(default=20, ge=1, le=100),
    current_user = Depends(get_current_control_user),
):
    result = USAGE_TRUTH.query_events(limit=limit)
    events = result.get("items", [])
    blocked_events = [
        event for event in events
        if event.get("status") == "quota_exceeded" or event.get("http_status") == 429
    ]
    return {
        "count": result.get("count", 0),
        "matched": result.get("matched", 0),
        "scanned": result.get("scanned", 0),
        "filters": result.get("filters", {}),
        "window_event_count": len(events),
        "blocked_event_count": len(blocked_events),
        "tenant_breakdown": dict(Counter(event.get("tenant_id") or "unknown" for event in blocked_events).most_common(20)),
        "api_key_breakdown": dict(Counter(event.get("api_key_id") or "unknown" for event in blocked_events).most_common(20)),
        "user_breakdown": dict(Counter(event.get("user_id") or "unknown" for event in blocked_events).most_common(20)),
        "reason_breakdown": dict(Counter(extract_quota_reason(event) for event in blocked_events).most_common(20)),
        "recent_blocked": [
            {
                "timestamp": event.get("timestamp"),
                "request_id": event.get("request_id"),
                "user_id": event.get("user_id"),
                "tenant_id": event.get("tenant_id"),
                "api_key_id": event.get("api_key_id"),
                "quota_mode": event.get("quota_mode"),
                "quota_reason": extract_quota_reason(event),
                "http_status": event.get("http_status"),
            }
            for event in blocked_events[:recent_limit]
        ],
    }

@app.get("/control-api/billing")
async def control_billing(limit: int = Query(default=200, ge=1, le=5000), current_user = Depends(get_current_control_user)):
    result = USAGE_TRUTH.billing_summary(limit=limit)
    summary = result.get("summary", {})
    return {
        "count": result.get("count", 0),
        "matched": result.get("matched", 0),
        "scanned": result.get("scanned", 0),
        "filters": result.get("filters", {}),
        "summary": summary,
        "tenant_breakdown": summary.get("tenant_breakdown", {}),
        "user_breakdown": summary.get("user_breakdown", {}),
        "api_key_breakdown": summary.get("api_key_breakdown", {}),
        "provider_breakdown": summary.get("provider_breakdown", {}),
        "model_breakdown": summary.get("model_breakdown", {}),
        "billable_mode_breakdown": summary.get("billable_mode_breakdown", {}),
    }

@app.get("/control-api/errors")
async def control_errors(
    limit: int = Query(default=200, ge=1, le=5000),
    top_n: int = Query(default=10, ge=1, le=50),
    current_user = Depends(get_current_control_user),
):
    result = USAGE_TRUTH.query_events(limit=limit)
    events = result.get("items", [])
    error_events = [event for event in events if event.get("status") not in (None, "success")]
    status_counts = Counter(event.get("status") or "unknown" for event in error_events)
    http_status_counts = Counter(str(event.get("http_status") or "unknown") for event in error_events)
    provider_counts = Counter(event.get("provider") or "unknown" for event in error_events)
    model_counts = Counter(event.get("model") or "unknown" for event in error_events)
    error_signature_counts = Counter(
        f"{event.get('status') or 'unknown'}|{event.get('http_status') or 'unknown'}|{event.get('provider') or 'unknown'}|{event.get('model') or 'unknown'}|{extract_error_message(event)[:120]}"
        for event in error_events
    )
    return {
        "count": result.get("count", 0),
        "matched": result.get("matched", 0),
        "scanned": result.get("scanned", 0),
        "filters": result.get("filters", {}),
        "window_event_count": len(events),
        "error_event_count": len(error_events),
        "status_breakdown": dict(status_counts.most_common(top_n)),
        "http_status_breakdown": dict(http_status_counts.most_common(top_n)),
        "provider_breakdown": dict(provider_counts.most_common(top_n)),
        "model_breakdown": dict(model_counts.most_common(top_n)),
        "top_error_signatures": [
            {"signature": signature, "count": count}
            for signature, count in error_signature_counts.most_common(top_n)
        ],
        "recent_errors": [
            {
                "timestamp": event.get("timestamp"),
                "request_id": event.get("request_id"),
                "user_id": event.get("user_id"),
                "tenant_id": event.get("tenant_id"),
                "api_key_id": event.get("api_key_id"),
                "provider": event.get("provider"),
                "model": event.get("model"),
                "status": event.get("status"),
                "http_status": event.get("http_status"),
                "error": extract_error_message(event),
            }
            for event in error_events[:top_n]
        ],
    }

@app.get("/control-api/models")
async def control_models(current_user = Depends(get_current_control_user)):
    models_status = await get_models_status()
    lb_providers = await get_providers()
    lb_metrics = await get_loadbalancer_metrics()
    ollama = await ollama_health()
    ollama_models_resp = await get_ollama_models()
    collector_model_status = await collector_service.models()

    models_list = list(models_status.values()) if isinstance(models_status, dict) else []
    provider_list = lb_providers.get("providers", []) if isinstance(lb_providers, dict) else []
    ollama_models = ollama_models_resp.get("models", []) if isinstance(ollama_models_resp, dict) else []
    lb_metrics_dict = lb_metrics.model_dump() if hasattr(lb_metrics, "model_dump") else (lb_metrics if isinstance(lb_metrics, dict) else {})
    model_hosts = ((collector_model_status or {}).get("model_status") or {}).get("hosts", [])

    health_status_map = (lb_metrics_dict.get("health_status", {}) or {})
    provider_list = [
        {
            **provider,
            "health": "healthy" if health_status_map.get(provider.get("name")) else "unhealthy",
            "enabled_state": "enabled" if provider.get("enabled") else "disabled",
        }
        for provider in provider_list
    ]

    warm_count = sum(1 for m in models_list if m.get("is_ready"))
    error_count = sum(1 for m in models_list if m.get("status") == "error")
    enabled_count = sum(1 for p in provider_list if p.get("enabled"))
    healthy_provider_count = sum(1 for ok in health_status_map.values() if ok)

    return {
        "summary": {
            "model_count": len(models_list),
            "warm_count": warm_count,
            "error_count": error_count,
            "provider_count": len(provider_list),
            "enabled_provider_count": enabled_count,
            "healthy_provider_count": healthy_provider_count,
            "enabled_provider_count": enabled_count,
            "disabled_provider_count": max(len(provider_list) - enabled_count, 0),
            "ollama_status": ollama.get("status", "unknown"),
            "ollama_model_count": len(ollama_models),
            "host_group_count": len(model_hosts),
        },
        "models": models_list,
        "model_hosts": model_hosts,
        "providers": provider_list,
        "load_balancer_metrics": lb_metrics_dict,
        "ollama": {
            "health": ollama,
            "models": ollama_models,
        },
    }

@app.get("/control-api/system")
async def control_system(current_user = Depends(get_current_control_user)):
    health_summary = await collector_service.health_summary()
    workloads = await collector_service.workloads()
    alerts = await collector_service.alerts()

    nodes = health_summary.get("nodes", []) if isinstance(health_summary, dict) else []
    alerts_list = alerts.get("alerts", []) if isinstance(alerts, dict) else []
    lb_summary = workloads.get("load_balancer", {}).get("summary", {}) if isinstance(workloads, dict) else {}

    return {
        "summary": {
            "overall_status": health_summary.get("overall_status", "unknown") if isinstance(health_summary, dict) else "unknown",
            "node_count": len(nodes),
            "alert_count": len(alerts_list),
            "dataset_count": workloads.get("datasets", {}).get("count", 0) if isinstance(workloads, dict) else 0,
            "rag_document_count": workloads.get("rag", {}).get("document_count", 0) if isinstance(workloads, dict) else 0,
            "learn_queue_length": workloads.get("learn_queue", {}).get("length", 0) if isinstance(workloads, dict) else 0,
            "backend_count": len(lb_summary),
        },
        "health": health_summary,
        "workloads": workloads,
        "alerts": alerts,
    }

@app.get("/control-api/topology")
async def control_topology(current_user = Depends(get_current_control_user)):
    inventory = {
        "nodes": [
            {"id": "node-vhp", "name": "vannt-home-pc", "role": "development", "status": "operational"},
            {"id": "node-vwo", "name": "vannt-work-op", "role": "compute", "status": "operational"},
            {"id": "node-dell", "name": "Dell Zx0Q", "role": "production", "status": "operational"},
        ],
        "services": [
            {"id": "svc-fastapi-8000", "name": "FastAPI Original", "type": "api", "node_id": "node-vhp", "status": "offline"},
            {"id": "svc-hybrid-8005", "name": "TTAi Hybrid v2.0", "type": "api", "node_id": "node-vhp", "status": "operational"},
            {"id": "svc-debug-8013", "name": "TTAi Debug", "type": "api", "node_id": "node-vhp", "status": "operational"},
            {"id": "svc-lb-8015", "name": "Load Balancer", "type": "load_balancer", "node_id": "node-vhp", "status": "operational"},
            {"id": "svc-rag-8075", "name": "RAG Service", "type": "memory", "node_id": "node-vhp", "status": "unknown"},
            {"id": "svc-dashboard-8090", "name": "Control Dashboard", "type": "dashboard", "node_id": "node-vhp", "status": "unknown"},
            {"id": "svc-cliproxy-8317", "name": "CLI Proxy", "type": "cli_proxy", "node_id": "node-vhp", "status": "operational"},
            {"id": "svc-ollama-public", "name": "Ollama Public", "type": "ai_inference", "node_id": "node-vhp", "status": "operational"},
            {"id": "svc-ollama-memory", "name": "Ollama Memory", "type": "ai_inference", "node_id": "node-vhp", "status": "operational"},
            {"id": "svc-wordpress", "name": "WordPress", "type": "cms", "node_id": "node-dell", "status": "offline"},
            {"id": "svc-fastapi-prod", "name": "FastAPI Prod", "type": "api", "node_id": "node-dell", "status": "offline"},
            {"id": "svc-postgres", "name": "PostgreSQL", "type": "database", "node_id": "node-dell", "status": "operational"},
            {"id": "svc-mysql", "name": "MySQL", "type": "database", "node_id": "node-dell", "status": "operational"},
            {"id": "svc-redis", "name": "Redis", "type": "cache", "node_id": "node-dell", "status": "operational"},
            {"id": "svc-ollama-remote", "name": "Ollama Remote", "type": "ai_inference", "node_id": "node-vwo", "status": "operational"},
            {"id": "svc-fastapi-remote", "name": "TTAi Remote API", "type": "api", "node_id": "node-vwo", "status": "operational"}
        ],
        "dependencies": [
            {"source_service_id": "svc-lb-8015", "target_service_id": "svc-debug-8013", "type": "api_call", "critical": True},
            {"source_service_id": "svc-lb-8015", "target_service_id": "svc-fastapi-remote", "type": "api_call", "critical": False},
            {"source_service_id": "svc-hybrid-8005", "target_service_id": "svc-cliproxy-8317", "type": "api_call", "critical": True},
            {"source_service_id": "svc-hybrid-8005", "target_service_id": "svc-ollama-public", "type": "api_call", "critical": True},
            {"source_service_id": "svc-rag-8075", "target_service_id": "svc-ollama-memory", "type": "api_call", "critical": True},
            {"source_service_id": "svc-wordpress", "target_service_id": "svc-mysql", "type": "database", "critical": True},
            {"source_service_id": "svc-fastapi-prod", "target_service_id": "svc-postgres", "type": "database", "critical": True}
        ]
    }
    nodes = inventory["nodes"]
    services = inventory["services"]
    dependencies = inventory["dependencies"]
    return {
        "version": "topology-mvp-v1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "node_count": len(nodes),
            "operational_node_count": sum(1 for n in nodes if n.get("status") == "operational"),
            "service_count": len(services),
            "operational_service_count": sum(1 for s in services if s.get("status") == "operational"),
            "dependency_count": len(dependencies),
            "critical_dependency_count": sum(1 for d in dependencies if d.get("critical")),
        },
        "inventory": inventory,
    }

@app.get("/control-api/proxy/state")
async def control_proxy_state(current_user = Depends(get_current_control_user)):
    return await get_proxy_runtime_state()


@app.get("/control-api/proxy/backends")
async def control_proxy_backends(current_user = Depends(get_current_control_user)):
    return await get_proxy_backends_state()


@app.get("/control-api/proxy/benchmark/latest")
async def control_proxy_benchmark_latest(current_user = Depends(get_current_control_user)):
    return get_latest_proxy_benchmark()


@app.get("/control-api/usage")
async def control_usage(limit: int = Query(default=20, ge=5, le=100), current_user = Depends(get_current_control_user)):
    summary_result = USAGE_TRUTH.usage_summary(limit=500)
    events_result = USAGE_TRUTH.query_events(limit=200)

    summary = summary_result.get("summary", {}) if isinstance(summary_result, dict) else {}
    raw_events = events_result.get("items", []) if isinstance(events_result, dict) else []
    events = [normalize_usage_event(event) for event in raw_events]

    deduped_events = []
    seen_keys = set()
    for event in events:
        dedupe_key = (
            event.get("request_id"),
            event.get("user_id"),
            event.get("status_normalized"),
            event.get("quota_reason_normalized"),
            event.get("provider"),
            event.get("model"),
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduped_events.append(event)

    normalized_status_breakdown = {}
    tenant_counts = {}
    api_key_counts = {}
    fallback_count = 0
    processing_times = []

    for event in deduped_events:
        normalized_status = event.get("status_normalized", "unknown")
        normalized_status_breakdown[normalized_status] = normalized_status_breakdown.get(normalized_status, 0) + 1

        tenant_id = event.get("tenant_id") or "unassigned"
        tenant_counts[tenant_id] = tenant_counts.get(tenant_id, 0) + 1

        api_key_id = event.get("api_key_id") or "unassigned"
        api_key_counts[api_key_id] = api_key_counts.get(api_key_id, 0) + 1

        if event.get("fallback_used"):
            fallback_count += 1

        processing_time = event.get("processing_time")
        if isinstance(processing_time, (int, float)):
            processing_times.append(processing_time)

    deduped_total = len(deduped_events)
    avg_latency = (sum(processing_times) / len(processing_times)) if processing_times else 0
    fallback_rate = (fallback_count / deduped_total) if deduped_total else 0

    top_users = summary.get("top_users", []) if isinstance(summary, dict) else []
    top_providers = summary.get("top_providers", []) if isinstance(summary, dict) else []
    top_provider_types = summary.get("top_provider_types", []) if isinstance(summary, dict) else []

    return {
        "summary": summary,
        "count": events_result.get("count", 0) if isinstance(events_result, dict) else 0,
        "matched": events_result.get("matched", 0) if isinstance(events_result, dict) else 0,
        "scanned": events_result.get("scanned", 0) if isinstance(events_result, dict) else 0,
        "filters": events_result.get("filters", {}) if isinstance(events_result, dict) else {},
        "highlights": {
            "total_events": summary.get("total_events", 0),
            "deduped_events": deduped_total,
            "success_events": normalized_status_breakdown.get("success", 0),
            "error_events": normalized_status_breakdown.get("error", 0),
            "quota_exceeded_events": normalized_status_breakdown.get("quota_exceeded", 0),
            "fallback_events": fallback_count,
            "fallback_rate": fallback_rate,
            "total_tokens_est": summary.get("total_tokens_est", 0),
            "avg_processing_time": summary.get("avg_processing_time", 0),
            "avg_processing_time_deduped": avg_latency,
            "top_user": top_users[0] if top_users else None,
            "top_provider": top_providers[0] if top_providers else None,
            "top_provider_type": top_provider_types[0] if top_provider_types else None,
            "top_status": next(iter(normalized_status_breakdown.items())) if normalized_status_breakdown else None,
        },
        "breakdowns": {
            "status_normalized": dict(sorted(normalized_status_breakdown.items(), key=lambda item: item[1], reverse=True)),
            "top_tenants": sorted(tenant_counts.items(), key=lambda item: item[1], reverse=True)[:10],
            "top_api_keys": sorted(api_key_counts.items(), key=lambda item: item[1], reverse=True)[:10],
        },
        "recent_events": deduped_events[:limit],
    }


@app.get("/control-api/session")
async def control_session_state(current_user = Depends(get_current_control_user)):
    return build_control_response(
        True,
        "session_state",
        "Control session active",
        user=current_user,
        cookie_secure=should_use_secure_cookie(),
        available_actions=get_available_control_actions(),
    )


@app.get("/control-api/actions")
async def control_actions(limit: int = Query(default=25, ge=1, le=200), current_user = Depends(get_current_control_user)):
    return build_control_response(
        True,
        "list_actions",
        "Loaded control action history",
        actions=read_control_actions(limit=limit),
    )


@app.post("/control-api/actions/run")
async def control_run_action(payload: ControlActionRequest, current_user = Depends(get_current_control_user)):
    action = (payload.action or "").strip().lower()
    target = (payload.target or "").strip()
    timestamp = datetime.utcnow().isoformat() + "Z"

    action_meta = CONTROL_ACTION_DEFINITIONS.get(action)
    action_record = {
        "timestamp": timestamp,
        "actor": current_user.get("username", "admin"),
        "session_type": current_user.get("session_type"),
        "action": action,
        "target": target or None,
        "timeout": payload.timeout,
        "sensitivity": action_meta.get("sensitivity") if action_meta else "unknown",
    }

    try:
        if not action_meta:
            raise HTTPException(status_code=400, detail=f"Unsupported control action: {action}")

        if not is_control_action_allowed(action):
            raise HTTPException(status_code=403, detail=f"Action disabled by policy: {action}")

        if action_meta.get("requires_target") and not target:
            raise HTTPException(status_code=400, detail=f"target is required for {action}")

        if action == "provider_enable":
            success = load_balancer.enable_provider(target)
            if not success:
                raise HTTPException(status_code=404, detail=f"Provider {target} not found")
            result = build_control_response(True, action, f"Provider {target} enabled")

        elif action == "provider_disable":
            success = load_balancer.disable_provider(target)
            if not success:
                raise HTTPException(status_code=404, detail=f"Provider {target} not found")
            result = build_control_response(True, action, f"Provider {target} disabled")

        elif action == "model_warmup":
            success = await model_manager.warmup_model(target, payload.timeout)
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to warm up model {target}")
            result = build_control_response(True, action, f"Model {target} warmed up successfully")

        elif action == "model_warmup_all":
            results = await model_manager.warmup_all(payload.timeout)
            result = build_control_response(
                True,
                action,
                f"Warmed up {sum(1 for success in results.values() if success)}/{len(results)} models",
                results=results,
            )

        elif action == "health_refresh":
            result = build_control_response(
                True,
                action,
                "Health snapshot refreshed",
                health=await health(),
                health_detailed=await health_detailed(),
            )

        elif action == "clear_learn_queue":
            file_result = clear_learn_queue_file()
            result = build_control_response(True, action, file_result.get("message", "Learn queue cleared"), **file_result)

        elif action == "archive_events":
            file_result = archive_usage_events_file()
            result = build_control_response(True, action, file_result.get("message", "Usage events archived"), **file_result)

        action_record["status"] = "success"
        action_record["result"] = result.get("message") or "ok"
        write_control_action(action_record)
        return result

    except HTTPException as exc:
        action_record["status"] = "error"
        action_record["result"] = exc.detail
        write_control_action(action_record)
        raise
    except Exception as exc:
        action_record["status"] = "error"
        action_record["result"] = str(exc)
        write_control_action(action_record)
        logger.error(f"Control action failed: {action}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Control action failed: {str(exc)}")

def extract_quota_reason(event: Dict) -> str:
    reason = event.get("quota_reason")
    if reason:
        return str(reason)

    error_value = event.get("error")
    if isinstance(error_value, dict):
        nested_reason = error_value.get("reason") or error_value.get("error")
        if nested_reason:
            return str(nested_reason)
    elif error_value:
        error_text = str(error_value)
        if "max_requests_exceeded" in error_text:
            return "max_requests_exceeded"
        if "max_tokens_est_exceeded" in error_text:
            return "max_tokens_est_exceeded"
        if "max_estimated_cost_exceeded" in error_text:
            return "max_estimated_cost_exceeded"
        if error_text != "quota_exceeded":
            return error_text

    status = event.get("status")
    if status:
        return str(status)

    return "unknown"


def extract_error_message(event: Dict) -> str:
    error_value = event.get("error")
    if isinstance(error_value, dict):
        nested_reason = error_value.get("reason") or error_value.get("error")
        if nested_reason:
            return str(nested_reason)
        return json.dumps(error_value, ensure_ascii=False)

    if error_value:
        error_text = str(error_value)
        if "max_requests_exceeded" in error_text:
            return "max_requests_exceeded"
        if "max_tokens_est_exceeded" in error_text:
            return "max_tokens_est_exceeded"
        if "max_estimated_cost_exceeded" in error_text:
            return "max_estimated_cost_exceeded"
        return error_text

    status = event.get("status")
    if status and status != "success":
        return str(status)

    return "Unknown error"


def normalize_usage_event(event: Dict) -> Dict:
    normalized = dict(event)

    status = str(normalized.get("status") or "unknown")
    quota_reason = extract_quota_reason(normalized)
    error_message = extract_error_message(normalized)

    normalized["status_normalized"] = status
    normalized["quota_reason_normalized"] = quota_reason
    normalized["error_message_normalized"] = error_message

    if status == "error" and quota_reason in {
        "max_requests_exceeded",
        "max_tokens_est_exceeded",
        "max_estimated_cost_exceeded",
    }:
        normalized["status_normalized"] = "quota_exceeded"

    return normalized

# Billing config management endpoints
@app.get("/api/admin/billing/config")
@app.get(API_V1_ADMIN_BILLING_CONFIG)
async def get_billing_config(current_user = Depends(get_current_admin_user)):
    """Get current billing configuration"""
    config = load_billing_config()
    return {
        "config": config,
        "path": str(BILLING_CONFIG_PATH),
        "exists": BILLING_CONFIG_PATH.exists(),
    }

@app.put("/api/admin/billing/config")
@app.put(API_V1_ADMIN_BILLING_CONFIG)
async def update_billing_config(new_config: Dict, current_user = Depends(get_current_admin_user)):
    """Update billing configuration (full replace)"""
    try:
        # Validate required structure
        if not isinstance(new_config, dict):
            raise HTTPException(status_code=400, detail="Config must be a JSON object")
        
        # Ensure required sections
        if "api_keys" not in new_config:
            new_config["api_keys"] = {}
        if "tenants" not in new_config:
            new_config["tenants"] = {}
        if "user_rules" not in new_config:
            new_config["user_rules"] = {
                "non_billable_prefixes": [],
                "non_billable_exact": []
            }
        
        # Add/update metadata
        new_config["version"] = new_config.get("version", "1.0.0")
        new_config["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Write to file
        with open(BILLING_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        return {
            "status": "updated",
            "path": str(BILLING_CONFIG_PATH),
            "config": new_config,
        }
    except Exception as e:
        logger.error(f"Failed to update billing config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


