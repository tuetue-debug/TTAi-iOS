from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
USAGE_EVENTS_PATH = BASE_DIR / "data" / "usage_events.jsonl"
USAGE_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)

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
async def chat(request: ChatRequest):
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
        usage_event = {
            "event_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": "api_chat",
            "request_path": "/api/chat",
            "user_id": user_id,
            "tenant_id": None,
            "api_key_id": None,
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
            "quota_billable": True,
            "billing_billable": False,
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
        final_status = "error"
        final_http_status = e.status_code
        error_detail = str(e.detail)
        processing_time = time.time() - start_time
        user_id = request.user_id if hasattr(request, 'user_id') else 'anonymous'
        input_tokens_est = estimate_tokens(request.message)
        total_tokens_est = input_tokens_est
        event_model = provider.model if provider else None
        cost_info = estimate_cost(event_model, total_tokens_est, provider_type)
        usage_event = {
            "event_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": "api_chat",
            "request_path": "/api/chat",
            "user_id": user_id,
            "tenant_id": None,
            "api_key_id": None,
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
            "quota_billable": True,
            "billing_billable": False,
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
        usage_event = {
            "event_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "channel": "api_chat",
            "request_path": "/api/chat",
            "user_id": user_id,
            "tenant_id": None,
            "api_key_id": None,
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
            "quota_billable": True,
            "billing_billable": False,
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
async def admin_usage_events(
    limit: int = Query(default=100, ge=1, le=1000),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    request_path: Optional[str] = None,
):
    events = read_usage_events(limit=1000)
    filtered = filter_usage_events(
        events,
        user_id=user_id,
        status=status,
        provider=provider,
        model=model,
        request_path=request_path,
    )
    return {
        "count": min(len(filtered), limit),
        "filters": {
            "user_id": user_id,
            "status": status,
            "provider": provider,
            "model": model,
            "request_path": request_path,
        },
        "events": filtered[:limit],
    }


@app.get("/api/admin/usage/summary")
async def admin_usage_summary(
    limit: int = Query(default=500, ge=1, le=5000),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    request_path: Optional[str] = None,
):
    events = read_usage_events(limit=limit)
    filtered = filter_usage_events(
        events,
        user_id=user_id,
        status=status,
        provider=provider,
        model=model,
        request_path=request_path,
    )
    return {
        "filters": {
            "user_id": user_id,
            "status": status,
            "provider": provider,
            "model": model,
            "request_path": request_path,
        },
        "summary": summarize_usage_events(filtered),
    }


@app.get("/api/admin/usage/users/{target_user_id}")
async def admin_usage_by_user(
    target_user_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    request_path: Optional[str] = None,
):
    events = read_usage_events(limit=1000)
    filtered = filter_usage_events(
        events,
        user_id=target_user_id,
        status=status,
        provider=provider,
        model=model,
        request_path=request_path,
    )
    return {
        "user_id": target_user_id,
        "count": min(len(filtered), limit),
        "filters": {
            "status": status,
            "provider": provider,
            "model": model,
            "request_path": request_path,
        },
        "summary": summarize_usage_events(filtered),
        "events": filtered[:limit],
    }

# Query Classification endpoints
@app.post("/api/classify", response_model=ClassificationResponse)
async def classify_query(request: ClassificationRequest):
    """Classify a query without processing it"""
    classification = query_classifier.classify(request.query)
    return ClassificationResponse(**classification.to_dict())

@app.post("/api/classify/batch")
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
async def get_loadbalancer_metrics():
    """Get load balancer metrics"""
    return LoadBalancerMetrics(**load_balancer.get_metrics())

@app.get("/api/loadbalancer/providers")
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
async def disable_provider(provider_name: str):
    """Disable a provider"""
    success = load_balancer.disable_provider(provider_name)
    if success:
        return {"message": f"Provider {provider_name} disabled"}
    else:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

@app.post("/api/loadbalancer/providers/{provider_name}/enable")
async def enable_provider(provider_name: str):
    """Enable a provider"""
    success = load_balancer.enable_provider(provider_name)
    if success:
        return {"message": f"Provider {provider_name} enabled"}
    else:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

# Model Management endpoints
@app.get("/api/models/status")
async def get_models_status():
    """Get status of all models"""
    return model_manager.get_all_status()

@app.get("/api/models/status/{model_name}", response_model=ModelStatusResponse)
async def get_model_status(model_name: str):
    """Get status of a specific model"""
    status = model_manager.get_model_status(model_name)
    if status:
        return ModelStatusResponse(**status)
    else:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

@app.post("/api/models/warmup/{model_name}")
async def warmup_model(model_name: str, timeout: int = 30):
    """Manually warm up a model"""
    success = await model_manager.warmup_model(model_name, timeout)
    if success:
        return {"message": f"Model {model_name} warmed up successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to warm up model {model_name}")

@app.post("/api/models/warmup/all")
async def warmup_all_models(timeout_per_model: int = 30):
    """Warm up all models"""
    results = await model_manager.warmup_all(timeout_per_model)
    successful = sum(1 for success in results.values() if success)
    return {
        "message": f"Warmed up {successful}/{len(results)} models",
        "results": results
    }

# User management endpoints (placeholder)
@app.get("/api/users")
async def get_users():
    return {"users": []}

@app.post("/api/users")
async def create_user():
    return {"message": "User created (placeholder)"}

# Ollama endpoints (Step 7 - Hybrid AI Pipeline)
@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get list of available Ollama models"""
    try:
        models = await ollama_service.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Ollama models: {str(e)}")

@app.get("/api/ollama/health")
async def ollama_health():
    """Check Ollama service health"""
    is_healthy = await ollama_service.health_check()
    return {"status": "healthy" if is_healthy else "unhealthy", "service": "ollama"}

@app.post("/api/ollama/generate", response_model=OllamaResponse)
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
async def hybrid_chat(request: ChatRequest):
    """
    Legacy hybrid endpoint - uses new load balancing system
    """
    return await chat(request)

# Test endpoints
@app.get("/api/test/classification")
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
async def test_loadbalancer():
    return {"message": "Load balancer test endpoint"}


# Control Dashboard Proxy
from fastapi import HTTPException, Depends
import httpx
from auth import get_current_admin_user

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



