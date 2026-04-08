# TTAi FastAPI Auth Environment Contract

## Purpose
This file defines the minimum JWT/auth environment expectations for `api.tuetue.vn`.

---

## Canonical JWT secret variable
Use:
- `TTAI_JWT_SECRET`

Compatibility aliases still accepted in code:
- `JWT_SECRET`
- `FASTAPI_JWT_SECRET`

Operational guidance:
- prefer `TTAI_JWT_SECRET`
- do not rely on aliases in new deployment docs

---

## Environment lanes
### Dev-like lanes
Accepted values:
- `dev`
- `development`
- `local`
- `test`

Behavior:
- if JWT secret is missing, the app may use the built-in development fallback
- a warning is expected in logs
- this is acceptable only for local/dev bootstrap

### Non-dev lanes
Accepted values:
- `prod`
- `production`
- `staging`

Behavior:
- `TTAI_JWT_SECRET` (or compatible alias) is required
- startup must not rely on fallback secret
- missing secret is a deployment/configuration error

---

## Required non-dev auth envs
Minimum expectation for non-dev:
- `TTAI_JWT_SECRET=<strong-random-secret>`
- `ENVIRONMENT=production` (or `staging`)

Recommended:
- avoid hardcoding secrets in source-controlled files
- inject through deployment environment or secret manager

---

## Rotation guidance
- rotate JWT secrets intentionally, not casually
- understand that rotating the secret invalidates existing JWT access tokens
- if refresh/session invalidation model evolves further, update this runbook accordingly

---

## Current status
This contract matches the current auth implementation:
- dev lanes may bootstrap with warning
- non-dev lanes must provide explicit secret

If future auth hardening changes token/session behavior, update this file in the same sprint.
