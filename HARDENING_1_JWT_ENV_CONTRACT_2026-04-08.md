# Hardening 1 — JWT / Env Contract Cleanup (2026-04-08)

## Objective
Strengthen the JWT/environment contract for `api.tuetue.vn` so the auth layer behaves clearly and safely across development vs non-development lanes.

---

## Current observed behavior
### What exists today
- `get_jwt_secret()` reads:
  - `TTAI_JWT_SECRET`
  - `JWT_SECRET`
  - `FASTAPI_JWT_SECRET`
- if configured secret exists, it is used
- if not configured:
  - production/staging raises runtime error
  - development/local/test falls back to embedded dev secret

### What this gets right
- non-dev lanes are not allowed to silently continue without a secret
- dev lane remains easy to bootstrap

### What is still too soft
- no explicit documented env contract file yet
- no explicit startup guidance for operators
- no single canonical variable preference documented outside code
- fallback warnings are correct but not yet operationalized into a short runbook

---

## Hardening decisions

### Decision 1 — Canonical variable
Use `TTAI_JWT_SECRET` as the primary documented variable.

Other vars may remain accepted for compatibility:
- `JWT_SECRET`
- `FASTAPI_JWT_SECRET`

But docs/runbooks should push:
- `TTAI_JWT_SECRET`

---

### Decision 2 — Environment interpretation
Treat these as non-dev:
- `prod`
- `production`
- `staging`

Treat these as dev-like:
- `dev`
- `development`
- `local`
- `test`

---

### Decision 3 — Required behavior by lane
#### Dev-like lanes
- fallback secret allowed
- warning must remain visible
- acceptable for local bootstrap only

#### Non-dev lanes
- startup must fail without configured secret
- no silent fallback
- this is already directionally correct and should stay

---

### Decision 4 — Next operational cleanup
Need a short env contract/runbook covering:
- required env vars for non-dev
- recommended env vars for dev
- what happens if JWT secret is absent
- rotation expectation for secrets

---

## Recommended deliverables for this hardening step
1. add a short runbook/doc for JWT env contract
2. ensure wording in code/logs points to `TTAI_JWT_SECRET` first
3. optionally add a tiny startup check/helper doc note in deployment paths

---

## Current judgment
The code-level guard is already reasonably good.
What is missing is the **explicit operational contract**.

So Hardening 1 should focus on:
- making the contract explicit
- reducing ambiguity for future deployment
- keeping dev velocity while tightening non-dev expectations

Status: **ANALYSIS COMPLETE — implement docs/runbook next**
