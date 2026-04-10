# RAG Service Final Topology — 2026-04-10

## Canonical live topology
### Public port `8075`
- Role: canonical live RAG compatibility surface
- Managed by: `TTAiRagService`
- Intended runner: `services/rag_service/run_canonical_service.py`
- Current service mode: `compatibility-surface`
- Current backend: `rag_v2`
- Current active backend: `RAGV2ShadowBackend`
- Proof endpoint: `/build-proof`
- Runtime introspection endpoint: `/compatibility`

### Proof/test port `8076`
- Role: temporary proof/reference service used to validate the new runtime path independently of the anomalous old 8075 holder
- Runner: `services/rag_service/run_proof_service.py`
- Service mode: `compatibility-surface-proof`
- Backend: `rag_v2`
- Status after cleanup: should be stopped unless actively needed for future tests

---

## Operational truth rules
1. Never trust service config alone; verify the actual listener PID.
2. For 8075, success means all of these are true:
   - `/build-proof` responds
   - `/compatibility` reports `backend = rag_v2`
   - `/compatibility` reports `backend_active = RAGV2ShadowBackend`
   - no orphan process is holding the port
3. Use 8076 only as a temporary proof/reference path, not as the permanent production surface.
4. After future cutovers, verify:
   - service PID
   - listener PID
   - build marker
   - active backend
   - env-effective values

---

## Historical note
The main anomaly during migration was an orphan Python process (`PID 7696`) that silently owned port `8075` while the managed service appeared healthy. This caused service-level configuration changes to look ineffective until real port ownership was verified and the orphan holder was removed.
