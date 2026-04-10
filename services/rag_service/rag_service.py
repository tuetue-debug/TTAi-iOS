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
from rag_service_config import (  # noqa: E402
    RAG_BACKEND,
    RAG_KB_PATH,
    RAG_PUBLIC_HOST,
    RAG_PUBLIC_PORT,
    RAG_SERVICE_MODE,
    compatibility_surface_metadata,
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
engine = RAGEngine(persist_directory=str(KNOWLEDGE_DIR))
adapter = CompatibilityAdapter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class ContextRequest(BaseModel):
    query: str
    max_tokens: int = 600


@app.get("/health")
def health():
    stats = engine.get_collection_stats()
    return adapter.map_health(
        stats,
        extra={
            "service_mode": RAG_SERVICE_MODE,
            "backend": RAG_BACKEND,
        },
    )


@app.post("/search")
def search(request: SearchRequest):
    results = engine.search(request.query, n_results=request.top_k)
    return adapter.map_search_results(results)


@app.post("/context")
def context(request: ContextRequest):
    context_text = engine.get_context_for_query(request.query, max_tokens=request.max_tokens)
    return adapter.map_context_result(context_text)


@app.get("/stats")
def stats():
    return engine.get_collection_stats()


@app.get("/compatibility")
def compatibility():
    return compatibility_surface_metadata()


if __name__ == "__main__":
    uvicorn.run(app, host=RAG_PUBLIC_HOST, port=RAG_PUBLIC_PORT)
