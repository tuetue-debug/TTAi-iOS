# API.TUETUE.VN Delivery Bridge Contract (2026-04-08)

## Objective
Define the internal auth delivery provider contract so serious-lane delivery can be added cleanly without binding auth routes directly to one vendor.

---

# 1. Contract purpose
The auth delivery bridge exists to sit between:
- auth lifecycle logic
- concrete outbound delivery provider(s)

Its job is to:
- normalize auth delivery requests
- call the provider abstraction
- normalize results/failures
- keep auth routes clean and vendor-neutral

---

# 2. Input contract
## Required fields
### `message_type`
Allowed initial values:
- `password_reset`
- `email_verification`

### `to_email`
Destination email address.

### `token`
Opaque auth token value.

### `expires_at`
Timestamp or expiry metadata associated with the token.

## Recommended contextual fields
- `user_id`
- `user_name`
- `environment`
- `request_id`
- optional `tenant_id`
- optional `locale`

## Optional prepared fields
Depending on rollout design, bridge may receive either:
- raw token and build link later
- or prebuilt action URL

But the contract should be explicit about which mode is used.

---

# 3. Output contract
## Success result should include
- `ok: true`
- `delivery_mode`
- `provider_kind`
- optional `provider_message_id`
- optional `provider_trace_id`
- `status`

### Example success statuses
- `queued`
- `sent`
- `accepted`

## Failure result should include
- `ok: false`
- `delivery_mode`
- `provider_kind`
- `status: failed`
- `error_kind`
- `safe_message`
- optional `provider_trace_id`

---

# 4. Failure model
## Initial failure kinds
- `provider_not_configured`
- `provider_unavailable`
- `provider_timeout`
- `provider_rejected`
- `invalid_destination`
- `internal_error`

## Why explicit error kinds matter
They let auth routes and rollout logic distinguish between:
- expected rollout gaps
- configuration problems
- temporary provider incidents
- bad request state

---

# 5. Logging / trace rules
## Must log internally
- message type
- destination email (safe/redacted if needed)
- environment lane
- provider kind
- success/failure
- error kind if failed
- request/provider trace id if available

## Must NOT log casually
- raw reset token
- raw verification token
- sensitive secret payloads

## Principle
Trace enough to debug rollout, but do not turn auth delivery into a secret leak path.

---

# 6. Suggested provider abstraction shape
## Internal provider call
Something like:
- `send_auth_message(payload) -> result`

Where payload contains normalized bridge input.
Where result matches the normalized output contract above.

## Why this matters
Auth routes should not know:
- SMTP request shape
- third-party provider JSON shape
- vendor-specific response quirks

That all belongs below the bridge/provider layer.

---

# 7. Lane behavior relationship
## Dev lane
- bridge may return `inline_token` behavior upstream
- no outbound provider required

## Serious lane
- bridge should attempt provider delivery
- if provider not configured, return normalized `provider_not_configured` style failure or pending status according to rollout policy

This keeps lane logic above vendor logic.

---

# 8. Recommended next move
After defining this contract, the next implementation step should be:

## Build the first code-level provider interface
- payload model
- result model
- stub provider implementation
- serious-lane integration path through the bridge

Only after that should a concrete SMTP or transactional adapter be plugged in.

---

# 9. Final conclusion
The delivery bridge contract should be:
- message-type-driven
- vendor-neutral
- traceable
- safe about token exposure
- explicit about success/failure

Status: **Delivery bridge contract complete.**
