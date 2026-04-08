# API.TUETUE.VN Contract Audit — 2026-04-08

## Objective
Audit the current FastAPI backend for `api.tuetue.vn` and classify each exposed surface so implementation can continue in a disciplined order.

Classification legend:
- **REAL** = backed by real logic/data flow and suitable to continue building on
- **PARTIAL** = real code exists, but behavior/data/storage is not yet strong enough to call operational-ready
- **MOCK** = hardcoded/demo/placeholder behavior
- **MOVE** = endpoint may be useful, but belongs under a different surface/boundary or should be internal-only
- **HIDE** = should not be presented as available product capability right now

---

## Executive summary
Current `api.tuetue.vn` backend is **not empty**. It already has meaningful implementation in:
- auth foundation
- chat orchestration
- usage metering
- quota logic
- billing summary logic
- admin/control support endpoints

However, the API contract is still **structurally mixed** across four kinds of surfaces:
1. product API
2. account/auth API
3. admin/control API
4. test/legacy/helper endpoints

That mixing is the main reason progress feels slower than it should.

---

## A. Auth / identity surface

### `/api/v1/auth/register`
- **Status:** REAL
- **Why:** Creates users through SQLite-backed repository and returns JWT token response.
- **Next action:** keep; later move internals to service/repository split.

### `/api/v1/auth/login`
- **Status:** REAL
- **Why:** Authenticates against persistent user repository and returns JWT.
- **Next action:** keep; add refresh-token strategy later.

### `/api/v1/auth/me`
- **GET Status:** REAL
- **PUT Status:** REAL
- **Why:** Reads and updates persisted user profile via repository.
- **Next action:** keep; likely duplicate into future `/api/v1/account/profile` surface.

### `/api/v1/auth/change-password`
- **Status:** REAL
- **Why:** Verifies current password and updates password hash in repository.
- **Next action:** keep; strengthen password policy and audit logging later.

### `/api/v1/auth/logout`
- **Status:** PARTIAL
- **Why:** Exists, but only returns success message; no token revocation, no refresh-token invalidation.
- **Next action:** keep route, replace behavior with real session/token invalidation strategy.

### `/api/v1/auth/api-keys`
- **Status:** MOCK
- **Why:** Returns fabricated key list from hardcoded values.
- **Next action:** remove from product-readiness claims; replace with real account/api-key implementation.

### `/api/v1/auth/usage/stats`
- **Status:** MOCK
- **Why:** Returns hardcoded usage numbers.
- **Next action:** replace with real self-usage view backed by usage ledger.

### `/api/v1/auth/billing/summary`
- **Status:** MOCK
- **Why:** Returns hardcoded billing summary.
- **Next action:** replace with real self-billing summary backed by usage + billing config.

---

## B. Product chat / orchestration surface

### `/api/v1/chat`
- **Status:** PARTIAL
- **Why:** Real orchestration exists: classification, provider selection, model warm-up, fallback behavior, usage logging, quota check, billing estimation.
- **Gaps:** response/error contract still needs hardening; provider fallbacks partly placeholder for non-Ollama branches.
- **Next action:** keep as core product endpoint; formalize contract + error model.

### `/api/v1/hybrid/chat`
- **Status:** MOVE
- **Why:** Pure backward-compat alias to chat flow.
- **Next action:** keep temporarily for compatibility, but not as primary future contract.

### `/api/v1/classify`
- **Status:** REAL
- **Why:** Backed by real classification logic.
- **Next action:** keep, but likely internal/system-oriented rather than end-user product surface.

### `/api/v1/classify/batch`
- **Status:** REAL
- **Why:** Real batch classification helper.
- **Next action:** likely internal/tooling endpoint; do not present as core product capability unless explicitly needed.

---

## C. System / provider / model runtime surface

### `/api/v1/system/health`
- **Status:** REAL
- **Why:** Health endpoint with actual checks.
- **Next action:** keep.

### `/api/v1/system/health/detailed`
- **Status:** REAL
- **Why:** Detailed runtime/system health inspection exists.
- **Next action:** keep; verify sensitivity of exposed details later.

### `/api/v1/system/loadbalancer/metrics`
- **Status:** REAL
- **Why:** Backed by actual load balancer metrics.
- **Next action:** keep; admin/system-facing.

### `/api/v1/system/loadbalancer/providers`
- **Status:** REAL
- **Why:** Returns actual provider list/config state.
- **Next action:** keep; admin/system-facing.

### `/api/v1/system/loadbalancer/providers/{provider_name}/disable`
### `/api/v1/system/loadbalancer/providers/{provider_name}/enable`
- **Status:** REAL
- **Why:** Calls real enable/disable logic with admin protection.
- **Next action:** keep; clearly admin/system only.

### `/api/v1/models/status`
### `/api/v1/models/status/{model_name}`
- **Status:** REAL
- **Why:** Real model manager state.
- **Next action:** keep.

### `/api/v1/models/warmup/{model_name}`
### `/api/v1/models/warmup/all`
- **Status:** REAL
- **Why:** Real warm-up actions with admin protection.
- **Next action:** keep; admin/system only.

### `/api/v1/ollama/models`
### `/api/v1/ollama/health`
### `/api/v1/ollama/generate`
### `/api/v1/ollama/chat`
- **Status:** REAL
- **Why:** Backed by actual Ollama service integration.
- **Next action:** keep, but classify as infrastructure/runtime surface, not primary product account surface.

---

## D. Admin usage / quota / billing surface

### `/api/v1/admin/usage/events`
### `/api/v1/admin/usage/summary`
### `/api/v1/admin/usage/users/{target_user_id}`
- **Status:** PARTIAL
- **Why:** Real read access over usage ledger exists, but ledger is still file-based JSONL and not yet production-grade aggregated storage.
- **Next action:** keep; acceptable for current admin phase.

### `/api/v1/admin/usage/billing-summary`
- **Status:** PARTIAL
- **Why:** Real billing summarization exists, but based on JSONL ledger + static config rules.
- **Next action:** keep; later migrate storage model.

### `/api/v1/admin/quota/status`
### `/api/v1/admin/quota/status/users/{target_user_id}`
### `/api/v1/admin/quota/blocked`
- **Status:** PARTIAL
- **Why:** Real quota logic exists, but operational storage/policy system is still lightweight and file/config driven.
- **Next action:** keep.

### `/api/v1/admin/overview`
### `/api/v1/admin/errors/summary`
- **Status:** PARTIAL
- **Why:** Real summaries exist, but derive from lightweight ledger/log aggregation rather than mature observability storage.
- **Next action:** keep for admin MVP.

### `/api/v1/admin/billing/config` (GET/PUT)
- **Status:** PARTIAL
- **Why:** Real config load/update exists, but config remains JSON-file based.
- **Next action:** keep for admin/internal usage; do not oversell as final billing control-plane maturity.

### `/api/v1/admin/control-dashboard`
### `/api/v1/admin/control-dashboard/health-summary`
### `/api/v1/admin/control-dashboard/providers`
- **Status:** MOVE
- **Why:** Useful, but semantically these are support endpoints for `control.tuetue.vn`, not first-class product API surfaces.
- **Next action:** keep temporarily; treat as control-surface support, not public product contract.

---

## E. Control-only helper surface

### `/control-api/overview`
### `/control-api/quota`
### `/control-api/billing`
### `/control-api/errors`
### `/control-api/models`
### `/control-api/system`
### `/control-api/topology`
### `/control-api/usage`
### `/control-api/session`
### `/control-api/actions`
### `/control-api/actions/run`
- **Status:** MOVE
- **Why:** These are explicitly control-dashboard helper endpoints.
- **Next action:** keep, but treat as internal/control surface. They should not define the long-term public contract of `api.tuetue.vn`.

---

## F. Legacy / placeholder / non-contract endpoints

### `/api/v1/users`
- **Status:** HIDE
- **Why:** explicit placeholder endpoints returning empty or placeholder content.
- **Next action:** remove from readiness claims; either implement properly later or delete.

### `/api/users`
- **Status:** HIDE
- **Why:** old alias + placeholder.
- **Next action:** same as above.

### `/api/chat`
- **Status:** MOVE
- **Why:** legacy alias to `/api/v1/chat`.
- **Next action:** keep only temporarily for compatibility.

### `/api/admin/*` aliases
- **Status:** MOVE
- **Why:** compatibility aliases for `/api/v1/admin/*`.
- **Next action:** retain short-term only if callers depend on them.

### `/api/loadbalancer/*`, `/api/models/*`, `/api/ollama/*`, `/api/hybrid/chat`
- **Status:** MOVE
- **Why:** legacy aliases for versioned endpoints.
- **Next action:** do not use as primary documented contract.

### `/api/test/classification`
### `/api/test/loadbalancer`
- **Status:** HIDE
- **Why:** test/debug-only surfaces.
- **Next action:** keep internal or disable outside dev.

### `/control-login`, `/control-auth/login`, `/control-auth/logout`, `/control-auth/session`
- **Status:** MOVE
- **Why:** valid control authentication helpers, but belong strictly to control/admin surface.
- **Next action:** keep as control-specific, not product API.

---

## Recommended contract grouping going forward

### 1. Product/account-facing contract to keep building
- `/api/v1/auth/*` (identity/session only)
- `/api/v1/account/*` (to be created next)
- `/api/v1/chat`

### 2. Admin/runtime contract to keep but treat separately
- `/api/v1/admin/*`
- `/api/v1/system/*`
- `/api/v1/models/*`
- `/api/v1/ollama/*`

### 3. Internal/control support contract
- `/control-api/*`
- `/control-auth/*`

### 4. Compatibility / cleanup candidates
- `/api/*` unversioned aliases
- `/api/test/*`
- placeholder `/api/v1/users`

---

## Immediate implementation implications

### What is honest to claim right now
- auth persistence foundation exists
- chat orchestration exists
- admin usage/quota/billing summaries exist in lightweight form
- model/provider control surfaces exist

### What is not honest to claim right now
- user-facing API key management is ready
- user-facing usage stats are ready
- user-facing billing summary is ready
- auth/session lifecycle is fully operational-ready
- public API contract is cleanly separated by surface

---

## Part 1 completion criteria
Part 1 is complete when:
1. endpoint contract is classified
2. fake-readiness areas are identified
3. next build surface is narrowed to account/product truth layer

Status: **COMPLETE**

## Recommended next step (Part 2)
Start building the missing **account truth layer**:
1. design `/api/v1/account/*` surface
2. move mock API keys/usage/billing out of `/auth/*`
3. implement real data-backed versions in a disciplined order
