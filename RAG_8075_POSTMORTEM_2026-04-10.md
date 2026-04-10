# RAG 8075 Postmortem — 2026-04-10

## What happened
A seemingly simple goal — switching port `8075` from legacy behavior toward `RAG-V2` behind a stable compatibility surface — turned into a much larger debugging exercise.

The core reason was not that the new design was wrong.
The core reason was that the live port was not actually controlled by the service path we believed it was.

---

## Root cause
Port `8075` was being held by an orphan Python process:
- PID: `7696`
- command: `python.exe ...\services\rag_service\rag_service.py`
- parent PID: `11884` (no longer existed)

This meant:
- service configuration changes could appear successful
- NSSM service restarts could appear successful
- but the real live runtime on `8075` could still be an older standalone holder

---

## Why it was confusing
Several signals looked correct in isolation:
- service path looked correct
- service status was `Running`
- command lines looked plausible
- source edits were present on disk

But the live runtime behavior did not match those source edits.
That mismatch produced repeated false leads until real port ownership was checked directly.

---

## What solved it
1. Introduce a stable compatibility-surface design
2. Add build marker and runtime observability fields
3. Build a clean proof service on `8076`
4. Confirm the new design actually worked there
5. Inspect real listener ownership on `8075`
6. Identify orphan PID `7696`
7. Kill the orphan and let the managed canonical runner take the port
8. Re-verify using:
   - `/build-proof`
   - `/compatibility`
   - `/health`

---

## Final success state
`8075` now proves:
- `backend = rag_v2`
- `backend_active = RAGV2ShadowBackend`
- `build_marker = rag-service-build-d68cd55-marker-1`
- no backend boot error

---

## Design lessons
### 1. Stable public surface matters
The compatibility-surface approach was the right direction.
The issue was not the idea; it was runtime ownership ambiguity.

### 2. Proof beats assumption
Never assume a service config change means the live port changed.
Always prove it.

### 3. Port ownership is part of truth
The real source of truth is not just the service definition.
It is:
- which PID owns the live port
- what code build that PID serves
- what backend that PID reports active

### 4. Runtime observability must be built in
Every switchable runtime should expose:
- build proof
- active backend
- raw env inputs
- boot errors
- service mode

---

## Preventive actions
- Keep build-proof and compatibility diagnostics in place
- Use explicit canonical runners for managed services
- Check listener PID after any cutover
- Keep proof/test services for risky migrations
- Write down runtime ownership assumptions as runbooks, not tribal memory

---

## Bottom line
The hard part was not switching to `RAG-V2`.
The hard part was proving who really owned the live runtime.
Once that was made visible, the migration became tractable.
