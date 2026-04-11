"""
TTAi Hybrid System v2.0 - FIXED VERSION
With Direct API Integration (DeepSeek + Gemini) + FALLBACK MECHANISM
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
import random
import time
import json
import unicodedata
import os
from typing import Optional, List
from pathlib import Path
from api_keys_config import config

app = FastAPI(title="TTAi Hybrid System v2.0 - Fixed")

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
    model: str = ""
    user_id: str = "anonymous"

class ChatResponse(BaseModel):
    response: str
    model_used: str
    provider_type: str
    processing_time: float
    fallback_used: bool = False
    context_used: bool = False

class ProviderInfo(BaseModel):
    name: str
    type: str
    endpoint: str
    enabled: bool
    cost_per_token: float = 0.0
    avg_response_time: float = 2.0

# Provider configuration
PROVIDERS = [
    # Local Ollama (free, slow ~20-30s)
    ProviderInfo(name="gemma3:4b", type="local_ollama", endpoint="http://localhost:11434", enabled=False, cost_per_token=0.0, avg_response_time=25.0),
    ProviderInfo(name="qwen3:4b", type="local_ollama", endpoint="http://localhost:11434", enabled=False, cost_per_token=0.0, avg_response_time=30.0),
    ProviderInfo(name="deepseek-r1:8b", type="local_ollama", endpoint="http://localhost:11434", enabled=False, cost_per_token=0.0, avg_response_time=35.0),
    
    # Remote Ollama (vannt-work-op)
    ProviderInfo(name="gemma3:4b-remote", type="remote_ollama", endpoint="http://100.89.201.7:11434", enabled=True, cost_per_token=0.0, avg_response_time=15.0),
    # Remote FastAPI (vannt-work-op)
    ProviderInfo(name="ttai-remote-fastapi", type="remote_fastapi", endpoint="http://100.89.201.7:8000", enabled=True, cost_per_token=0.0, avg_response_time=5.0),
    
    # Cloud APIs (fast, paid)
    ProviderInfo(name="deepseek-chat", type="deepseek_api", endpoint=config.DEEPSEEK_API_URL, enabled=bool(config.DEEPSEEK_API_KEY), cost_per_token=0.0001, avg_response_time=2.0),
    ProviderInfo(name="gemini-flash-latest", type="gemini_api", endpoint=config.GEMINI_API_URL, enabled=bool(config.GEMINI_API_KEY), cost_per_token=0.00005, avg_response_time=1.5),
    ProviderInfo(name="gemini-2.5-pro", type="gemini_api", endpoint=config.GEMINI_API_URL, enabled=bool(config.GEMINI_API_KEY), cost_per_token=0.00015, avg_response_time=3.0),
]

METRICS_DIR = (Path(__file__).resolve().parent / "logs")
METRICS_FILE = METRICS_DIR / "provider_metrics.jsonl"
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8075")


def log_provider_metric(provider: ProviderInfo, status: str, latency: float, message: str, extra: dict | None = None):
    try:
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": time.time(),
            "provider": provider.name,
            "provider_type": provider.type,
            "status": status,
            "latency_ms": round(latency * 1000, 2),
            "cost_per_token": provider.cost_per_token,
            "message_chars": len(message),
        }
        if extra:
            payload.update(extra)
        with METRICS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as log_err:
        print(f"[metrics] failed to log provider metric: {log_err}")


async def fetch_rag_context(query: str, max_tokens: int = 600) -> str:
    if not RAG_SERVICE_URL:
        return ""
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.post(
                f"{RAG_SERVICE_URL}/context",
                json={"query": query, "max_tokens": max_tokens}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("context", "")
    except Exception as exc:
        print(f"[RAG] context fetch failed: {exc}")
    return ""

def normalize_text(text: str) -> str:
    """Normalize text for comparison (remove diacritics, lowercase)"""
    # Normalize Unicode
    text = unicodedata.normalize('NFKD', text)
    # Remove diacritics
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return text.lower()

def select_provider(message: str, requested_model: str = "") -> ProviderInfo:
    """Intelligent provider selection with fallback logic"""
    
    # If model specified, use it
    if requested_model:
        for provider in PROVIDERS:
            if provider.name == requested_model and provider.enabled:
                print(f"Using requested model: {provider.name}")
                return provider
    
    # Normalize message for Vietnamese text processing
    message_normalized = normalize_text(message)
    
    # STRATEGY 1: Code queries -> DeepSeek (best for code)
    code_keywords = ["code", "python", "viet", "ham", "chuong trinh", "lap trinh", "algorithm", "html", "css", "javascript", "program"]
    if any(word in message_normalized for word in code_keywords):
        # Try DeepSeek API first
        deepseek_providers = [p for p in PROVIDERS if "deepseek" in p.name.lower() and p.enabled]
        if deepseek_providers:
            print(f"Code query -> DeepSeek: {deepseek_providers[0].name}")
            return deepseek_providers[0]
    
    # STRATEGY 2: Complex reasoning -> Gemini Pro (most capable)
    complex_keywords = ["phuc tap", "he thong", "kien truc", "phan tich", "so sanh", "danh gia", "giai thich", "machine learning", "ai"]
    if any(word in message_normalized for word in complex_keywords):
        gemini_pro_providers = [p for p in PROVIDERS if "gemini-2.5-pro" in p.name and p.enabled]
        if gemini_pro_providers:
            print(f"Complex query -> Gemini Pro: {gemini_pro_providers[0].name}")
            return gemini_pro_providers[0]
    
    # STRATEGY 3: Fast responses -> Gemini Flash (fastest)
    fast_keywords = ["nhanh", "gap", "urgent", "quick", "simple", "hello", "xin chao", "chao"]
    if any(word in message_normalized for word in fast_keywords):
        gemini_flash_providers = [p for p in PROVIDERS if "flash" in p.name and p.enabled]
        if gemini_flash_providers:
            print(f"Fast query -> Gemini Flash: {gemini_flash_providers[0].name}")
            return gemini_flash_providers[0]
    
    # STRATEGY 4: Medium queries -> Remote Ollama (balanced)
    if len(message_normalized) > 50 and len(message_normalized) < 200:
        remote_ollama_providers = [p for p in PROVIDERS if "remote" in p.name and p.enabled]
        if remote_ollama_providers:
            print(f"Medium query -> Remote Ollama: {remote_ollama_providers[0].name}")
            return remote_ollama_providers[0]
    
    # DEFAULT: Prefer Gemini Flash latest, then DeepSeek, then local Ollama
    api_flash = next((p for p in PROVIDERS if p.name == "gemini-flash-latest" and p.enabled), None)
    if api_flash:
        print(f"Default -> Gemini Flash: {api_flash.name}")
        return api_flash

    deepseek_provider = next((p for p in PROVIDERS if p.name == "deepseek-chat" and p.enabled), None)
    if deepseek_provider:
        print(f"Default -> DeepSeek API: {deepseek_provider.name}")
        return deepseek_provider

    local_providers = [p for p in PROVIDERS if p.type == "local_ollama" and p.enabled]
    if local_providers:
        print(f"Default -> Local Ollama: {local_providers[0].name}")
        return local_providers[0]

    # Fallback to any enabled provider
    enabled_providers = [p for p in PROVIDERS if p.enabled]
    if enabled_providers:
        print(f"Fallback -> {enabled_providers[0].name}")
        return enabled_providers[0]

    raise Exception("No enabled providers available")

async def execute_provider(provider: ProviderInfo, message: str, user_id: str) -> str:
    start_time = time.time()
    try:
        if provider.type == "local_ollama":
            result = await call_local_ollama(provider, message)
        elif provider.type == "remote_ollama":
            result = await call_remote_ollama(provider, message)
        elif provider.type == "deepseek_api":
            result = await call_deepseek_api(provider, message, user_id)
        elif provider.type == "gemini_api":
            result = await call_gemini_api(provider, message)
        elif provider.type == "remote_fastapi":
            result = await call_remote_fastapi(provider, message, user_id)
        else:
            raise Exception(f"Unknown provider type: {provider.type}")
        latency = time.time() - start_time
        log_provider_metric(provider, "success", latency, message)
        return result
    except Exception as exc:
        latency = time.time() - start_time
        log_provider_metric(provider, "failure", latency, message, {"error": str(exc)})
        raise


async def call_provider_with_fallback(provider: ProviderInfo, message: str, user_id: str) -> tuple[str, str, bool]:
    """Call provider with fallback mechanism that tries all enabled providers."""
    attempted: set[str] = set()
    candidates: list[ProviderInfo] = [provider] + [p for p in PROVIDERS if p.enabled and p.name != provider.name]

    last_error: Optional[Exception] = None
    for candidate in candidates:
        if candidate.name in attempted or not candidate.enabled:
            continue
        attempted.add(candidate.name)
        try:
            response = await execute_provider(candidate, message, user_id)
            fallback_used = candidate.name != provider.name
            return response, candidate.name, fallback_used
        except Exception as exc:
            print(f"{candidate.name} failed: {repr(exc)}")
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise Exception("No enabled providers available")

async def call_local_ollama(provider: ProviderInfo, message: str) -> str:
    """Call local Ollama with timeout"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": provider.name,
            "prompt": message,
            "stream": False
        }
        response = await client.post(f"{provider.endpoint}/api/generate", json=payload)
        response.raise_for_status()
        return response.json()["response"]

async def call_remote_ollama(provider: ProviderInfo, message: str) -> str:
    """Call remote Ollama with timeout"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        payload = {
            "model": "gemma3:4b",
            "prompt": message,
            "stream": False
        }
        response = await client.post(f"{provider.endpoint}/api/generate", json=payload)
        response.raise_for_status()
        return response.json()["response"]

async def call_remote_fastapi(provider: ProviderInfo, message: str, user_id: str) -> str:
    """Call remote FastAPI endpoint with timeout"""
    async with httpx.AsyncClient(timeout=25.0) as client:
        payload = {
            "message": message,
            "model": "",
            "user_id": user_id
        }
        response = await client.post(f"{provider.endpoint}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["response"]

async def call_deepseek_api(provider: ProviderInfo, message: str, user_id: str) -> str:
    """Call DeepSeek API with timeout"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {
            "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message}],
            "stream": False,
            "user": user_id
        }
        response = await client.post(f"{provider.endpoint}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

async def call_gemini_api(provider: ProviderInfo, message: str) -> str:
    """Call Gemini API with timeout"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        model_name = provider.name
        url = f"{provider.endpoint}/v1beta/models/{model_name}:generateContent?key={config.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": message}]
            }]
        }
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

# Chat endpoint with full hybrid support and fallback
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    
    try:
        # Select provider intelligently
        provider = select_provider(request.message, request.model)
        
        # Fetch RAG context
        rag_context = await fetch_rag_context(request.message)
        message_payload = request.message
        if rag_context:
            message_payload = (
                "You are TTAi with access to internal knowledge. Use the provided context to answer\n"
                f"Context:\n{rag_context}\n\nQuestion: {request.message}\nAnswer:"
            )
        
        # Call provider with fallback mechanism
        response_text, model_used, fallback_used = await call_provider_with_fallback(provider, message_payload, request.user_id)
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            model_used=model_used,
            provider_type=provider.type,
            processing_time=processing_time,
            fallback_used=fallback_used,
            context_used=bool(rag_context)
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error after {processing_time:.2f}s: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# Health check endpoint
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "TTAi Hybrid System v2.0 - Fixed",
        "version": "2.0.1",
        "features": ["Local Ollama", "Remote Ollama", "DeepSeek API", "Gemini API", "Smart Load Balancing", "Fallback Mechanism"],
        "providers_enabled": [p.name for p in PROVIDERS if p.enabled]
    }

# Provider status endpoint
@app.get("/providers")
async def get_providers():
    return {
        "providers": [
            {
                "name": p.name,
                "type": p.type,
                "enabled": p.enabled,
                "endpoint": p.endpoint
            }
            for p in PROVIDERS
        ]
    }

if __name__ == "__main__":
    print("=" * 60)
    print("TTAi Hybrid System v2.0 - Fixed")
    print("With Fallback Mechanism and Vietnamese Text Processing")
    print("=" * 60)
    
    # Print available providers
    enabled_providers = [p.name for p in PROVIDERS if p.enabled]
    print(f"Enabled providers: {', '.join(enabled_providers)}")
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8005)