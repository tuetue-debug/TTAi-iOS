# RAG-V2 8075 Implementation Plan — 2026-04-10

## Goal
Promote port `8075` to the operational identity **`RAG-V2 8075`** without breaking existing callers, while preserving rollback safety and data continuity.

---

## Executive implementation policy
### We will NOT do a blind swap.
### We WILL do a contract-preserving, data-store-aware cutover.

That means:
- keep port `8075`
- preserve current external endpoint contract
- explicitly manage persistence/index path
- explicitly update service registration and nightly ingest
- preserve rollback path to `legacy RAG archive`

---

## B5.1 Files that likely need changes

### Runtime/API layer
1. `services/rag_service/rag_service.py`
   - Either becomes the compatibility wrapper for `RAG-V2 8075`
   - Or delegates to a new RAG-V2 engine while preserving endpoint contract

2. `services/rag_service/rag_engine.py`
   - If reused, must be clearly classified as legacy or upgraded implementation
   - If replaced, it should not silently remain the active engine under old assumptions

3. Possible new file(s)
   - `services/rag_service/rag_v2_adapter.py`
   - `services/rag_service/rag_v2_engine.py`
   - or similar split to keep compatibility logic separate from new retrieval internals

### Service management
4. `automation/register_rag_service.ps1`
   - update service target path if runtime entrypoint changes
   - document service identity explicitly as the live 8075 runtime

### Ingest / indexing
5. `automation/nightly-memory-and-rag.ps1`
   - update if current nightly ingest does not feed the store used by `RAG-V2 8075`
   - remove ambiguity between old ingest path and new runtime store

### Hybrid callers
6. `ttai_hybrid_v2.py`
7. `ttai_hybrid_v2_fixed.py`
   - ideally no changes if compatibility is preserved
   - only touch these if `/context` behavior or timeout handling must be adjusted

### Documentation/runbooks
8. `TTAi_HYBRID_RUNTIME_TRACE_MAP.md`
9. `TTAi_SYSTEM_MAP_AND_CHEATSHEET.md`
10. `MEMORY_SYSTEM_AUDIT_2026-04-07.md`
11. `MEMORY_REINDEX_AND_GEMMA_FLOW_2026-04-07.md`
12. `MEMORY_RAG_GEMMA_UPGRADE_PLAN_2026-04-07.md`
   - update only after runtime cutover is validated

---

## B5.2 Recommended architecture for cutover

## Preferred design: compatibility wrapper on 8075
Keep `services/rag_service/rag_service.py` as the public HTTP surface for `8075`.

### Inside that wrapper
- `/health` stays stable
- `/stats` stays stable
- `/search` stays stable
- `/context` stays stable

### Behind the wrapper
- plug in `RAG-V2` retrieval internals
- map new result format back to current legacy response shape when necessary
- keep data-store path explicit and configurable

### Why this is best
- minimizes caller changes
- keeps service registration simple
- makes rollback easier
- preserves operator muscle memory

---

## B5.3 Implementation phases

### Phase A — Prepare compatibility wrapper
#### Tasks
- decide whether current `rag_service.py` remains the wrapper
- introduce explicit adapter boundary between HTTP contract and retrieval engine
- define mapping rules from `RAG-V2` internals to legacy `/search` and `/context` outputs

#### Deliverables
- wrapper design note
- adapter implementation stub
- explicit config variables for engine/store selection

---

### Phase B — Define data-store strategy
#### Must decide
- Will `RAG-V2 8075` continue using `E:\openclaw-knowledge_base`?
- Will it continue using collection `ttai_knowledge`?
- Or will it use a new store and require migration/reindex?

### Recommendation
Prefer one of these two safe options:

#### Option 1 — Same store, upgraded engine
- simplest runtime migration path
- highest continuity
- may inherit some legacy baggage

#### Option 2 — New store + compatibility wrapper + planned reindex
- cleaner architecture
- higher migration complexity
- requires explicit cutover and rollback design

### Near-term recommendation
Start with **Option 1 if compatible**, because it reduces risk.

---

### Phase C — Align ingest pipeline
#### Tasks
- inspect whether `automation/nightly-memory-and-rag.ps1` updates the live store used by 8075
- if not, create or update a nightly ingest path for `RAG-V2 8075`
- make ingest target explicit in script/config

#### Deliverables
- one canonical nightly ingest path
- no parallel ambiguous ingest paths feeding different stores unnoticed

---

### Phase D — Update service registration
#### Tasks
- decide final service entrypoint
- update `automation/register_rag_service.ps1` if entrypoint changes
- preserve or document service name `TTAiRagService`
- preserve stdout/stderr logs

#### Deliverables
- one clear registration path
- restart procedure note

---

### Phase E — Validate hybrid callers
#### Tasks
- verify `ttai_hybrid_v2.py` still receives usable context
- verify `ttai_hybrid_v2_fixed.py` still receives usable context
- verify timeout behavior remains acceptable

#### Deliverables
- caller validation notes
- any caller patch only if compatibility proves insufficient

---

### Phase F — Cutover + smoke test
#### Tasks
- deploy wrapper/engine
- restart service
- run health/stats/search/context tests
- run at least one hybrid path test
- validate logs

#### Deliverables
- cutover record
- smoke test record

---

### Phase G — Rollback safety
#### Tasks
- keep legacy runtime path and config snapshot
- keep rollback registration procedure
- verify old service can be restored if needed

#### Deliverables
- rollback note
- rollback command list

---

## B5.4 Exact change strategy by file

### `services/rag_service/rag_service.py`
#### Proposed change
Refactor into explicit API compatibility surface.

#### Responsibilities after change
- parse legacy request bodies
- call RAG-V2 backend/adapter
- map backend response to:
  - `/context` -> `{ "context": string }`
  - `/search` -> `{ "results": [...] }`
- expose `health` and `stats`

### `services/rag_service/rag_engine.py`
#### Proposed change
Do not let this file remain ambiguously “current” if it is actually legacy.

#### Options
- rename/classify as legacy implementation
- or refactor it into shared compatibility layer only if still useful

### `automation/register_rag_service.ps1`
#### Proposed change
- keep service name stable if possible
- point to the new wrapper entrypoint if path changes
- update comments/messages so operators know 8075 = `RAG-V2 8075`

### `automation/nightly-memory-and-rag.ps1`
#### Proposed change
- make the ingest target explicit
- ensure nightly job feeds the same store used by live 8075
- remove hidden dependency on old engine path if no longer correct

### `ttai_hybrid_v2.py` and `ttai_hybrid_v2_fixed.py`
#### Proposed change
- no code change by default
- only patch if latency or timeout handling requires it after real test

---

## B5.5 Rollout strategy

### Stage 1 — Dry preparation
- implement adapter/wrapper
- do not replace live service yet
- prepare config and service notes

### Stage 2 — Parallel verification if possible
- run new implementation against test queries
- compare `/search` and `/context` outputs against current live 8075 behavior

### Stage 3 — Controlled cutover
- re-register or restart service to new runtime
- run smoke tests immediately

### Stage 4 — Observation window
- monitor logs
- test hybrid callers
- validate nightly ingest after next run or manual trigger

### Stage 5 — Documentation update
- rename docs/runbooks only after runtime is stable

---

## B5.6 Minimum acceptance criteria
Cutover should not be considered successful unless:
- `GET /health` works
- `GET /stats` works
- `POST /search` returns legacy-compatible result shape
- `POST /context` returns legacy-compatible context shape
- hybrid callers still behave acceptably
- live store continuity is confirmed
- rollback remains possible

---

## B5.7 Suggested next execution order
1. Implement compatibility wrapper design
2. Decide same-store vs new-store strategy
3. Align nightly ingest
4. Update service registration path
5. Run dry validation
6. Perform controlled cutover
7. Update docs

---

## Bottom line
The correct implementation path is not “replace old RAG with V2 somehow.”
It is:
**turn 8075 into a stable public compatibility surface, then swap the retrieval internals underneath it deliberately.**
