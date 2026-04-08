# API.TUETUE.VN Part 2 — Account Truth Layer Design (2026-04-08)

## Goal
Define the correct boundary between auth and account, design the new `/api/v1/account/*` contract, and map current mock/legacy endpoints into the new surface so implementation can proceed without ambiguity.

---

# 1. Boundary: Auth vs Account

## 1.1 Auth surface = identity + session + token lifecycle
Auth exists to answer:
- who is this user?
- can they authenticate?
- what token/session do they have?
- can they renew or end that session?

### Auth should own
- register
- login
- logout
- refresh token
- current identity (`/me` or `/session/me` style)
- password change / reset
- email verification
- token/session invalidation
- role claims at identity level

### Auth should NOT own
- profile editing as a long-term business/account domain
- API key inventory
- usage dashboards
- billing summaries
- plan/subscription display
- account settings unrelated to authentication itself

## 1.2 Account surface = user-facing business/account data
Account exists to answer:
- what does this user own?
- what settings/profile/subscription do they have?
- what API keys are active?
- how much usage/cost/quota have they consumed?

### Account should own
- profile
- account settings
- API keys
- usage summary
- usage event history
- billing summary
- quota/plan/limits view
- subscription-facing information

## 1.3 Clean split to adopt now

### Keep under `/api/v1/auth/*`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/change-password`
- future:
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/forgot-password`
  - `POST /api/v1/auth/reset-password`
  - `POST /api/v1/auth/verify-email`

### Move to `/api/v1/account/*`
- profile update/read
- API keys
- usage summary/history
- billing summary
- quota / limits / plan

## 1.4 Practical decision for current codebase
To minimize wasted motion:
- keep `GET /api/v1/auth/me` as the short-term identity endpoint
- introduce `/api/v1/account/*` for all business/account surfaces
- optionally add `/api/v1/account/profile` that internally reuses current user repository/profile logic
- later decide whether `PUT /api/v1/auth/me` is deprecated in favor of `PUT /api/v1/account/profile`

---

# 2. Proposed `/api/v1/account/*` contract

## Design principles
1. No fake data
2. No business/account data under `/auth/*`
3. User-facing account views are distinct from admin views
4. Build only the minimum truthful contract first

---

## 2.1 Profile

### `GET /api/v1/account/profile`
**Purpose**
Return the authenticated user’s account/profile view.

**Auth required**
Yes

**Response (target)**
```json
{
  "id": "123",
  "email": "user@example.com",
  "name": "Test User",
  "role": "user",
  "status": "active",
  "created_at": "2026-04-08T00:00:00Z",
  "updated_at": "2026-04-08T00:00:00Z"
}
```

### `PUT /api/v1/account/profile`
**Purpose**
Update allowed profile/account fields.

**Allowed fields (phase 1)**
- `name`
- `email`

**Request (target)**
```json
{
  "name": "New Name",
  "email": "new@example.com"
}
```

**Response**
Updated profile object

**Implementation note**
Can reuse the same repository logic now used by `PUT /api/v1/auth/me`.

---

## 2.2 API keys

### `GET /api/v1/account/api-keys`
**Purpose**
List the authenticated user’s API keys.

**Auth required**
Yes

**Response (target)**
```json
{
  "items": [
    {
      "id": "key_001",
      "name": "Production Key",
      "key_prefix": "sk-ttai-abcd",
      "scopes": ["chat:write"],
      "created_at": "2026-04-08T00:00:00Z",
      "last_used_at": null,
      "is_active": true
    }
  ],
  "count": 1
}
```

### `POST /api/v1/account/api-keys`
**Purpose**
Create a new API key for the current user.

**Request (target)**
```json
{
  "name": "Production Key",
  "scopes": ["chat:write"]
}
```

**Response (target)**
```json
{
  "id": "key_001",
  "name": "Production Key",
  "key": "sk-ttai-very-long-secret-only-return-once",
  "key_prefix": "sk-ttai-abcd",
  "scopes": ["chat:write"],
  "created_at": "2026-04-08T00:00:00Z",
  "is_active": true
}
```

### `DELETE /api/v1/account/api-keys/{key_id}`
**Purpose**
Revoke/delete an API key.

**Response**
```json
{
  "ok": true,
  "message": "API key revoked"
}
```

### `POST /api/v1/account/api-keys/{key_id}/rotate`
**Purpose**
Rotate an existing key.

**Phase decision**
Can be deferred until after basic create/list/revoke works.

---

## 2.3 Usage

### `GET /api/v1/account/usage/summary`
**Purpose**
Return the authenticated user’s summarized usage view.

**Response (target)**
```json
{
  "period": "30d",
  "summary": {
    "total_requests": 120,
    "success_events": 118,
    "error_events": 2,
    "total_tokens_est": 45000,
    "estimated_cost": 3.42,
    "avg_processing_time": 1.24
  }
}
```

### `GET /api/v1/account/usage/events`
**Purpose**
Return recent usage events for the authenticated user.

**Query params (phase 1)**
- `limit`
- optional `status`

**Response (target)**
```json
{
  "items": [
    {
      "timestamp": "2026-04-08T00:00:00Z",
      "request_path": "/api/v1/chat",
      "provider": "cliproxy-gpt-mini",
      "model": "gpt-mini",
      "status": "success",
      "total_tokens_est": 320,
      "estimated_cost": 0.0001,
      "processing_time": 0.82
    }
  ],
  "count": 1
}
```

### `GET /api/v1/account/usage/breakdown`
**Purpose**
Optional next-step endpoint for grouped usage breakdowns.

**Phase decision**
Can be delayed until summary/events are truthful.

---

## 2.4 Billing / limits

### `GET /api/v1/account/billing/summary`
**Purpose**
Return the user-facing billing summary derived from real usage + billable rules.

**Response (target)**
```json
{
  "summary": {
    "estimated_cost": 3.42,
    "billable_requests": 87,
    "non_billable_requests": 33,
    "currency": "USD"
  }
}
```

### `GET /api/v1/account/billing/limits`
**Purpose**
Return quota/limit state for the authenticated user.

**Response (target)**
```json
{
  "quota_status": {
    "allowed": true,
    "quota_enabled": true,
    "quota_mode": "default_quota_v1",
    "usage": {
      "requests": 120,
      "tokens_est": 45000,
      "estimated_cost": 3.42
    },
    "remaining": {
      "requests": 880,
      "tokens_est": 955000,
      "estimated_cost": 16.58
    }
  }
}
```

### `GET /api/v1/account/subscription`
**Purpose**
Return current plan/subscription-facing data.

**Phase decision**
Likely stub or hidden until there is real plan storage.

---

# 3. Mapping: old endpoints -> new endpoints

## 3.1 Auth area

### Keep
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/change-password`
- `POST /api/v1/auth/logout`

### Transitional decision
- `PUT /api/v1/auth/me`
  - short-term: keep working
  - long-term: deprecate in favor of `PUT /api/v1/account/profile`

---

## 3.2 Mock endpoints to replace

### Old: `GET /api/v1/auth/api-keys`
- **Action:** deprecate
- **Replacement:** `GET /api/v1/account/api-keys`

### Old: `GET /api/v1/auth/usage/stats`
- **Action:** deprecate
- **Replacement:** `GET /api/v1/account/usage/summary`

### Old: `GET /api/v1/auth/billing/summary`
- **Action:** deprecate
- **Replacement:** `GET /api/v1/account/billing/summary`

---

## 3.3 Current real logic that can be reused

### Reuse for profile
- current repository-backed user read/update logic from `user_auth.py` and `user_routes.py`

### Reuse for usage
- `read_usage_events()`
- `filter_usage_events()`
- `summarize_usage_events()`
- existing event schema written by `/api/v1/chat`

### Reuse for billing
- `summarize_billing_usage()`
- `classify_billable_flags()`
- `check_quota_allowance()`
- `load_billing_config()`

### Reuse for quota/limits
- `check_quota_allowance(user_id=...)`

---

# 4. Recommended implementation order for Part 2

## Phase 2A — establish truthful account surface
### Step 1
Implement:
- `GET /api/v1/account/profile`
- `PUT /api/v1/account/profile`

**Why first**
Lowest risk, immediate boundary win, reuses existing repository logic.

### Step 2
Implement:
- `GET /api/v1/account/usage/summary`
- `GET /api/v1/account/usage/events`

**Why second**
Real data can be derived immediately from existing usage ledger without inventing new fake structures.

### Step 3
Implement:
- `GET /api/v1/account/billing/summary`
- `GET /api/v1/account/billing/limits`

**Why third**
Also reusable from existing billing/quota logic once account surface exists.

### Step 4
Implement:
- `GET /api/v1/account/api-keys`
- `POST /api/v1/account/api-keys`
- `DELETE /api/v1/account/api-keys/{key_id}`

**Why fourth**
Requires new persistence model, so it is the first account feature that truly needs additional schema/storage work.

---

# 5. Decisions to adopt now

## Decision A
`/auth/*` is not the place for business/account dashboards.

## Decision B
`/api/v1/account/*` becomes the new truthful user-facing account surface.

## Decision C
Current mock endpoints under `/auth/*` should be treated as deprecated immediately, even before code removal.

## Decision D
Part 2 implementation should start with:
1. profile
2. usage
3. billing
4. api keys

---

# 6. Completion criteria for Part 2 design
Part 2 design is complete when:
1. auth/account boundary is explicit
2. `/api/v1/account/*` contract is defined
3. old mock endpoints are mapped to replacements
4. implementation order is fixed

Status: **COMPLETE (DESIGN)**

## Recommended next step
Move to Part 2 implementation, beginning with:
- `GET /api/v1/account/profile`
- `PUT /api/v1/account/profile`
- deprecation note/cleanup plan for `PUT /api/v1/auth/me`
