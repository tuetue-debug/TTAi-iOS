import os
import traceback

os.environ['TTAI_RAG_BACKEND'] = 'rag_v2'
os.environ['TTAI_RAG_SERVICE_MODE'] = 'compatibility-surface'

try:
    import rag_service  # noqa: F401
    print('IMPORT_OK')
    engine = rag_service.get_backend_engine()
    print('BACKEND_ENGINE_TYPE=', type(engine).__name__)
    if hasattr(engine, 'stats'):
        print('STATS=', engine.stats())
    else:
        print('STATS=', engine.get_collection_stats())
except Exception as exc:
    print('IMPORT_FAILED')
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise
