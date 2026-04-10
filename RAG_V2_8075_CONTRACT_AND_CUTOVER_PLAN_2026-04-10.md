# RAG-V2 8075 Contract and Cutover Plan — 2026-04-10

## Executive answer
**No, dependent connections will not safely auto-switch just because port 8075 keeps the same number.**
They will only keep working if the service behind `8075` preserves the contract they already expect.

After reading the current runtime and callers, the safest path is:
- keep port `8075`
- preserve `/context` compatibility first
- treat `/search` compatibility as required for any direct callers
- update service registration explicitly
- do a staged cutover with rollback ready

---

## Files inspected for B2
- `services/rag_service/rag_service.py`
- `services/rag_service/rag_engine.py`
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`
- `automation/register_rag_service.ps1`
- `automation/nightly-memory-and-rag.ps1`

---

## Current live contract on port 8075
The current service is a FastAPI app from `services/rag_service/rag_service.py`.

### Current endpoints
- `GET /health`
- `POST /search`
- `POST /context`
- `GET /stats`

### `POST /search`
#### Request body
```json
{
  "query": "string",
  "top_k": 5
}
```

#### Response body
```json
{
  "results": [
    {
      "content": "string",
      "metadata": {
        "source": "string",
        "timestamp": "string",
        "type": "string",
        "topic": "string",
        "length": 123,
        "keywords": "a|b|c"
      },
      "distance": 0.123,
      "semantic_score": 0.9,
      "lexical_score": 0.8,
      "recency_score": 0.7,
      "relevance_score": 0.85
    }
  ]
}
```

### `POST /context`
#### Request body
```json
{
  "query": "string",
  "max_tokens": 600
}
```

#### Response body
```json
{
  "context": "string"
}
```

### `GET /health`
Returns:
- `status`
- `stats`

### `GET /stats`
Returns collection stats from the engine.

---

## What the current callers actually depend on

### `ttai_hybrid_v2.py`
This caller depends on:
- `RAG_SERVICE_URL` defaulting to `http://localhost:8075`
- `POST /context`
- request body containing:
  - `query`
  - `max_tokens`
- response body containing:
  - `context`

#### Important detail
This hybrid app **does not use `/search` directly**.
It only needs `/context` to remain compatible.
If `/context` breaks, the hybrid app will silently lose contextual grounding and fall back to no-context behavior.

### `ttai_hybrid_v2_fixed.py`
Same dependency pattern as above:
- calls `POST {RAG_SERVICE_URL}/context`
- expects JSON key `context`
- timeout is short (`1.0s`)

#### Important detail
Even if schema is compatible, **latency regression** can still break behavior because the timeout is strict.
So cutover requires both:
- response shape compatibility
- similar enough latency

### `automation/register_rag_service.ps1`
This script currently registers the Windows/NSSM service using:
- service name default: `TTAiRagService`
- script path default: `services\rag_service\rag_service.py`

#### Meaning
If we want `RAG-V2 8075` to be the real runtime behind the service, this registration path must be updated deliberately, or an adapter service must remain at that path.

### `automation/nightly-memory-and-rag.ps1`
This script does **not** call port `8075` directly.
Instead it runs:
- `python .\TTAi-AI-Model\rag_engine.py`

#### Meaning
Nightly ingest is a separate migration risk.
If `RAG-V2 8075` uses a different index pipeline or storage path, this nightly script will not automatically update itself.
It must be reconciled explicitly.

---

## Main migration risks

### Risk 1 — `/context` schema break
This is the most immediate runtime risk.
If `RAG-V2 8075` changes:
- request field names
- response field name `context`
- timeout behavior
then hybrid chat on port 8005 may continue running but lose retrieval context.

### Risk 2 — service registration still pointing to legacy runtime
Even if a new `RAG-V2` implementation exists elsewhere, NSSM will keep launching the old script until registration is changed.

### Risk 3 — nightly ingest still updating old data path
If cutover happens but ingest still populates the old store or old engine path, the new runtime may appear healthy but serve stale or empty retrieval.

### Risk 4 — `/search` direct consumers may exist outside inspected callers
The two hybrid runtime files do not use `/search`, but other scripts, dashboards, or future tools may.
Therefore `/search` should remain compatible unless we prove no dependent callers exist.

### Risk 5 — parser/index assumptions remain legacy
`services/rag_service/rag_engine.py` still contains older parsing assumptions for structured memory entries.
If `RAG-V2 8075` is supposed to improve recall, simply keeping the same file and labeling it new will not produce the intended upgrade.

---

## Safe cutover design options

## Option A — Best practical path: compatibility adapter on 8075
### Idea
Keep `8075` serving the same external contract:
- same endpoints
- same request/response fields
- same service name if needed

But internally route those requests into the new `RAG-V2` engine.

### Why this is best
- minimal caller churn
- hybrid apps do not need code changes if `/context` remains stable
- rollback is simpler
- operator docs can transition gradually

### Required compatibility guarantees
- `POST /context` must still accept `{ query, max_tokens }`
- `POST /context` must still return `{ context: string }`
- `POST /search` should still accept `{ query, top_k }`
- `POST /search` should still return `{ results: [...] }`
- latency on `/context` should stay within current caller tolerance

## Option B — Explicit caller migration
### Idea
Let `RAG-V2` expose a different contract, then modify every caller.

### Why this is risky now
- more moving parts
- higher regression surface
- easy to miss hidden callers
- harder rollback

**Recommendation: do not use Option B first.**

---

## Concrete cutover sequence

### Phase 0 — Freeze and backup
1. Record current NSSM service settings for `TTAiRagService`.
2. Record current knowledge base path / persistence directory.
3. Snapshot current scripts and log locations.
4. Keep the legacy runtime available as `legacy RAG archive`.

### Phase 1 — Define compatibility surface
1. Treat this contract as mandatory for cutover:
   - `POST /context` input/output shape unchanged
   - `POST /search` input/output shape unchanged
   - `GET /health` and `GET /stats` remain available
2. Decide whether adapter layer lives:
   - inside `services/rag_service/rag_service.py`, or
   - in a replacement service script with the same external API

### Phase 2 — Prepare `RAG-V2 8075`
1. Wire new retrieval engine behind compatible handlers.
2. Ensure `context` string generation still works.
3. Ensure search results are mapped to the expected legacy result shape.
4. Ensure persistence/index path is explicit.

### Phase 3 — Reconcile nightly ingest
1. Check whether `automation/nightly-memory-and-rag.ps1` should:
   - continue feeding the new engine, or
   - be replaced by a new indexing path
2. Do not cut over until nightly refresh path matches the new runtime.

### Phase 4 — Update service registration
1. Update `automation/register_rag_service.ps1` to point to the new runtime path if needed.
2. Keep service name stable unless there is a strong reason to rename.
3. Verify stdout/stderr logs still land in a known place.

### Phase 5 — Smoke test
Minimum smoke tests before declaring success:
1. `GET /health` on `8075`
2. `POST /context` with a real query returns `{ "context": ... }`
3. `POST /search` with a real query returns `{ "results": [...] }`
4. `ttai_hybrid_v2.py` still gets context without code changes
5. `ttai_hybrid_v2_fixed.py` still gets context without timeout failures
6. Nightly ingest path updates the retrieval store actually used by `8075`

### Phase 6 — Rename docs and operator language
Only after runtime success:
- update docs to say `8075` = `RAG-V2 8075`
- label old implementation as `legacy RAG archive`
- clarify rollback path

---

## What needs explicit adjustment
### Yes, these areas likely need adjustment:
- service registration path in `automation/register_rag_service.ps1`
- nightly ingest path in `automation/nightly-memory-and-rag.ps1`
- possibly service implementation path under `services/rag_service/`
- any direct `/search` consumers not yet audited

### What may not need adjustment if compatibility is preserved
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`

But only if `/context` stays contract-compatible and fast enough.

---

## Decision recommendation
**Recommended cutover policy:**
- do not change port number
- do not force caller rewrites first
- replace the engine behind `8075` through a compatibility-preserving wrapper
- migrate nightly ingest explicitly
- keep legacy runtime available for rollback/archive

---

## Bottom line
The transition will break things if handled as a simple label or port swap.
The safe path is a **contract-preserving, staged cutover** where `8075` keeps behaving the same externally while the engine behind it becomes `RAG-V2 8075`.
