from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from auth import get_current_admin_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
USAGE_EVENTS_PATH = BASE_DIR / "data" / "usage_events.jsonl"
BILLING_CONFIG_PATH = BASE_DIR / "data" / "billing_config.json"
USAGE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)

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
                    "internal_"
                ],
                "non_billable_exact": [
                    "anonymous",
                    "admin",
                    "system"
                ]
            }
        }
    try:
        with open(BILLING_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load billing config: {e}, using defaults")
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
                    "internal_"
                ],
                "non_billable_exact": [
                    "anonymous",
                    "admin",
                    "system"
                ]
            }
        }

def write_usage_event(event: Dict):
    with open(USAGE_EVENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

def read_usage_events(limit: int = 100) -> List[Dict]:
    if not USAGE_EVENTS_PATH.exists():
        return []
    lines = USAGE_EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))


def summarize_usage_events(events: List[Dict]) -> Dict:
    total = len(events)
    success = sum(1 for e in events if e.get("status") == "success")
    fallbacks = sum(1 for e in events if e.get("fallback_used"))
    total_tokens = sum(int(e.get("total_tokens_est") or 0) for e in events)
    avg_latency = round(sum(float(e.get("processing_time") or 0) for e in events) / total, 3) if total else 0
    providers = Counter(e.get("provider") or "unknown" for e in events)
    provider_types = Counter(e.get("provider_type") or "unknown" for e in events)
    users = Counter(e.get("user_id") or "anonymous" for e in events)
    statuses = Counter(e.get("status") or "unknown" for e in events)
    return {
        "total_events": total,
        "success_events": success,
        "error_events": total - success,
        "fallback_events": fallbacks,
        "total_tokens_est": total_tokens,
        "avg_processing_time": avg_latency,
        "top_providers": providers.most_common(10),
        "top_provider_types": provider_types.most_common(10),
        "top_users": users.most_common(10),
        "status_breakdown": dict(statuses),
    }


def filter_usage_events(
    events: List[Dict],
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
    filtered = events
    if user_id:
        filtered = [e for e in filtered if (e.get("user_id") or "") == user_id]
    if status:
        filtered = [e for e in filtered if (e.get("status") or "") == status]
    if provider:
        filtered = [e for e in filtered if (e.get("provider") or "") == provider]
    if model:
        filtered = [e for e in filtered if (e.get("model") or "") == model]
    if request_path:
        filtered = [e for e in filtered if (e.get("request_path") or "") == request_path]
    if tenant_id:
        filtered = [e for e in filtered if (e.get("tenant_id") or "") == tenant_id]
    if api_key_id:
        filtered = [e for e in filtered if (e.get("api_key_id") or "") == api_key_id]
    if quota_billable is not None:
        filtered = [e for e in filtered if e.get("quota_billable") is quota_billable]
    if billing_billable is not None:
        filtered = [e for e in filtered if e.get("billing_billable") is billing_billable]
    if billable_mode:
        filtered = [e for e in filtered if (e.get("billable_mode") or "") == billable_mode]
    return filtered


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

# Mount Control Dashboard
CONTROL_FRONTEND_PATH = BASE_DIR.parent / "control-frontend"
if CONTROL_FRONTEND_PATH.exists():
    app.mount("/control", StaticFiles(directory=str(CONTROL_FRONTEND_PATH), html=True), name="control")
    logger.info(f"Mounted control frontend at /control from {CONTROL_FRONTEND_PATH}")
else:
    logger.warning(f"Control frontend directory not found: {CONTROL_FRONTEND_PATH}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def root():
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
        user_id = request.user_id if hasattr(request, 'user_id') else 'anonymous'
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
        user_id = request.user_id if hasattr(request, 'user_id') else 'anonymous'
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
        if final_status == "quota_exceeded":
            raise
        final_status = "error"
        final_http_status = e.status_code
        error_detail = str(e.detail)
        processing_time = time.time() - start_time
        user_id = request.user_id if hasattr(request, 'user_id') else 'anonymous'
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
        user_id = request.user_id if hasattr(request, 'user_id') else 'anonymous'
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
    events = read_usage_events(limit=1000)
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
    return {
        "count": min(len(filtered), limit),
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
        "events": filtered[:limit],
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
    events = read_usage_events(limit=limit)
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
    return {
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
        "summary": summarize_usage_events(filtered),
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
    events = read_usage_events(limit=1000)
    filtered = filter_usage_events(
        events,
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
        "count": min(len(filtered), limit),
        "filters": {
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
        "summary": summarize_usage_events(filtered),
        "events": filtered[:limit],
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
    effective_user_id = user_id or "anonymous"
    quota_status = check_quota_allowance(
        user_id=effective_user_id,
        api_key_id=api_key_id,
        tenant_id=tenant_id,
    )
    return {
        "scope": {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "api_key_id": api_key_id,
        },
        "quota_status": quota_status,
    }

@app.get("/api/admin/quota/status/users/{target_user_id}")
@app.get(API_V1_ADMIN_QUOTA_STATUS_USER)
async def admin_quota_status_by_user(
    target_user_id: str,
    tenant_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    current_user = Depends(get_current_admin_user),
):
    quota_status = check_quota_allowance(
        user_id=target_user_id,
        api_key_id=api_key_id,
        tenant_id=tenant_id,
    )
    return {
        "scope": {
            "user_id": target_user_id,
            "tenant_id": tenant_id,
            "api_key_id": api_key_id,
        },
        "quota_status": quota_status,
    }

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
    events = read_usage_events(limit=limit)
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
    return {
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
        "summary": summarize_billing_usage(filtered),
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
        f"{event.get('status') or 'unknown'}|{event.get('http_status') or 'unknown'}|{event.get('provider') or 'unknown'}|{event.get('model') or 'unknown'}|{(event.get('error') or 'unknown')[:120]}"
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
            "error": event.get("error"),
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
):
    events = read_usage_events(limit=limit)
    blocked_events = [
        event for event in events
        if event.get("status") == "quota_exceeded" or event.get("http_status") == 429
    ]
    return {
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
async def control_billing(limit: int = Query(default=200, ge=1, le=5000)):
    events = read_usage_events(limit=limit)
    summary = summarize_billing_usage(events)
    return {
        "summary": summary,
        "tenant_breakdown": summary.get("tenant_breakdown", {}),
        "api_key_breakdown": summary.get("api_key_breakdown", {}),
        "provider_breakdown": summary.get("provider_breakdown", {}),
        "billable_mode_breakdown": summary.get("billable_mode_breakdown", {}),
    }

@app.get("/control-api/errors")
async def control_errors(
    limit: int = Query(default=200, ge=1, le=5000),
    top_n: int = Query(default=10, ge=1, le=50),
):
    events = read_usage_events(limit=limit)
    error_events = [event for event in events if event.get("status") not in (None, "success")]
    status_counts = Counter(event.get("status") or "unknown" for event in error_events)
    http_status_counts = Counter(str(event.get("http_status") or "unknown") for event in error_events)
    provider_counts = Counter(event.get("provider") or "unknown" for event in error_events)
    model_counts = Counter(event.get("model") or "unknown" for event in error_events)
    error_signature_counts = Counter(
        f"{event.get('status') or 'unknown'}|{event.get('http_status') or 'unknown'}|{event.get('provider') or 'unknown'}|{event.get('model') or 'unknown'}|{(event.get('error') or 'unknown')[:120]}"
        for event in error_events
    )
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
                "error": event.get("error"),
            }
            for event in error_events[:top_n]
        ],
    }

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

def summarize_billing_usage(events: List[Dict]) -> Dict:
    if not events:
        return {
            "total_estimated_cost": 0.0,
            "billable_estimated_cost": 0.0,
            "non_billable_estimated_cost": 0.0,
            "billable_events": 0,
            "non_billable_events": 0,
            "billable_mode_breakdown": {},
            "tenant_breakdown": {},
            "api_key_breakdown": {},
            "provider_breakdown": {},
        }
    
    total_estimated_cost = 0.0
    billable_estimated_cost = 0.0
    non_billable_estimated_cost = 0.0
    billable_events = 0
    non_billable_events = 0
    billable_mode_counts = {}
    tenant_costs = {}
    api_key_costs = {}
    provider_costs = {}
    
    for e in events:
        cost = e.get("estimated_cost")
        if cost is None:
            cost = 0.0
        total_estimated_cost += cost
        
        is_billable = e.get("billing_billable", False)
        if is_billable:
            billable_estimated_cost += cost
            billable_events += 1
        else:
            non_billable_estimated_cost += cost
            non_billable_events += 1
        
        billable_mode = e.get("billable_mode", "unknown")
        billable_mode_counts[billable_mode] = billable_mode_counts.get(billable_mode, 0) + 1
        
        tenant_id = e.get("tenant_id")
        if tenant_id:
            tenant_costs[tenant_id] = tenant_costs.get(tenant_id, 0.0) + cost
        
        api_key_id = e.get("api_key_id")
        if api_key_id:
            api_key_costs[api_key_id] = api_key_costs.get(api_key_id, 0.0) + cost
        
        provider = e.get("provider")
        if provider:
            provider_costs[provider] = provider_costs.get(provider, 0.0) + cost
    
    def sort_dict_by_value(d, reverse=True):
        return dict(sorted(d.items(), key=lambda x: x[1], reverse=reverse))
    
    return {
        "total_estimated_cost": round(total_estimated_cost, 6),
        "billable_estimated_cost": round(billable_estimated_cost, 6),
        "non_billable_estimated_cost": round(non_billable_estimated_cost, 6),
        "billable_events": billable_events,
        "non_billable_events": non_billable_events,
        "billable_mode_breakdown": sort_dict_by_value(billable_mode_counts),
        "tenant_breakdown": sort_dict_by_value(tenant_costs),
        "api_key_breakdown": sort_dict_by_value(api_key_costs),
        "provider_breakdown": sort_dict_by_value(provider_costs),
    }




