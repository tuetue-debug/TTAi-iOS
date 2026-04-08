# API.TUETUE.VN Delivery Strategy Preparation (2026-04-08)

## Objective
Prepare a clean delivery strategy for:
- forgot/reset password
- email verification

so the system can move from dev bootstrap flows to a serious deployment lane without ambiguity.

---

# 1. Current delivery state
## What exists now
Backend groundwork exists for:
- forgot-password token issuance
- reset-password token consumption
- verify-email token issuance
- verify-email token consumption

## Current dev-lane behavior
- forgot-password may return reset token directly
- verify-email request may return verification token directly

## Why this is acceptable now
- useful for dev/bootstrap/testing
- no delivery integration required yet

## Why this is not enough later
In a serious lane, raw tokens should not be returned to ordinary clients as the primary delivery mode.

---

# 2. Delivery strategy decision

## Core decision
Adopt a **dual-lane delivery model**:

### Dev lane
- token-in-response allowed
- intended for local testing / controlled bootstrap only

### Serious lane
- token-in-response disabled for normal callers
- token must be delivered through an explicit delivery channel

This preserves velocity in development while avoiding weak operational patterns later.

---

# 3. Preferred serious-lane delivery channel
## Primary recommendation
**Email delivery** should be the primary serious-lane channel for:
- password reset instructions
- email verification links

### Why
- matches user expectation
- aligns naturally with auth lifecycle
- avoids introducing a custom side-channel too early

---

# 4. Delivery contract by flow

## A. Forgot / reset password
### Dev lane
`POST /api/v1/auth/forgot-password`
- may return:
  - reset token
  - expiry metadata

### Serious lane target
`POST /api/v1/auth/forgot-password`
- should return generic success message
- should not expose raw token
- should trigger delivery via email provider/integration

### Reset consumption
`POST /api/v1/auth/reset-password`
- remains token-based consume endpoint
- token arrives via delivered link or controlled handoff

---

## B. Verify email
### Dev lane
`POST /api/v1/auth/verify-email/request`
- may return verification token for local testing

### Serious lane target
`POST /api/v1/auth/verify-email/request`
- should return generic success message
- should trigger verification email delivery
- should not expose raw verification token to normal caller

### Verification consume endpoint
`POST /api/v1/auth/verify-email`
- remains token-based consume endpoint
- token arrives from delivered verification link

---

# 5. Strategy for rollout

## Phase 1 — current state
- backend token lifecycle exists
- token-in-response allowed in dev lane

## Phase 2 — delivery integration
Add a provider/integration abstraction for outbound auth messages.
Examples later could include:
- SMTP provider
- transactional mail provider
- internal notification bridge (only if clearly justified)

## Phase 3 — lane enforcement
Once delivery is available:
- disable raw token return in serious lane
- keep raw token return only in dev-like lanes

---

# 6. Implementation guidance
## Do next
- introduce explicit policy gate for token exposure by environment lane
- define delivery adapter abstraction before binding to one provider
- keep token consume endpoints unchanged where possible

## Do not do yet
- hardcode a specific mail provider too early without deployment decision
- enforce verify-email gating before delivery exists
- remove dev token-return flow before replacement path is ready

---

# 7. Recommended next technical move
After this strategy prep, the next implementation step should be:

## Add delivery exposure policy
Meaning:
- in dev-like lanes: allow token in response
- in serious lanes: suppress token in response and route toward delivery integration

This is the clean bridge between groundwork and real deployment behavior.

---

# 8. Final conclusion
The right strategy is not to choose between dev convenience and production discipline.
The right strategy is to separate them explicitly.

Status: **Delivery strategy preparation complete.**
