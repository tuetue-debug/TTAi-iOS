# RAG-V2 8075 B13 Promotion Plan — 2026-04-10

## Executive summary
Use the working 8076 proof service as the **golden path** and promote that implementation into the canonical runtime for public port `8075`.

Do not continue treating the current 8075 live runtime as the clean reference, because it has shown anomalous behavior that does not faithfully reflect source changes.

---

## What B12 proved
The parallel proof service on `8076` successfully demonstrated:
- current source code is valid
- compatibility surface works
- `rag_v2` backend switching works
- build marker and runtime observability work
- active backend can be proven (`RAGV2ShadowBackend`)
- no backend boot error is present

This makes `8076` the trustworthy runtime reference.

---

## B13 policy decision
### Canonical migration policy
- `8076 proof service` = trusted reference implementation
- `8075 current service` = anomalous legacy live path
- future work should promote the proven 8076 implementation into the 8075 role

---

## Recommended migration strategy

## Strategy A — Rebuild 8075 from the 8076 golden path (recommended)
### Idea
Treat the proof runner / proof runtime behavior as the canonical startup flow, then re-register or relaunch `8075` using that same proven path.

### Why this is best
- avoids continuing to patch an anomalous live runtime blindly
- uses the already-proven runtime path
- reduces uncertainty about what code is actually active
- makes backend switching proof-able from day one

---

## Concrete promotion steps

### Phase 1 — Freeze proof implementation
- keep `run_proof_service.py` as the known-good startup pattern
- keep proof outputs saved as evidence
- keep `rag_v2` proof env visible

### Phase 2 — Create canonical runner for 8075
Create a dedicated canonical runner for 8075, for example:
- `services/rag_service/run_canonical_service.py`

This runner should:
- set `TTAI_RAG_SERVICE_MODE=compatibility-surface`
- set `TTAI_RAG_BACKEND=rag_v2`
- set `TTAI_RAG_PORT=8075`
- import the same proven app path as 8076
- start uvicorn explicitly

### Phase 3 — Register 8075 to canonical runner
Update service registration so `TTAiRagService` launches the canonical runner instead of relying on a more ambiguous startup path.

### Phase 4 — Verify with proof endpoints on 8075
Before declaring success, verify on 8075:
- `/build-proof`
- `/compatibility`
- `/health`
- `/search`
- `/context`

### Phase 5 — Keep rollback available
If canonical runner promotion fails:
- revert service entry to legacy startup path or legacy backend config
- keep proof service 8076 alive as a working reference

---

## Acceptance criteria for promoted 8075
Promoted 8075 is only considered successful if all are true:
- `/build-proof` exists on 8075
- `/compatibility` reports `backend = rag_v2`
- `/compatibility` reports `backend_active = RAGV2ShadowBackend`
- build marker matches expected source revision
- `/health` remains good
- `/search` and `/context` preserve public contract shape

---

## Why this is better than continuing to patch the current 8075 runtime
Because the current 8075 runtime has already proven that:
- command line can look correct while behavior is still misleading
- source edits may not be reflected as expected
- backend switching is harder to trust there

The 8076 proof service removes that ambiguity.

---

## Broader design lesson
The canonical runtime for a critical port should be launched by an explicit, observable runner — not by a path whose behavior becomes difficult to trust under service lifecycle edge cases.

---

## Immediate next step after B13
Implement:
- `services/rag_service/run_canonical_service.py`

Then prepare a controlled service-registration change so `TTAiRagService` uses the canonical runner for public `8075`.
