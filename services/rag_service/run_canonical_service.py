import os
import uvicorn

os.environ.setdefault('TTAI_RAG_SERVICE_MODE', 'compatibility-surface')
os.environ.setdefault('TTAI_RAG_BACKEND', 'rag_v2')
os.environ.setdefault('TTAI_RAG_PORT', '8075')

import rag_service  # noqa: E402

if __name__ == '__main__':
    uvicorn.run(rag_service.app, host='0.0.0.0', port=int(os.environ['TTAI_RAG_PORT']))
