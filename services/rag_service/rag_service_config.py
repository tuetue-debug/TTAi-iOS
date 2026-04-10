import os
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def get_public_port() -> int:
    return int(os.environ.get("TTAI_RAG_PORT", "8075"))


def get_public_host() -> str:
    return os.environ.get("TTAI_RAG_HOST", "0.0.0.0")


def get_service_mode() -> str:
    return os.environ.get("TTAI_RAG_SERVICE_MODE", "compatibility-surface")


def get_backend_name() -> str:
    return os.environ.get("TTAI_RAG_BACKEND", "legacy")


def get_collection_name() -> str:
    return os.environ.get("TTAI_RAG_COLLECTION_NAME", "ttai_knowledge")


def get_kb_path() -> Path:
    return Path(os.environ.get("TTAI_KB_PATH") or (WORKSPACE_ROOT / "knowledge_base"))


def get_ingest_script() -> str:
    return os.environ.get("TTAI_RAG_INGEST_SCRIPT", ".\\TTAi-AI-Model\\rag_engine.py")


def get_service_entrypoint() -> str:
    return os.environ.get("TTAI_RAG_SERVICE_ENTRYPOINT", "services\\rag_service\\rag_service.py")


RAG_PUBLIC_PORT = get_public_port()
RAG_PUBLIC_HOST = get_public_host()
RAG_SERVICE_MODE = get_service_mode()
RAG_BACKEND = get_backend_name()
RAG_COLLECTION_NAME = get_collection_name()
RAG_KB_PATH = get_kb_path()
RAG_INGEST_SCRIPT = get_ingest_script()
RAG_SERVICE_ENTRYPOINT = get_service_entrypoint()


def compatibility_surface_metadata() -> dict:
    return {
        "public_port": get_public_port(),
        "public_host": get_public_host(),
        "service_mode": get_service_mode(),
        "backend": get_backend_name(),
        "collection_name": get_collection_name(),
        "persist_directory": str(get_kb_path()),
        "service_entrypoint": get_service_entrypoint(),
        "ingest_script": get_ingest_script(),
    }
