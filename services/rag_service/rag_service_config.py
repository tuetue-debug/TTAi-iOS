import os
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

RAG_PUBLIC_PORT = int(os.environ.get("TTAI_RAG_PORT", "8075"))
RAG_PUBLIC_HOST = os.environ.get("TTAI_RAG_HOST", "0.0.0.0")
RAG_SERVICE_MODE = os.environ.get("TTAI_RAG_SERVICE_MODE", "legacy")
RAG_BACKEND = os.environ.get("TTAI_RAG_BACKEND", "legacy")
RAG_COLLECTION_NAME = os.environ.get("TTAI_RAG_COLLECTION_NAME", "ttai_knowledge")
RAG_KB_PATH = Path(os.environ.get("TTAI_KB_PATH") or (WORKSPACE_ROOT / "knowledge_base"))
RAG_INGEST_SCRIPT = os.environ.get("TTAI_RAG_INGEST_SCRIPT", ".\\TTAi-AI-Model\\rag_engine.py")
RAG_SERVICE_ENTRYPOINT = os.environ.get("TTAI_RAG_SERVICE_ENTRYPOINT", "services\\rag_service\\rag_service.py")


def compatibility_surface_metadata() -> dict:
    return {
        "public_port": RAG_PUBLIC_PORT,
        "public_host": RAG_PUBLIC_HOST,
        "service_mode": RAG_SERVICE_MODE,
        "backend": RAG_BACKEND,
        "collection_name": RAG_COLLECTION_NAME,
        "persist_directory": str(RAG_KB_PATH),
        "service_entrypoint": RAG_SERVICE_ENTRYPOINT,
        "ingest_script": RAG_INGEST_SCRIPT,
    }
