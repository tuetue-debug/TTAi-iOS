# TTAi API Access Policy v1

_Last updated: 2026-04-05_

## Goal
Define the first practical access boundary for TTAi API Model so `chat.tuetue.vn`, `control.tuetue.vn`, and backend/operator actions can evolve safely without breaking the current live system.

## Current auth reality
Current admin auth is still a stub in `repos/TTAi-deployment/fastapi/auth.py`:
- uses `HTTPBearer`
- currently accepts any non-empty bearer token
- enough for boundary wiring
- not enough for real production security

So v1 is a **boundary cleanup phase**, not final security.

---

## 1. Access classes

### A. Public / Product
Used by end users and product-facing clients.

Characteristics:
- no admin bearer token required
- intended for `chat.tuetue.vn`
- may later require end-user auth/session auth depending on product flow

Examples:
- `POST /api/v1/chat`
- `POST /api/v1/classify`
- `POST /api/v1/classify/batch`
- `POST /api/v1/hybrid/chat`
- `GET /api/v1/system/health`
- `GET /api/v1/system/health/detailed` (for now still public/read-only)

---

### B. Admin / Control
Used by `control.tuetue.vn` and admin/operator dashboards.

Characteristics:
- bearer token required
- intended for admin visibility and admin config operations
- should later move to real JWT/session/RBAC

Protected in v1:
- `GET /api/v1/admin/control-dashboard`
- `GET /api/v1/admin/control-dashboard/health-summary`
- `GET /api/v1/admin/control-dashboard/providers`
- `GET /api/v1/admin/usage/events`
- `GET /api/v1/admin/usage/summary`
- `GET /api/v1/admin/quota/status`
- `GET /api/v1/admin/quota/status/users/{target_user_id}`
- `GET /api/v1/admin/usage/billing-summary`
- `GET /api/v1/admin/billing/config`
- `PUT /api/v1/admin/billing/config`

---

### C. Operator / Internal Write Actions
Used for runtime mutation or operational control.

Characteristics:
- bearer token required
- write/control operations that should not be public
- intended for internal ops/admin use only

Protected in v1:
- `POST /api/v1/system/loadbalancer/providers/{provider_name}/disable`
- `POST /api/v1/system/loadbalancer/providers/{provider_name}/enable`
- `POST /api/v1/models/warmup/{model_name}`
- `POST /api/v1/models/warmup/all`

---

### D. Internal / Debug / Transitional
Used for debugging, testing, or transition support.

Current state:
- some routes remain publicly reachable for compatibility or diagnostics
- should be tightened in later phases

Examples:
- `/api/v1/test/*`
- some legacy `/api/...` write routes still mirror canonical handlers

---

## 2. v1 implementation rule

### Canonical enforcement focus
Boundary cleanup should prioritize `/api/v1/...` routes first.

Why:
- route standardization is already in progress
- `control.tuetue.vn` should target canonical routes
- future deprecation of legacy routes becomes easier

### Backward compatibility rule
Legacy routes remain active during migration.
That means security is improved structurally, but not fully hardened until:
1. clients move to canonical routes
2. auth becomes real production auth
3. legacy routes are reviewed/deprecated

---

## 3. Recommended next security phases

### Phase 2
- replace stub bearer auth with real admin token validation
- centralize admin auth helper
- add separate auth paths for:
  - end-user auth
  - admin auth
  - API key auth

### Phase 3
- add RBAC roles such as:
  - owner
  - admin
  - ops
  - support
  - billing-admin

### Phase 4
- split admin read vs admin write scopes
- move system/operator actions behind stricter scope checks
- lock test/debug endpoints to internal-only use

---

## 4. Practical guidance for surfaces

### `chat.tuetue.vn`
Should use:
- public/product routes
- later user-authenticated routes
- should not call admin/control APIs directly

### `control.tuetue.vn`
Should use:
- `/api/v1/admin/*`
- selected `/api/v1/system/*`
- selected `/api/v1/models/*`
- always through authenticated admin sessions/tokens

### `api.tuetue.vn`
Remains the enforcement point for:
- data access
- billing/quota rules
- admin visibility
- runtime mutation/control actions

---

## 5. Final policy statement

For TTAi API Model v1:
- keep product, admin, and backend surfaces separate
- protect canonical admin/control routes first
- protect runtime mutation actions first
- preserve compatibility while migrating clients
- treat current bearer auth as temporary boundary wiring, not final production security
