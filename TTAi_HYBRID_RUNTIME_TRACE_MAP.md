# TTAi HYBRID RUNTIME TRACE MAP

## 1. Purpose

This document maps the current live runtime path of the TTAi hybrid system as far as it can be verified from:
- running ports/processes/services
- live HTTP responses
- current code files
- current collector topology

The goal is to identify the **real execution chain** before inserting usage metering or other business-critical logic.

---

## 2. Runtime Snapshot Verified on 2026-04-05

## 2.1 Listening services
The following ports were verified listening locally:
- `8000`
- `8005`
- `8015`
- `8075`
- `8090`

## 2.2 Live service identity checks

### Port `8000`
`GET /` returned:
- service: `TTAi Super Model Hybrid API`
- version: `2.0.0`
- features include:
  - Load Balancing (60/30/10)
  - Query Classification
  - Model Warm-up
  - Ollama Integration
  - CLI Proxy Fallback

### Port `8005`
`GET /` returned:
- service: `TTAi Hybrid System v2.0 - Fixed`
- version: `2.0.1`
- features include:
  - Local Ollama
  - Remote Ollama
  - DeepSeek API
  - Gemini API
  - Smart Load Balancing
  - Fallback Mechanism

### Port `8015`
`GET /` returned:
- service: `TTAi Load Balancer`
- version: `1.1.0`
- backends:
  - `http://localhost:8005`
  - `http://localhost:8000`
  - `http://100.89.201.7:8000`
- hedge enabled: `true`
- hedge delay: `0.35s`

### Port `8075`
Backed by:
- `services/rag_service/rag_service.py`
- registered Windows service: `TTAiRagService`

### Port `8090`
Backed by:
- `services/control_dashboard/collector_service.py`
- registered Windows service: `TTAiControlDashboard`

---

## 3. Confirmed Services and Code Anchors

## 3.1 RAG service
Confirmed via NSSM:
- service: `TTAiRagService`
- application: Python 3.11
- script: `services\rag_service\rag_service.py`
- port: `8075`

## 3.2 Control Dashboard Collector
Confirmed via NSSM:
- service: `TTAiControlDashboard`
- application: Python 3.11
- script: `services\control_dashboard\collector_service.py`
- port: `8090`

## 3.3 Port `8005`
Current live identity strongly matches:
- `ttai_hybrid_v2_fixed.py`

Why:
- root response says `TTAi Hybrid System v2.0 - Fixed`
- code in `ttai_hybrid_v2_fixed.py` contains:
  - title/identity matching “FIXED VERSION”
  - `@app.get("/")`
  - version `2.0.1`
  - `execute_provider(...)`
  - `call_provider_with_fallback(...)`
  - `chat(...)`

### Working assumption
Port `8005` is currently served by logic corresponding to:
- `ttai_hybrid_v2_fixed.py`

This is the strongest candidate for the true hybrid execution runtime.

## 3.4 Port `8015`
Current live identity strongly matches:
- `load_balancer.py`

Why:
- root response exactly exposes backend list and hedge config
- `load_balancer.py` contains matching root route and backend configuration concepts

### Working assumption
Port `8015` is currently served by logic corresponding to:
- `load_balancer.py`

## 3.5 Port `8000`
Live root response identifies it as:
- `TTAi Super Model Hybrid API`
- version `2.0.0`

Likely candidates include portal/backend or hybrid service variants, but the exact runtime file is **not yet fully proven** from available evidence.

### Working assumption
Port `8000` is a local API path participating in the hybrid/backend chain and is also listed as a load balancer backend.
It should be treated as a live execution path but still needs exact file confirmation.

---

## 4. Current Runtime Topology (Practical View)

## 4.1 High-level flow candidates
There are two likely request entry patterns currently relevant:

### Path A — Through load balancer
Client / portal / WordPress
→ `8015` (`TTAi Load Balancer`)
→ one of:
- `8005` local hybrid fixed runtime
- `8000` local API runtime
- `100.89.201.7:8000` remote API runtime
→ provider/model execution
→ response back through caller path

### Path B — Direct hybrid execution
Client / portal / WordPress
→ `8005` (`TTAi Hybrid System v2.0 - Fixed`)
→ provider selection / fallback logic
→ response back

### Path C — Direct local API runtime
Client / portal / internal caller
→ `8000`
→ local hybrid/super-model path
→ response back

---

## 5. Most Important Runtime Facts for Metering

## 5.1 Port `8015` is a routing layer, not the best final billing anchor
Because:
- it selects among multiple backends
- hedging is enabled
- final provider/model choice may happen deeper in backend/hybrid logic

### Implication
`8015` should carry:
- request trace propagation
- routing telemetry
- backend chosen

But should **not** automatically be treated as the final canonical billing event writer unless it knows the final provider/model outcome.

## 5.2 Port `8005` is the strongest current billing-anchor candidate
Because:
- it appears to contain actual hybrid provider execution logic
- it contains provider execution and fallback functions
- it exposes the “fixed” hybrid runtime identity

### Implication
If this is truly the active path for most model execution, then usage metering must capture runtime truth here.

## 5.3 Port `8000` still matters and must be traced explicitly
Because:
- it is listed as a healthy backend by the load balancer
- it presents itself as a hybrid/super-model API
- remote `100.89.201.7:8000` is also a healthy backend

### Implication
Even if `8005` becomes the main metering anchor, `8000` and remote `8000` must be included in trace mapping because some live requests may bypass `8005`.

---

## 6. File-Level Runtime Map

## 6.1 `ttai_hybrid_v2_fixed.py`
Likely live for `8005`.

Relevant confirmed functions/routes:
- `execute_provider(...)`
- `call_provider_with_fallback(...)`
- `chat(request: ChatRequest)`
- `@app.get("/")`

### Role in runtime
This appears to be the real local hybrid execution engine.

### Metering importance
This is the best known place to capture:
- actual provider selected
- actual model used
- fallback behavior
- execution result
- execution latency

---

## 6.2 `load_balancer.py`
Likely live for `8015`.

Relevant confirmed behavior:
- root route publishes backend list
- hedging is enabled
- backends are `8005`, `8000`, and remote `8000`

### Role in runtime
This is the routing front door.

### Metering importance
This is the right place for:
- request trace propagation
- route-selection log
- backend selected
- hedge/fallback telemetry at load-balancer layer

Not ideal for the final canonical billing event by itself.

---

## 6.3 `TTAi-Portal/backend/app/...`
Still important for portal-facing authenticated traffic.

Likely key files:
- `backend/app/main.py`
- `backend/app/routes/chat.py`
- `backend/app/services/chat_service.py`
- `backend/app/services/model_service.py`

### Role in runtime
These should be treated as the user/account-facing request context layer.

### Metering importance
This is where to capture:
- user identity
- tenant identity (later)
- channel
- conversation/session context
- auth mode

But provider/model truth still likely comes from deeper hybrid runtime.

---

## 7. Probable End-to-End Runtime Flow

## 7.1 WordPress / portal chat flow (current practical hypothesis)
WordPress / portal chat UI
→ local API or load balancer entry (`8000` or `8015`)
→ if routed through `8015`, backend selected among `8005`, `8000`, or remote `8000`
→ if execution reaches `8005`, provider selection/fallback happens inside fixed hybrid runtime
→ provider/model executes
→ response returns upward
→ UI renders response

## 7.2 Direct API / internal test flow
Internal test / admin / script
→ `8005` or `8000` directly
→ hybrid execution
→ provider/model executes
→ response returns

This matches current operational behavior better than the earlier assumption that everything flows through one single clean stack.

---

## 8. Recommended Metering Anchor Strategy

## 8.1 Canonical usage event source
Primary candidate:
- hybrid execution runtime at `8005`
- likely `ttai_hybrid_v2_fixed.py`

Why:
- closest known layer to actual provider/model/fallback truth

## 8.2 Trace propagation source
Primary candidate:
- `load_balancer.py` on `8015`
- plus FastAPI middleware in portal/backend layer

Why:
- request may pass across several layers
- trace continuity matters for debugging and later billing disputes

## 8.3 Portal identity enrichment source
Primary candidate:
- `TTAi-Portal/backend/app/routes/chat.py`
- `TTAi-Portal/backend/app/services/chat_service.py`

Why:
- closest layer to authenticated user / tenant / session information

---

## 9. What Is Still Not Fully Proven

The following still need explicit runtime validation before coding metering into production:

1. Whether WordPress production chat hits `8000`, `8005`, or `8015` by default right now.
2. Whether portal admin/chat backend currently calls hybrid directly or through load balancer.
3. Which exact file/process is serving `8000` in the current runtime.
4. Whether any live traffic bypasses `ttai_hybrid_v2_fixed.py` entirely.

These are important because metering inserted in the wrong execution layer could undercount or double-count events.

---

## 10. Recommended Immediate Verification Tasks

## Task 1
Trace WordPress production chat endpoint configuration:
- identify exact URL configured in active production plugin/container
- confirm whether it points to `8015`, `8005`, or `8000`

## Task 2
Trace portal backend model invocation path:
- confirm whether `chat_service.py` / `model_service.py` call `8005`, `8000`, or another path

## Task 3
Identify exact runtime file for local `8000` process:
- confirm command line or deployment config for PID `12148`

## Task 4
Run one request with a unique trace marker and inspect:
- portal/backend logs
- load balancer logs
- hybrid logs
- provider metrics logs

That would produce a fully validated end-to-end path map.

---

## 11. Recommended Next Coding Decision

Before implementing usage metering for production traffic:

### Do first
- confirm real traffic entry path from WordPress and portal
- confirm active runtime file for `8000`
- confirm whether `8005` is always or only sometimes in the request path

### Then implement
- request ID propagation at all entry points
- actor context capture in portal/backend
- canonical usage event write in the true hybrid execution layer

---

## 12. Final Working Conclusion

As of this runtime trace review, the strongest current operational picture is:

- `8015` = load balancer front door
- `8005` = fixed hybrid runtime and best current canonical execution anchor
- `8000` = additional live API/hybrid runtime path still needing exact code confirmation
- `8075` = RAG service
- `8090` = control dashboard collector

This is enough to guide the next verification step, but not yet enough to safely finalize production metering insertion without one more round of runtime trace confirmation.
