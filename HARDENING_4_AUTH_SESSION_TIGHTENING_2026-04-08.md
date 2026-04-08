# Hardening 4 — Auth / Session Tightening (2026-04-08)

## Objective
Tighten the auth/session layer after the previous hardening steps so the system is cleaner, less transitional, and more consistent.

---

## Current state entering Hardening 4
### Already implemented
- access + refresh token flow
- refresh rotation
- auth sessions list
- revoke current / revoke all refresh sessions
- forgot/reset password groundwork
- email verification groundwork
- account truth layer
- deprecated auth/account crossover endpoints

### Transitional / still loose
- `PUT /api/v1/auth/me` still overlaps with `/api/v1/account/profile`
- deprecated crossover endpoints still exist for compatibility only
- no explicit deprecation metadata in responses beyond message body
- no explicit session hygiene cleanup helper for expired tokens
- response contract around auth transitions can still be sharpened

---

## Hardening 4 priorities

### H4.1 — Make transitional endpoints more explicitly transitional
- keep compatibility where useful
- but make deprecation status clearer in response body
- reduce ambiguity around `/auth/me` vs `/account/profile`

### H4.2 — Tighten auth/account contract consistency
- ensure profile ownership belongs to account surface
- keep `/auth/me` as identity lookup
- clarify that profile mutation should move toward `/account/profile`

### H4.3 — Session hygiene helper
- introduce lightweight cleanup for expired/revoked token records if useful
- reduce long-term auth table drift in dev lane

### H4.4 — Re-check auth route clarity after tightening
- ensure auth surface reads as identity/session/auth lifecycle
- ensure account surface remains the place for business/account views

---

## Implementation approach
This hardening step should avoid unnecessary churn.
Prefer:
- clarity improvements
- lifecycle consistency
- cleanup helpers
- small contract signals

Avoid:
- breaking compatibility abruptly
- large refactors unrelated to current readiness goals

---

## Success criteria
Hardening 4 is successful when:
1. auth vs account boundary is even clearer
2. transitional surfaces are explicitly marked as such
3. session/token storage has at least minimal hygiene support
4. the auth layer feels tighter rather than larger

Status: **ANALYSIS COMPLETE — implement tightening changes next**
