# API.TUETUE.VN Mini Re-Readiness Pass After API-Key Chat Fix (2026-04-08)

## Why this update exists
A critical integration defect was confirmed and then fixed:
- API-key-authenticated chat requests executed successfully
- but usage events incorrectly recorded `user_id` as `anonymous`
- which prevented account usage/billing surfaces from reflecting owner-linked API-key traffic correctly

After root-cause debugging and re-test, this mini pass updates the true readiness state.

---

# 1. What changed after the fix
## Root cause fixed
`/api/v1/chat` now resolves and uses the owning user identity consistently for API-key-authenticated requests.

## Re-test outcome
Confirmed after fix:
- API-key-authenticated chat returns 200
- usage event contains correct `user_id`
- usage event contains correct `api_key_id`
- account usage surfaces show the event
- billing summary reflects the event

---

# 2. Readiness status changes

## Upgraded: PARTIAL -> READY
### `/api/v1/chat` via API-key-authenticated accounting path
**Previous status:** PARTIAL
**New status:** READY (for current dev-lane foundation)

### Why upgraded
Because the most important missing trust property is now satisfied:
- request executes
- identity resolves
- event writes correctly
- account surfaces reflect the result

This closes the most important known integration gap from the prior readiness pass.

---

# 3. Updated readiness summary

## READY / USABLE FOUNDATION
### Auth
- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/auth/refresh`
- `/api/v1/auth/sessions`
- `/api/v1/auth/logout`
- `/api/v1/auth/change-password`

### Account
- `/api/v1/account/profile`
- `/api/v1/account/usage/summary`
- `/api/v1/account/usage/events`
- `/api/v1/account/billing/summary`
- `/api/v1/account/billing/limits`
- `/api/v1/account/api-keys`
- `POST /api/v1/account/api-keys`
- `DELETE /api/v1/account/api-keys/{key_id}`

### Chat
- `/api/v1/chat` via user identity path
- `/api/v1/chat` via API-key-authenticated path

---

## STILL PARTIAL / STILL NEEDS HARDENING
### Security/config
- dev fallback JWT secret still appears in non-configured runs
- not yet equivalent to production-hardening

### Auth completeness
- no forgot/reset password yet
- no verify email yet
- no access-token revocation model yet
- limited session/device metadata

### Storage maturity
- auth/api keys on SQLite dev lane
- usage on JSONL ledger
- billing config on JSON
- acceptable for current foundation, not final operations model

### Contract cleanup
- transitional `PUT /api/v1/auth/me` still exists
- deprecated auth crossover endpoints still present for compatibility
- legacy aliases/test endpoints still need later cleanup/hiding

---

# 4. Current honest position
`api.tuetue.vn` now qualifies as a **stronger usable backend foundation** than before.

It is not merely a scaffold anymore.
It now has:
- auth lifecycle foundation
- truthful account surface
- API-key lifecycle
- API-key-authenticated chat with correct owner-linked telemetry
- smoke-tested and debug-validated core flows

That said, it should still be described as:

## Current label
**Dev-lane ready, integration-clean for the tested core paths, but not yet fully production-hardened.**

---

# 5. Best next move
Now that the most important integration defect is fixed, the next best move is not random expansion.
The next best move is one of:

## Option A — hardening sprint
- JWT/env contract cleanup
- forgot/reset password
- verify email groundwork
- token/session model tightening

## Option B — contract cleanup sprint
- deprecate/hide remaining transitional endpoints
- clean legacy aliases
- prepare docs/UI to use only truthful surfaces

## Recommended next move
**Option A first, then Option B.**
Because the backbone is now cleaner, so the best value is to harden it.

---

# 6. Final update
The previously critical API-key accounting linkage defect is fixed and verified.
That raises the trust level of the whole `api.tuetue.vn` foundation.

Status: **Mini re-readiness pass complete; core chat/account/auth foundation is materially stronger now.**
