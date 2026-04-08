# API.TUETUE.VN Cleanup Readiness (2026-04-08)

## Objective
Decide what can be cleaned up now, what should remain transitional for compatibility, and what should only be removed after deployment/delivery lanes are ready.

---

# 1. Remove soon (when callers are confirmed migrated)
## Auth/account crossover deprecated endpoints
- `GET /api/v1/auth/api-keys`
- `GET /api/v1/auth/usage/stats`
- `GET /api/v1/auth/billing/summary`

### Why
These no longer represent the truthful contract and only exist for compatibility.

### Cleanup condition
Remove once UI/callers are confirmed to use `/api/v1/account/*` only.

---

# 2. Keep transitional for now
## `PUT /api/v1/auth/me`
### Why keep temporarily
- compatibility bridge for any existing caller using auth surface for profile mutation

### Why not keep forever
- profile mutation belongs to account surface
- keeping both forever weakens boundary clarity

### Future target
Deprecation first (already done), removal later after callers align to:
- `PUT /api/v1/account/profile`

---

# 3. Hide / internal-only candidates
## Internal verification helper
- `GET /api/v1/auth/api-key/me`

### Judgment
Useful for validation/debugging, but not necessarily a first-class public product contract forever.
Could be documented as internal/debug or admin-supportive rather than end-user-facing.

## Test/debug surfaces
- `/api/test/*`

### Judgment
Hide or disable outside dev/test lanes.

---

# 4. Legacy alias cleanup candidates
## Unversioned / older alias surfaces
Examples include:
- `/api/chat`
- `/api/admin/*` aliases where `/api/v1/admin/*` exists
- `/api/loadbalancer/*` aliases where versioned paths exist
- `/api/models/*` aliases where versioned paths exist
- `/api/ollama/*` aliases where versioned paths exist

### Judgment
Do not rush removal blindly.
But they should no longer be treated as the preferred contract.

### Cleanup condition
- confirm no required caller depends on them
- prefer documenting only versioned routes first
- remove in a controlled cleanup sprint later

---

# 5. Keep until deployment/delivery lane is ready
## Token-return behavior in dev-only auth flows
- forgot-password returning reset token
- verify-email/request returning verification token

### Judgment
Do not remove this behavior before serious-lane delivery exists.
The right move is lane-based suppression later, not premature removal now.

---

# 6. Cleanup priorities

## Priority A — contract cleanliness
1. stop documenting deprecated crossover auth/account endpoints as real surfaces
2. prefer `/api/v1/account/*` everywhere in docs/UI
3. treat `PUT /api/v1/auth/me` as transitional only

## Priority B — visibility cleanup
4. hide `/api/test/*` outside dev/test lanes
5. classify `/api/v1/auth/api-key/me` as internal/debug unless long-term product need emerges

## Priority C — later removal
6. remove deprecated crossover endpoints after migration confirmation
7. later reduce legacy alias surfaces in controlled batch

---

# 7. What should NOT be cleaned prematurely
- auth delivery token exposure in dev lane
- transitional compatibility before caller migration
- internal helpers still needed for debugging/validation

Reason:
Premature cleanup creates instability without improving real readiness.

---

# 8. Final conclusion
Cleanup should be staged.
The goal is not aggressive deletion; the goal is a cleaner truthful contract with minimal compatibility risk.

Status: **Cleanup readiness complete.**
