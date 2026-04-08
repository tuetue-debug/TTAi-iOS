# API.TUETUE.VN Delivery Provider Strategy (2026-04-08)

## Objective
Define the delivery-provider strategy for serious-lane auth flows, especially:
- forgot/reset password
- email verification

This strategy should be practical enough for rollout preparation, but not prematurely lock the system into the wrong provider shape.

---

# 1. Core strategy choice
## Recommended strategy
Adopt a **provider abstraction around outbound auth email delivery**, with email as the primary serious-lane channel.

### Meaning
The backend should not hardcode one vendor as the auth contract.
Instead, it should define an internal delivery interface and let the actual provider implementation sit behind it.

---

# 2. Why email is the right primary channel
## For forgot/reset password
Email is the natural primary channel because:
- users expect password reset by email
- token/link delivery fits standard auth UX
- it avoids inventing a custom side-channel

## For verify email
Email is obviously the primary verification target because:
- the goal is to prove address ownership
- direct mail delivery is the cleanest proof path

### Conclusion
Use **email delivery as the first-class serious-lane target**.

---

# 3. Provider shape recommendation
## Do not choose by brand first
Choose by interface first.

### Internal provider contract should support:
- destination email address
- message type
- token or generated link payload
- expiry metadata
- optional user/context metadata
- success/failure result
- provider response trace id if available

## Suggested auth delivery message types
- `password_reset`
- `email_verification`

This keeps auth delivery clean and extensible.

---

# 4. Preferred implementation shape
## Layering
### Layer A — Auth flow
- forgot/reset logic
- verify-email logic
- token lifecycle

### Layer B — Auth delivery bridge
- decides lane behavior
- shapes delivery payload
- invokes provider abstraction when serious-lane delivery is required

### Layer C — Provider implementation
Examples later could be:
- SMTP adapter
- transactional email service adapter
- other mail delivery adapter

### Why this shape is right
It prevents the auth lifecycle from becoming tightly coupled to one vendor.

---

# 5. Rollout recommendation
## Phase 1 — provider abstraction first
Implement a provider interface / service boundary before binding to a real mail provider.

## Phase 2 — first provider adapter
Choose one serious-lane adapter for rollout.
This may be:
- SMTP
- transactional mail provider

## Phase 3 — lane enforcement
In serious lane:
- auth flows should attempt real provider delivery
- inline token return should remain suppressed
- failures should be reported clearly and safely

---

# 6. What not to do
## Avoid these mistakes
- hardcoding a vendor-specific API shape directly into auth routes
- exposing raw tokens in serious lane just because provider is not ready
- building auth around a provider-specific response contract
- mixing product messaging channels with core auth delivery without a clear security model

---

# 7. Practical recommendation for next step
## Best next technical move
Implement the **internal auth delivery provider contract** first.

That contract should answer:
- what the auth layer asks the provider to do
- what the provider returns
- how failures are represented

Only after that should a concrete provider adapter be chosen or built.

---

# 8. Final conclusion
The right provider strategy is:
- **email-first** for serious-lane auth flows
- **provider-abstracted** instead of vendor-hardcoded
- **lane-aware** so dev convenience and serious delivery stay clearly separated

Status: **Delivery provider strategy complete.**
