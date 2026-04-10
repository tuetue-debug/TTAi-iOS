# RAG-V2 8075 Canonical Runner Cutover Checklist — 2026-04-10

## Goal
Promote the proven proof-service startup pattern into the official public 8075 runtime.

---

## Pre-cutover
- [ ] proof service 8076 verified with build marker
- [ ] proof service 8076 verified with `backend = rag_v2`
- [ ] proof service 8076 verified with `backend_active = RAGV2ShadowBackend`
- [ ] proof service 8076 verified with healthy public contract endpoints
- [ ] canonical runner file exists: `services/rag_service/run_canonical_service.py`

---

## Service registration change
- [ ] update `TTAiRagService` entrypoint to canonical runner
- [ ] keep Python executable unchanged if possible
- [ ] keep service name stable if possible
- [ ] keep logs available

---

## Post-cutover proof on 8075
- [ ] `GET /build-proof`
- [ ] `GET /compatibility`
- [ ] `GET /health`
- [ ] `POST /search`
- [ ] `POST /context`

---

## Expected proof signals on 8075
- [ ] build marker visible
- [ ] backend reported as `rag_v2`
- [ ] active backend reported as `RAGV2ShadowBackend`
- [ ] no backend boot error

---

## Rollback
- [ ] keep previous service registration details captured
- [ ] be ready to re-point service to prior entrypoint
- [ ] keep 8076 proof service available as working reference during migration
