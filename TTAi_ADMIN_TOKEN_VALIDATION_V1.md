# TTAi Admin Token Validation v1

_Last updated: 2026-04-05_

## Goal
Replace the previous admin-auth stub (any non-empty bearer token) with actual bearer token validation for TTAi admin/control routes.

## Current behavior
Admin routes now validate the bearer token against:
1. `TTAI_ADMIN_TOKEN`
2. `FASTAPI_ADMIN_TOKEN`
3. fallback development token: `ttai-dev-admin-token`

## Why this shape
This keeps the transition safe:
- development/runtime testing works immediately
- live deployment can switch to a real secret via environment
- admin/control boundary is now meaningful instead of accepting any bearer token

## Important warning
The fallback token is only for transition/development.
Before long-term live use, production should explicitly set:
- `TTAI_ADMIN_TOKEN=<strong-random-secret>`

## Validation logic
- missing bearer token → `401 Not authenticated`
- wrong bearer token → `403 Invalid admin token`
- correct bearer token → request allowed

## Protected use cases
Applies to admin/control routes already wired with `get_current_admin_user`, including:
- admin usage / billing / quota endpoints
- billing config write/read endpoints
- system provider enable/disable
- model warm-up routes
- control dashboard proxy routes

## Recommended production next step
Set admin token in service environment, for example through NSSM environment configuration, then restart `TTAiFastAPI8000` and verify live admin endpoints with the configured bearer token.
