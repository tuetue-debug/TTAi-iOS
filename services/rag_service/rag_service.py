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

app = FastAPI(title="TTAi RAG Service", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb_override = os.environ.get("TTAI_KB_PATH")
if kb_override:
    KNOWLEDGE_DIR = Path(kb_override)
else:
    KNOWLEDGE_DIR = WORKSPACE_ROOT / "knowledge_base"

KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
engine = RAGEngine(persist_directory=str(KNOWLEDGE_DIR))


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class ContextRequest(BaseModel):
    query: str
    max_tokens: int = 600


@app.get("/health")
def health():
    stats = engine.get_collection_stats()
    return {
        "status": "ok" if stats.get("document_count") else "empty",
        "stats": stats
    }


@app.post("/search")
def search(request: SearchRequest):
    results = engine.search(request.query, n_results=request.top_k)
    return {"results": results}


@app.post("/context")
def context(request: ContextRequest):
    context_text = engine.get_context_for_query(request.query, max_tokens=request.max_tokens)
    return {"context": context_text}


@app.get("/stats")
def stats():
    return engine.get_collection_stats()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8075)
