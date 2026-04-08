# API.TUETUE.VN Enforcement Decisions (2026-04-08)

## Objective
Decide what should actually be enforced after the hardening sprint, so the system can move from groundwork to deliberate policy.

---

# 1. Verified email enforcement
## Current state
- email verification lifecycle exists
- `email_verified` state exists
- no broad enforcement policy yet

## Decision
### Near-term policy
Do **not** immediately block general login or core account access based on email verification.

### Why
The current system has groundwork but not delivery integration yet. Enforcing too early would create friction without a complete delivery path.

## Recommended first enforcement targets
When email delivery is ready, enforce verified-email requirement first for:
- API key creation (optional early target)
- sensitive account changes (optional)
- future billing/subscription actions

## Not recommended yet
- blocking basic login
- blocking `/api/v1/auth/me`
- blocking existing recovery flows

### Judgment
Email verification should become a **graduated enforcement**, not an immediate blanket gate.

---

# 2. Auth/session policy enforcement
## Current state
- refresh rotation exists
- logout current/all exists
- reset password revokes refresh sessions
- session cleanup helper exists

## Decision
### Enforce now (conceptually / as contract direction)
- password reset invalidates refresh sessions ✅ already done
- refresh token reuse should remain invalid after rotation ✅ already done
- single-use reset/verify tokens ✅ already done

### Next enforcement candidates
- require stronger password policy beyond minimum length
- consider limiting refresh/session proliferation later
- consider admin-only or internal-only use of cleanup helper outside dev lane

### Judgment
Auth/session enforcement is good enough for current foundation; next improvements should be incremental, not disruptive.

---

# 3. Deprecated / transitional surface enforcement
## Current state
- `/api/v1/auth/api-keys` deprecated
- `/api/v1/auth/usage/stats` deprecated
- `/api/v1/auth/billing/summary` deprecated
- `PUT /api/v1/auth/me` transitional and explicitly deprecated in response

## Decision
### Near-term policy
Keep transitional/deprecated endpoints temporarily for compatibility.

### But enforce clarity now
All transitional surfaces must:
- signal deprecation clearly
- point to replacement surface
- not pretend to be the preferred contract

### Later cleanup target
Once callers/UI are aligned:
- remove deprecated auth/account crossover endpoints first
- then remove or hide low-value legacy aliases/test surfaces

### Judgment
Enforcement here is about **honesty first, removal second**.

---

# 4. Admin / control policy enforcement
## Current state
- admin/control auth has separate token/cookie model
- destructive control actions have env-sensitive handling

## Decision
### Serious lane expectation
- admin token must be explicit
- destructive actions should remain explicitly controlled by env/config
- control/admin surfaces should remain separate from product/account contract

### Judgment
Do not merge control convenience with product API simplicity.
Keep separation as a policy rule.

---

# 5. API key policy enforcement
## Current state
- API key create/list/revoke exists
- API key auth works in chat path
- no deep scope enforcement yet

## Decision
### Near-term policy
Treat API keys as valid auth credentials for current supported flows, but do not oversell scopes yet.

### Next enforcement target
- enforce scopes when more API-key-addressable actions exist
- avoid fake fine-grained permissions until real checks are in place

### Optional future gate
Require verified email before creating new API keys once email delivery exists.

---

# 6. Billing/quota enforcement
## Current state
- quota checks exist
- billing summary exists
- storage is still lightweight

## Decision
### Current policy
Quota/billing enforcement may continue in the current lightweight model for dev-lane truth.

### Caution
Do not market current billing/quota storage as full production-grade control-plane maturity yet.

---

# 7. Enforcement priorities

## Enforce now (already implemented or should be treated as active policy)
1. non-dev lanes require explicit JWT secret
2. password reset invalidates refresh sessions
3. refresh rotation invalidates prior refresh token
4. reset/verify tokens are single-use
5. deprecated surfaces must clearly identify replacements

## Enforce next (when supporting infrastructure is ready)
6. verified email for selected sensitive actions
7. stronger password policy
8. API key scope enforcement
9. more explicit admin/control restrictions by lane

## Enforce later
10. broader verified-email gating
11. full production-grade billing/usage durability assumptions
12. aggressive deprecated-surface removal once callers migrate

---

# 8. Final conclusion
The right move is not blanket enforcement everywhere.
The right move is staged enforcement:
- enforce what is already structurally supported
- avoid fake enforcement where delivery/integration is not ready
- keep the contract honest while preparing tighter rules

Status: **Enforcement decisions complete.**
