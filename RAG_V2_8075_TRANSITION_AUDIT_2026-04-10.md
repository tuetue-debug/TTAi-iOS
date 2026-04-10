# RAG-V2 8075 Transition Audit — 2026-04-10

## Key answer first
**No — other connections will NOT safely "just switch by themselves" unless the service contract behind port 8075 stays compatible.**

If port `8075` is repointed to `RAG-V2 8075` without checking callers, likely failure modes include:
- callers expecting old `/search` response shape
- callers expecting `/context` to behave the same way
- automation scripts registering or launching the old service path
- app code (`ttai_hybrid_v2*.py`) assuming old endpoint semantics
- docs/runbooks becoming misleading and causing operator mistakes

Therefore the transition must be done as a **contract-preserving migration**, not just a port rename.

---

## What was found in the workspace

### Runtime/code callers that reference 8075 directly
These are the most important migration-sensitive files:
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`
- `automation/register_rag_service.ps1`
- `automation/nightly-memory-and-rag.ps1`
- `services/rag_service/rag_service.py`
- `services/rag_service/rag_engine.py`

### Documentation / mapping files that still describe old 8075 identity
These should be updated after runtime direction is finalized:
- `MEMORY_RAG_GEMMA_UPGRADE_PLAN_2026-04-07.md`
- `MEMORY_REINDEX_AND_GEMMA_FLOW_2026-04-07.md`
- `MEMORY_SYSTEM_AUDIT_2026-04-07.md`
- `TTAi_HYBRID_RUNTIME_TRACE_MAP.md`
- `TTAi_SYSTEM_MAP_AND_CHEATSHEET.md`
- `TTAi_SUPER_MODEL_PROJECT_REVIEW_2026-04-05.md`

---

## Critical migration rule
Port `8075` can only become `RAG-V2 8075` safely if one of these is true:

### Option A — Contract preserved (preferred)
`RAG-V2 8075` exposes the same endpoints and compatible response formats as the current callers expect.

### Option B — Callers updated explicitly
Every caller that uses `8075` is updated to the new request/response contract.

**Recommendation:** use Option A first if possible. It minimizes breakage.

---

## Contracts that must be checked before cutover

### 1. `/search`
Need to confirm:
- request body shape
- required fields
- response schema
- ranking/evidence fields used by callers

### 2. `/context`
Need to confirm:
- request format
- expected context payload shape
- timeout/error behavior

### 3. Service start / registration behavior
Need to confirm:
- what `automation/register_rag_service.ps1` registers
- what script path the Windows service uses
- where logs are written
- whether any NSSM/service wrapper assumes old filenames

### 4. Downstream app assumptions
Need to confirm:
- whether `ttai_hybrid_v2.py` and `ttai_hybrid_v2_fixed.py` require old field names or ordering
- whether fallback logic assumes legacy behavior

---

## Safe transition sequence

### Step 1 — Freeze legacy service identity
- Snapshot legacy config, startup path, and index/data location.
- Label it internally as `legacy RAG archive`.
- Do not destroy it.

### Step 2 — Inspect current 8075 contract
- Capture real sample requests/responses for `/search` and `/context`.
- Document exact caller expectations.

### Step 3 — Build/verify `RAG-V2 8075` compatibility layer
- Make sure the new service can answer the same endpoint paths.
- If needed, add an adapter layer so callers do not break.

### Step 4 — Update launch scripts / registration
- Point service registration to the `RAG-V2 8075` runtime.
- Keep log paths and restart behavior explicit.

### Step 5 — Smoke test before declaring cutover
Minimum tests:
- `8075/search` returns valid result shape
- `8075/context` returns valid result shape
- `ttai_hybrid_v2.py` still works
- `ttai_hybrid_v2_fixed.py` still works
- no unexpected timeout/fallback regressions

### Step 6 — Only then update docs broadly
- Update trace maps, system maps, and runbooks after cutover is confirmed.

---

## What should NOT happen
- Do not just change the port label in docs and assume runtime is fine.
- Do not kill legacy RAG before a compatibility check exists.
- Do not migrate callers blindly without checking response contract.
- Do not mix the archive role and live shadow role on the same unclear naming.

---

## Recommended next concrete actions
1. Read the current runtime code for:
   - `services/rag_service/rag_service.py`
   - `ttai_hybrid_v2.py`
   - `ttai_hybrid_v2_fixed.py`
   - `automation/register_rag_service.ps1`
2. Document the actual 8075 contract.
3. Decide whether `RAG-V2 8075` will preserve that contract or require caller edits.
4. Only then prepare the real cutover plan.

---

## Bottom line
Port cutover is **not automatic**. It is safe only if contract compatibility is preserved or every dependent caller is updated deliberately.
