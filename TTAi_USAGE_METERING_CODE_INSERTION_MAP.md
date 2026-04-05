# TTAi USAGE METERING CODE INSERTION MAP

## 1. Purpose

This document maps the current code paths where usage metering should be inserted.

It translates planning into implementation reality by identifying:
- current request entry points
- where routing/provider selection happens
- where response metadata is finalized
- where the canonical usage event writer should be called
- where admin read views can later pull data from

This file should be used before any coding begins on usage metering.

---

## 2. Important Scope Clarification

The workspace contains many historical experiments, temp files, backups, and alternate implementations.

For metering work, the most relevant code paths appear to be:

## 2.1 Primary portal/backend candidate
- `TTAi-Portal/backend/app/main.py`
- `TTAi-Portal/backend/app/routes/chat.py`
- `TTAi-Portal/backend/app/services/chat_service.py`
- `TTAi-Portal/backend/app/services/model_service.py`
- `TTAi-Portal/backend/app/models.py`
- `TTAi-Portal/backend/app/routes/auth.py`
- `TTAi-Portal/backend/app/routes/api_keys.py`
- `TTAi-Portal/backend/app/routes/billing.py`
- `TTAi-Portal/backend/app/routes/control_dashboard.py`

## 2.2 Hybrid core candidate
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`
- `load_balancer.py`
- `simple_proxy.py`

## 2.3 Monitoring/ops layer already present
- `services/control_dashboard/collector_service.py`

This means metering work should **not** start in the collector.
It should start in the actual traffic path.

---

## 3. Current Real Entry Points Identified

## 3.1 Portal chat request entry
File:
- `TTAi-Portal/backend/app/routes/chat.py`

Relevant route:
- `@router.post("/")`

Meaning:
- This appears to be the main authenticated portal chat API route.
- Best candidate for user-context-aware metering on portal chat traffic.

Additional portal chat-related routes exist for:
- conversation history
- regenerate
- continue
- feedback
- search
- stats

These are important later, but metering should begin with the primary chat request path first.

---

## 3.2 Portal auth entry
File:
- `TTAi-Portal/backend/app/routes/auth.py`

Relevant routes:
- `/auth/login`
- `/auth/me`
- `/auth/oauth/{provider}`
- `/auth/oauth/{provider}/callback`

Meaning:
- These routes are important for actor identity resolution.
- Metering should not start here, but these routes define how `user_id` is resolved for later chat/API usage.

---

## 3.3 API key/business placeholder routes
Files:
- `TTAi-Portal/backend/app/routes/api_keys.py`
- `TTAi-Portal/backend/app/routes/billing.py`

Current observation:
- route skeletons exist, but they appear to be placeholders or status routes rather than complete provisioning/billing flows.

Meaning:
- usage metering should be built before these become real customer-facing systems
- but their presence is useful because later admin/customer usage APIs can align with these route groups

---

## 3.4 Hybrid API entry
File:
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`

Relevant route:
- `@app.post("/api/chat")`

Meaning:
- This is the clearest low-level execution path where model/provider routing and fallback are decided.
- This is the most important insertion point for canonical usage event capture if this code path is still the active runtime for hybrid execution.

---

## 3.5 Load balancer entry
File:
- `load_balancer.py`
- `simple_proxy.py`

Relevant routes:
- `@app.post("/api/chat")`
- `@app.get("/health")`

Meaning:
- If traffic enters through the load balancer first, request tracing should begin here.
- However, the canonical metering event should only be finalized after the real backend/provider outcome is known.

---

## 4. Best Insertion Points by Layer

## 4.1 Layer A — Request boundary / trace initialization

### Best candidate file
- `TTAi-Portal/backend/app/main.py`

Why:
- this file already has HTTP middleware hooks (`@app.middleware("http")`)
- ideal place to attach a request ID / trace ID
- ideal place to populate initial usage context shell

### What to insert here
Create middleware that:
- generates `request_id`
- stores `request_start_time`
- stores path/method/channel guess
- attaches request-scoped context for later usage event completion

### Output from this layer
A request-scoped `UsageContext` object or equivalent carrying:
- request_id
- start_time
- channel
- source_ip
- auth mode

---

## 4.2 Layer B — Actor identity resolution

### Best candidate files
- `TTAi-Portal/backend/app/routes/chat.py`
- `TTAi-Portal/backend/app/auth.py`
- later `TTAi-Portal/backend/app/routes/api_keys.py`

Why:
- chat route already uses authenticated current user context
- auth layer resolves `user_id`
- future API key routes will resolve machine credential context

### What to capture here
- `user_id`
- `tenant_id` (when tenant model exists)
- `api_key_id` (for API traffic)
- channel (`portal_chat`, `api`, `admin_test`, etc.)

### Notes
This should enrich the request-scoped usage context rather than write the final usage event immediately.

---

## 4.3 Layer C — Routing/provider selection

### Best candidate files
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`

Key functions identified:
- `execute_provider(...)`
- `call_provider_with_fallback(...)`
- route `chat(request: ChatRequest)`

Why these matter:
- these functions know the chosen provider/model
- they know whether fallback was used
- they know the final runtime outcome

### What to capture here
- provider name
- model used
- routing path
- fallback flag
- execution status
- backend chosen

### Recommended insertion point
Inside or immediately after:
- `call_provider_with_fallback(...)`

This is likely the best place to capture the actual execution path.

---

## 4.4 Layer D — Response finalization / latency / final event write

### Best candidate files
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`
- `TTAi-Portal/backend/app/services/chat_service.py`
- `TTAi-Portal/backend/app/services/model_service.py`

Why:
- these locations already calculate processing time
- response objects already include `model_used` and `processing_time` / `processing_time_ms`
- they are close to the final response payload

### What to finalize here
- latency_ms
- status
- response size / output token estimate
- estimated cost
- final billable/quota flags
- persist canonical usage event

### Strong recommendation
The **final write** to `usage_events` should happen at the point where all of the following are known:
- actor
- provider/model
- routing/fallback result
- latency
- success/error outcome

That likely means:
- either at the end of hybrid `chat()`
- or in the portal `chat_service` after model response is returned

---

## 5. Recommended Canonical Metering Flow in Current Code

## Preferred implementation path

### Step 1
Add request/trace middleware in:
- `TTAi-Portal/backend/app/main.py`

### Step 2
Create a shared usage metering module, for example:
- `TTAi-Portal/backend/app/services/usage_metering.py`

This module should expose:
- `create_usage_context()`
- `attach_actor_context()`
- `attach_routing_result()`
- `finalize_usage_event()`
- `write_usage_event()`

### Step 3
In portal chat route/service:
- enrich usage context with authenticated user information

### Step 4
In hybrid execution path:
- enrich usage context with provider/model/fallback info

### Step 5
At final response boundary:
- compute token/cost estimates
- write canonical usage event

---

## 6. File-by-File Recommended Insertions

## 6.1 `TTAi-Portal/backend/app/main.py`
### Current role
- FastAPI app root
- middleware exists already
- good place for request-wide context

### Add here
- request ID middleware
- usage context bootstrap
- request start timestamp
- request end safety logging for unhandled failures

### Why first
This gives every later layer a consistent trace ID.

---

## 6.2 `TTAi-Portal/backend/app/routes/chat.py`
### Current role
- primary portal chat endpoint
- has access to authenticated current user context

### Add here
- channel assignment (`portal_chat`)
- actor attachment (`user_id`, later `tenant_id`)
- pass usage context to service layer

### Why important
This is the main user-facing entry path for registered portal users.

---

## 6.3 `TTAi-Portal/backend/app/services/chat_service.py`
### Current role
- conversation/message orchestration
- already tracks `processing_time_ms`
- already persists conversation/message entities

### Add here
- finalize portal-facing usage event if this is the layer that receives completed model response
- attach conversation/session identifiers to usage context
- optional secondary event for conversation analytics (not billing ledger)

### Why important
This may be the cleanest place to connect user/chat context with final response metadata.

---

## 6.4 `TTAi-Portal/backend/app/services/model_service.py`
### Current role
- model response handling and timing metadata

### Add here
- if this service is the actual point of provider invocation, capture provider/model outcome here
- return structured routing/model metadata upward rather than only plain response payload

### Why important
This is a likely bridge between portal logic and execution layer.

---

## 6.5 `ttai_hybrid_v2.py`
### Current role
- direct hybrid execution route
- route `POST /api/chat`
- contains provider execution and fallback functions

### Add here
- execution result metadata capture
- routing path capture
- provider/model/fallback state
- optional low-level event payload to be returned upward

### Why important
This is where the truth about provider selection appears to live.

---

## 6.6 `ttai_hybrid_v2_fixed.py`
### Current role
- likely alternate/fixed runtime candidate
- very similar structure to `ttai_hybrid_v2.py`

### Add here if active runtime
- same as above

### Important caution
Before coding, confirm which of:
- `ttai_hybrid_v2.py`
- `ttai_hybrid_v2_fixed.py`
- another service on `8005`

is actually the active runtime path.

---

## 6.7 `load_balancer.py`
### Current role
- front door for backend distribution in some flows
- already has middleware and `/api/chat`

### Add here
- request_id pass-through / propagation
- request-level routing trace log
- backend selected at load balancer level
- do **not** treat this alone as final canonical billing event unless final model/provider outcome is known here

### Why important
Useful for trace continuity and routing debug, but not sufficient by itself for full billing metering.

---

## 6.8 `simple_proxy.py`
### Current role
- alternate/simple load balancer path
- logs into `load_balancer.jsonl`

### Add here only if active
- request trace propagation
- backend chosen
- minimal route telemetry

### Why secondary
This appears more like a simplified routing path, useful but probably not the final business-metering anchor.

---

## 7. Existing Data Fields Already Present and Useful

The following existing fields are already visible in current code and should be reused:
- `user_id`
- `model_used`
- `processing_time`
- `processing_time_ms`
- conversation/message storage
- provider metrics logs
- load balancer logs

This is good news: the project already has the beginnings of a metering vocabulary.

What is missing is a canonical event writer and unified ledger.

---

## 8. Recommended New Shared Module

Create a new backend module, likely under:
- `TTAi-Portal/backend/app/services/usage_metering.py`

Recommended contents:
- `UsageContext`
- `UsageEventDraft`
- `UsageEventWriter`
- `TokenEstimator`
- `CostEstimator`
- `QuotaFlagResolver`

This avoids copying logic into routes and hybrid files directly.

---

## 9. First Implementation Slice (Most Practical)

Do not try to meter everything at once.

### First slice should meter:
- authenticated portal chat requests
- direct portal chat response lifecycle
- model/provider outcome
- latency
- estimated tokens/cost

### First slice should not yet attempt:
- full payment logic
- invoice generation
- self-service billing UI
- complete API key monetization

The first milestone is simply:
**every portal chat request produces a trustworthy usage event**.

---

## 10. Gaps / Unknowns That Must Be Confirmed Before Coding

Before implementation begins, confirm these runtime truths:

1. Which file actually powers the live hybrid runtime on port `8005`?
2. Whether portal chat reaches hybrid directly or via load balancer first.
3. Whether `TTAi-Portal/backend/app/services/model_service.py` is the real invocation layer or just a wrapper.
4. Which backend path should be treated as the canonical billing event source.
5. Whether direct API traffic currently exists in the same FastAPI app or a different gateway path.

Without this confirmation, metering work risks being inserted into the wrong layer.

---

## 11. Recommended Immediate Coding Sequence

## Step 1
Confirm active runtime path for portal chat → hybrid → provider.

## Step 2
Implement request ID middleware in:
- `TTAi-Portal/backend/app/main.py`

## Step 3
Create shared usage metering module.

## Step 4
Instrument `routes/chat.py` + `services/chat_service.py`.

## Step 5
Instrument active hybrid execution file (`ttai_hybrid_v2.py` or actual runtime equivalent).

## Step 6
Persist to `usage_events` and test with real chat requests.

---

## 12. Recommended Next Artifact

After this file, the next most useful artifact is:
- `TTAi_HYBRID_RUNTIME_TRACE_MAP.md`

That file should answer the unresolved runtime questions directly:
- exact request path from WordPress/Portal to provider
- exact files and services involved
- exact component where provider selection happens in real runtime

This would remove the last uncertainty before coding usage metering into the live path.
