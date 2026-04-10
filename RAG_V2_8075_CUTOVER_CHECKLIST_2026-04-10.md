# RAG-V2 8075 Cutover Checklist — 2026-04-10

## Goal
Cut over port `8075` to **`RAG-V2 8075`** without breaking hybrid callers, nightly ingest, or operator workflows.

---

## B3.1 Compatibility checklist

### Endpoint compatibility
- [ ] `GET /health` still exists
- [ ] `GET /stats` still exists
- [ ] `POST /search` still exists
- [ ] `POST /context` still exists

### Request compatibility
- [ ] `/search` still accepts `{ "query": string, "top_k": number }`
- [ ] `/context` still accepts `{ "query": string, "max_tokens": number }`

### Response compatibility
- [ ] `/search` still returns `{ "results": [...] }`
- [ ] each `/search` result can still provide caller-usable fields
- [ ] `/context` still returns `{ "context": "..." }`
- [ ] `/health` still returns a usable status payload
- [ ] `/stats` still returns collection/service stats

### Behavior compatibility
- [ ] empty-result behavior is acceptable and non-crashing
- [ ] timeout behavior is acceptable for current callers
- [ ] error payloads are understandable during incident handling

---

## B3.2 Service registration checklist

### NSSM / Windows service
- [ ] record current `TTAiRagService` settings before changing anything
- [ ] record current `AppDirectory`
- [ ] record current script path
- [ ] record current stdout log path
- [ ] record current stderr log path
- [ ] decide whether service name stays `TTAiRagService`

### Registration update
- [ ] if runtime path changes, update `automation/register_rag_service.ps1`
- [ ] confirm new script path exists
- [ ] confirm Python executable path remains valid
- [ ] confirm NSSM path remains valid
- [ ] confirm logs still land under a predictable path

### Restart behavior
- [ ] stop old service cleanly
- [ ] register/update service once
- [ ] start new service
- [ ] confirm process is listening on `8075`

---

## B3.3 Nightly ingest checklist

### Current-state capture
- [ ] confirm what `automation/nightly-memory-and-rag.ps1` currently updates
- [ ] confirm whether current nightly job feeds the same store used by live `8075`
- [ ] record current ingest log path

### Migration decisions
- [ ] decide whether nightly ingest remains in place or is replaced
- [ ] define the new index/store path for `RAG-V2 8075`
- [ ] ensure nightly ingest feeds the runtime actually serving `8075`
- [ ] ensure no legacy-only ingest path remains silently active

### Post-cutover validation
- [ ] run nightly ingest manually once in test mode if possible
- [ ] verify new documents are visible through `8075/search` or `8075/context`
- [ ] confirm no stale-store behavior remains

---

## B3.4 Hybrid caller checklist

### `ttai_hybrid_v2.py`
- [ ] `/context` still works without caller edits
- [ ] response still includes `context`
- [ ] context arrives within current timeout tolerance
- [ ] no silent fallback to empty context on normal queries

### `ttai_hybrid_v2_fixed.py`
- [ ] `/context` still works without caller edits
- [ ] response still includes `context`
- [ ] context arrives within current timeout tolerance
- [ ] no silent regression in grounding quality

---

## B3.5 Smoke test checklist

### API surface
- [ ] `GET http://127.0.0.1:8075/health`
- [ ] `GET http://127.0.0.1:8075/stats`
- [ ] `POST http://127.0.0.1:8075/context` with a real query
- [ ] `POST http://127.0.0.1:8075/search` with a real query

### Functional tests
- [ ] a known recall query returns non-empty context
- [ ] a known recall query returns structured search results
- [ ] hybrid app still answers with `context_used=true` when appropriate
- [ ] no obvious latency spike beyond caller tolerance

### Operator tests
- [ ] service logs are readable
- [ ] restart procedure still works
- [ ] failure mode is diagnosable from logs and health endpoints

---

## B3.6 Rollback checklist
- [ ] keep legacy runtime path available
- [ ] keep legacy config/settings snapshot
- [ ] keep legacy knowledge/index location documented
- [ ] be ready to re-register the old service path
- [ ] define rollback smoke tests before cutover

---

## B3.7 Do-not-do list
- [ ] do not relabel docs first and assume runtime is done
- [ ] do not cut over without checking `/context`
- [ ] do not ignore nightly ingest alignment
- [ ] do not delete legacy runtime before successful smoke tests
- [ ] do not assume hidden `/search` consumers do not exist

---

## Recommended cutover gate
Only proceed with real cutover if all are true:
- [ ] compatibility surface confirmed
- [ ] nightly ingest aligned
- [ ] service registration path ready
- [ ] smoke tests passed
- [ ] rollback path documented and practical
