# TTAi USAGE METERING IMPLEMENTATION PLAN

## 1. Purpose

This document defines how TTAi should implement usage metering in practice.

It is the bridge between:
- product/business requirements
- billing data model
- real FastAPI / routing / model execution behavior

This is the first critical implementation layer for:
- API provisioning
- quota enforcement
- billing
- support visibility
- profitability analysis

Without reliable usage metering, every later billing/payment feature is unsafe.

---

## 2. Main Goal

Every request that matters should become a structured, traceable usage event.

That means TTAi must be able to answer questions like:
- Which tenant or user made this request?
- Was it portal chat or API usage?
- Which model/provider handled it?
- How many tokens were used?
- How long did it take?
- Did it succeed, fail, or fallback?
- What did it cost internally?
- Should it count toward quota or billing?

---

## 3. Scope of Metering

Usage metering must eventually cover 3 request classes:

## 3.1 Portal chat traffic
Examples:
- WordPress chat widget
- portal chat UI
- free user sessions
- registered user chat

## 3.2 Direct API traffic
Examples:
- tenant API key usage
- server-to-server API calls
- customer applications consuming TTAi APIs

## 3.3 Internal/admin/testing traffic
Examples:
- admin test prompts
- internal diagnostics
- support reproductions
- synthetic tests

These should be measured but clearly tagged so they are not accidentally billed as customer usage.

---

## 4. Core Metering Principles

1. **One request = one usage event**
   - Every request that reaches the model execution layer should generate a canonical event.

2. **Meter after routing decision and before final response write-back**
   - So the event contains real provider/model/routing outcome.

3. **Track both technical and business dimensions**
   - latency, provider, status, tokens, estimated cost, tenant, channel, quota impact.

4. **Meter failed/fallback requests too**
   - They matter for support, abuse analysis, and provider cost.

5. **Use trace IDs everywhere**
   - So logs, request records, and admin debugging can be linked.

---

## 5. What Must Be Captured Per Event

Minimum event fields (aligns with the billing data model):
- event_id
- request_id / trace_id
- timestamp
- channel (`portal_chat`, `wordpress_chat`, `api`, `admin_test`, `internal`)
- tenant_id (nullable)
- user_id (nullable)
- api_key_id (nullable)
- session_id (nullable)
- provider
- model
- routing_path
- input_tokens
- output_tokens
- total_tokens
- latency_ms
- status (`success`, `error`, `timeout`, `fallback`, `rejected`)
- http_status (if API-facing)
- estimated_cost
- quota_billable (bool)
- billing_billable (bool)
- source_ip / client_id if appropriate
- metadata_json (fallback reason, classifier decision, etc.)

---

## 6. Proposed Metering Pipeline

## Step 1 — Request enters API boundary
At the API boundary, assign:
- `request_id`
- `received_at`
- initial request channel
- actor context (anonymous/free, user, api_key, tenant)

## Step 2 — Authenticate / identify actor
Determine:
- anonymous/free user
- logged-in portal user
- API customer via API key
- admin/internal traffic

## Step 3 — Routing/classification decision
Capture:
- selected provider
- selected model
- routing path
- classifier output (if available)
- fallback intention state

## Step 4 — Model execution
Capture:
- execution start time
- execution finish time
- latency
- status
- output size
- fallback used or not

## Step 5 — Token/cost estimation
Compute:
- input token estimate
- output token estimate
- total token estimate
- estimated internal cost
- whether it is quota-billable and/or billing-billable

## Step 6 — Write usage event
Persist canonical event to the usage ledger.

## Step 7 — Aggregate asynchronously
Roll up into:
- daily usage
- monthly usage
- tenant summaries
- api_key summaries

---

## 7. Where to Instrument in the Current Architecture

This must be implemented as close as possible to the real request execution path.

## 7.1 FastAPI request boundary
Best place to attach:
- middleware or dependency layer
- request-scoped context
- request ID generation

Responsibilities here:
- identify actor/channel
- attach trace/request metadata

## 7.2 Hybrid routing/core execution layer
Best place to attach:
- the component that knows the actual chosen provider/model/fallback path

Responsibilities here:
- record routing decision
- record provider/model used
- record fallback behavior
- capture execution latency

## 7.3 Response finalization layer
Best place to attach:
- just before returning final response to caller

Responsibilities here:
- estimate output tokens
- finalize event payload
- write usage event

---

## 8. Metering for Different Channels

## 8.1 Free / anonymous portal chat
Recommended approach:
- use pseudo identity with `channel=wordpress_chat` or `portal_chat`
- `tenant_id = null`
- `billing_billable = false`
- `quota_billable = true` if enforcing free-tier usage caps

## 8.2 Registered chat user
Recommended approach:
- attach `user_id`
- optional `tenant_id` if user belongs to personal tenant
- `billing_billable` depends on plan
- `quota_billable = true`

## 8.3 API customer request
Recommended approach:
- identify `api_key_id`
- resolve `tenant_id`
- `billing_billable = true`
- `quota_billable = true`

## 8.4 Admin/internal traffic
Recommended approach:
- attach `user_id` if known
- `channel=admin_test` or `internal`
- `billing_billable = false`
- optionally `quota_billable = false`

---

## 9. Token Estimation Strategy

## 9.1 Initial implementation approach
Start with estimated tokens if exact provider accounting is not consistently available.

Recommended initial methods:
- use model tokenizer where feasible
- otherwise use conservative approximation
- store whether token count is `estimated` vs `exact`

Suggested metadata additions:
- `token_count_mode` = `exact` or `estimated`
- `estimation_method` = tokenizer_name / heuristic_name

## 9.2 Why this matters
Token estimation quality directly affects:
- quota fairness
- billing fairness
- provider cost analysis
- profitability reporting

---

## 10. Cost Estimation Strategy

Each event should also store estimated internal cost.

Possible formula inputs:
- provider
- model
- request type
- token counts
- static cost table
- local inference cost approximation (optional, later)

Initial recommendation:
- start with provider/model pricing table
- use exact API provider cost where known
- use configured estimated cost for local/remote Ollama paths

Store both:
- `estimated_cost`
- `currency`

Later, support:
- actual cost reconciliation
- margin analysis by tenant/plan

---

## 11. Quota Logic Requirements

Metering must support quota decisions, even before billing goes live.

Minimum quota dimensions:
- requests per minute
- requests per day
- monthly token limit
- concurrent request cap
- model tier access

Quota enforcement should read from:
- plan features
- API key scopes
- tenant overrides

---

## 12. Status Semantics

Usage events should normalize runtime outcomes into clear statuses:
- `success`
- `error`
- `timeout`
- `fallback`
- `rejected`

Suggested interpretation:
- `success` → completed normally
- `fallback` → completed but only after reroute/provider switch
- `timeout` → no usable completion in time
- `error` → execution error or provider failure
- `rejected` → denied before execution due to auth/quota/policy

This distinction is important for admin support and SLA analysis.

---

## 13. Aggregation Jobs

After usage events are written, aggregation should produce:

## 13.1 Daily aggregates
Group by:
- tenant
- user (optional)
- api key (optional)
- provider/model
- channel

Outputs:
- request_count
- tokens
- estimated_cost
- success/error counts
- fallback counts

## 13.2 Monthly aggregates
Group by:
- tenant
- subscription/billing cycle

Outputs:
- billable usage
- quota consumption
- estimated revenue basis
- estimated provider cost basis

---

## 14. Admin Read APIs Needed First

Before customer-facing billing UI, the first APIs that should exist are internal/admin-only usage views.

Recommended first set:
- `GET /api/v1/admin/usage/summary`
- `GET /api/v1/admin/usage/tenants/{tenant_id}`
- `GET /api/v1/admin/usage/api-keys/{api_key_id}`
- `GET /api/v1/admin/usage/events`
- `GET /api/v1/admin/usage/costs`

These APIs should answer:
- who is consuming usage
- what providers/models are used most
- who is near limits
- where failures/timeouts happen
- what internal cost is being incurred

---

## 15. Suggested First Implementation Sequence

## Phase 1A — Instrument event generation
Deliverables:
- request ID middleware
- actor resolution helpers
- usage event writer interface
- logging at model execution boundary

## Phase 1B — Persist usage ledger
Deliverables:
- `usage_events` table
- append-only event writes
- initial indexes

## Phase 1C — Token and cost estimation
Deliverables:
- token estimator abstraction
- provider cost table
- estimated cost attachment

## Phase 1D — Admin visibility
Deliverables:
- internal usage summary endpoints
- simple admin dashboard views or JSON exports

## Phase 1E — Aggregation and quota support
Deliverables:
- `usage_daily`
- `usage_monthly`
- quota checks powered from aggregated or recent raw usage

---

## 16. Required Technical Interfaces

The implementation should define clear internal interfaces such as:

### `UsageContext`
Contains:
- request_id
- actor context
- tenant context
- channel
- auth mode

### `UsageEventDraft`
Built progressively during request execution.

### `UsageEventWriter`
Responsible for persisting completed events.

### `TokenEstimator`
Computes or estimates tokens.

### `CostEstimator`
Computes estimated internal cost.

### `QuotaChecker`
Checks whether usage should be allowed.

These abstractions help avoid scattering metering logic across unrelated files.

---

## 17. Risks to Avoid

- writing usage events only in outer HTTP logs but not at the true model execution layer
- failing to capture fallback/provider-switch behavior
- coupling billing logic too early into request handlers
- relying only on provider logs instead of canonical internal usage events
- charging customers before the ledger is trustworthy
- ignoring anonymous/free usage because it still matters for product analytics and abuse prevention

---

## 18. Documentation and Debug Discipline

To avoid wasted time, metering work must be documented strictly.

Every implementation step should record:
- file changed
- endpoint/hook added
- fields captured
- whether token counts are exact or estimated
- whether event is billing-billable or quota-billable
- test result

Suggested supporting files after implementation begins:
- `TTAi_USAGE_METERING_PROGRESS.md`
- `TTAi_USAGE_EVENT_SCHEMA_EXAMPLES.md`
- `TTAi_QUOTA_ENFORCEMENT_RULES.md`

---

## 19. Implementation Readiness Decision

This workstream is ready to move from planning to implementation once these are agreed:
- canonical request boundary for event creation
- canonical source of provider/model routing result
- token estimation strategy for first release
- database location for usage ledger
- free-tier quota policy
- whether WordPress chat and API traffic share one usage schema

---

## 20. Immediate Next Step

After this document, the next recommended concrete work item is:
- map the current FastAPI request path and identify the exact files/hooks where usage metering should be inserted

Recommended next file:
- `TTAi_USAGE_METERING_CODE_INSERTION_MAP.md`

That file should describe:
- which existing endpoints receive traffic
- where routing/provider selection happens
- where response is finalized
- where the usage event writer should be called
