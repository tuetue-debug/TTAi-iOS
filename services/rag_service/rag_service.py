import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from rag_engine import RAGEngine  # noqa: E402
from compatibility_adapter import CompatibilityAdapter  # noqa: E402
from rag_v2_backend import RAGV2ShadowBackend  # noqa: E402
from rag_service_config import (  # noqa: E402
    RAG_KB_PATH,
    RAG_PUBLIC_HOST,
    RAG_PUBLIC_PORT,
    compatibility_surface_metadata,
    get_backend_name,
    get_service_mode,
)

app = FastAPI(title="TTAi RAG Service", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KNOWLEDGE_DIR = Path(RAG_KB_PATH)
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
legacy_engine = RAGEngine(persist_directory=str(KNOWLEDGE_DIR))
adapter = CompatibilityAdapter()
_backend_boot_error = None
BUILD_MARKER = "rag-service-build-d68cd55-marker-1"

try:
    rag_v2_shadow_backend = RAGV2ShadowBackend(WORKSPACE_ROOT)
except Exception as exc:
    rag_v2_shadow_backend = None
    _backend_boot_error = f"{type(exc).__name__}: {exc}"


def get_backend_engine():
    desired_backend = str(get_backend_name()).lower()
    if desired_backend in {"rag_v2", "rag-v2", "shadow", "rag_v2_shadow"}:
        if rag_v2_shadow_backend is not None:
            return rag_v2_shadow_backend
        return legacy_engine
    return legacy_engine


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class ContextRequest(BaseModel):
    query: str
    max_tokens: int = 600


@app.get("/health")
def health():
    engine = get_backend_engine()
    if hasattr(engine, "get_collection_stats"):
        stats = engine.get_collection_stats()
    else:
        stats = engine.stats()
    return adapter.map_health(
        stats,
        extra={
            "service_mode": get_service_mode(),
            "backend": get_backend_name(),
            "backend_boot_error": _backend_boot_error,
            "backend_active": type(engine).__name__,
            "env_backend_raw": os.environ.get("TTAI_RAG_BACKEND"),
            "env_service_mode_raw": os.environ.get("TTAI_RAG_SERVICE_MODE"),
            "build_marker": BUILD_MARKER,
        },
    )


@app.post("/search")
def search(request: SearchRequest):
    engine = get_backend_engine()
    if hasattr(engine, "get_context_for_query"):
        results = engine.search(request.query, n_results=request.top_k)
    else:
        results = engine.search(request.query, top_k=request.top_k)
    return adapter.map_search_results(results)


@app.post("/context")
def context(request: ContextRequest):
    engine = get_backend_engine()
    if hasattr(engine, "get_context_for_query"):
        context_text = engine.get_context_for_query(request.query, max_tokens=request.max_tokens)
    else:
        context_text = engine.context(request.query, max_tokens=request.max_tokens)
    return adapter.map_context_result(context_text)


@app.get("/stats")
def stats():
    engine = get_backend_engine()
    if hasattr(engine, "get_collection_stats"):
        return engine.get_collection_stats()
    return engine.stats()


@app.get("/compatibility")
def compatibility():
    payload = compatibility_surface_metadata()
    payload["backend_boot_error"] = _backend_boot_error
    payload["backend_active"] = type(get_backend_engine()).__name__
    payload["env_backend_raw"] = os.environ.get("TTAI_RAG_BACKEND")
    payload["env_service_mode_raw"] = os.environ.get("TTAI_RAG_SERVICE_MODE")
    payload["build_marker"] = BUILD_MARKER
    return payload


@app.get("/build-proof")
def build_proof():
    return {
        "proof": BUILD_MARKER,
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "file": __file__,
    }


if __name__ == "__main__":
    uvicorn.run(app, host=RAG_PUBLIC_HOST, port=RAG_PUBLIC_PORT)
