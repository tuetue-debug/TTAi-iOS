# RAG-V2 8075 Live Contract Results — 2026-04-10

## Scope
This document records the actual live responses observed from the current service on port `8075` before any real cutover.

---

## Live sample: `GET /health`
### Observed response
```json
{
  "status": "ok",
  "stats": {
    "document_count": 539,
    "persist_directory": "E:\\openclaw-knowledge_base",
    "collection_name": "ttai_knowledge",
    "status": "active"
  }
}
```

### Conclusion
- `/health` is a rich health payload, not a minimal ping.
- It exposes runtime/store metadata and should remain useful after cutover.

---

## Live sample: `GET /stats`
### Observed response
```json
{
  "document_count": 539,
  "persist_directory": "E:\\openclaw-knowledge_base",
  "collection_name": "ttai_knowledge",
  "status": "active"
}
```

### Conclusion
- Current 8075 runtime uses a real persistent store.
- Current persistence path is `E:\openclaw-knowledge_base`.
- Current collection is `ttai_knowledge`.
- Any real cutover must preserve or deliberately migrate this data contract.

---

## Live sample: `POST /search`
### Observed contract shape
```json
{
  "results": [
    {
      "content": "string",
      "metadata": {
        "source": "string",
        "type": "string"
      },
      "distance": 0.0,
      "semantic_score": 0.0,
      "lexical_score": 0.0,
      "recency_score": 0.0,
      "relevance_score": 0.0
    }
  ]
}
```

### Notes
- Actual response included populated values and memory content.
- Search results are metadata-rich and ranking-aware.
- This is not a minimal search API.

### Conclusion
- `RAG-V2 8075` should preserve this result envelope or map into it.
- Any caller relying on score/debug fields could break if they disappear.

---

## Live sample: `POST /context`
### Observed response
```json
{
  "context": ""
}
```

### Conclusion
- `/context` contract is confirmed live as `{ "context": string }`.
- Empty string is an accepted current behavior.
- Hybrid callers are therefore already tolerant of empty context and must remain tolerant after cutover.
- However, a cutover that increases empty-context frequency would still be a quality regression even if schema compatibility is preserved.

---

## Final B4 verdict

### Confirmed current live contract on 8075
- `GET /health` -> rich health JSON with nested `stats`
- `GET /stats` -> store/runtime stats JSON
- `POST /search` -> `{ "results": [...] }` with rich result objects
- `POST /context` -> `{ "context": "..." }`

### Confirmed current live data contract
- persistence path: `E:\openclaw-knowledge_base`
- collection: `ttai_knowledge`
- runtime status: active
- document count at sample time: `539`

### What this means for cutover
A safe cutover to **`RAG-V2 8075`** must preserve:
1. endpoint presence
2. request/response compatibility
3. useful search-result field mapping
4. data-store continuity or explicit migration
5. acceptable `/context` latency and quality

### Practical readiness verdict
- **Schema readiness:** mostly clear
- **Service registration readiness:** still requires explicit update work
- **Nightly ingest readiness:** still requires explicit alignment work
- **Cutover readiness today:** **not ready for blind swap**
- **Recommended mode:** staged contract-preserving migration with rollback
