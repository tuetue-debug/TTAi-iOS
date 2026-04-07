# B2 Auth Persistence Audit — 2026-04-08

## Scope
Stabilized the FastAPI dev-lane auth foundation in `repos/TTAi-deployment/fastapi` without touching the production 8000 deployment path.

## What changed
- Replaced in-memory auth storage (`_users_db`, `_next_user_id`) with a SQLite-backed `UserRepository` in `user_auth.py`.
- Added auto-init for the `users` table and email index.
- Added a dev-safe bootstrap path that can seed one test user via env-controlled settings.
- Kept the existing auth route surface stable for:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
  - `PUT /api/v1/auth/change-password`
  - `POST /api/v1/auth/logout`
- Updated `PUT /api/v1/auth/me` to persist profile changes through the repository instead of mutating a module-global dict.
- Improved JWT config handling:
  - prefers `TTAI_JWT_SECRET`
  - falls back to `JWT_SECRET` / `FASTAPI_JWT_SECRET`
  - only uses a dev fallback secret outside configured envs when runtime is clearly development-like
  - raises at runtime for missing secret in `prod` / `production` / `staging`
- Added explicit Python dependency declarations for auth packages in `requirements.txt`.

## Persistence details
- Default auth DB path: `fastapi/data/auth_dev.sqlite3`
- Override via: `TTAI_AUTH_DB_PATH`
- Dev seed controls:
  - `TTAI_AUTH_SEED_TEST_USER=0` to disable
  - `TTAI_AUTH_SEED_EMAIL`
  - `TTAI_AUTH_SEED_NAME`
  - `TTAI_AUTH_SEED_PASSWORD`

## Remaining gaps / known limits
- `logout` is still stateless/client-side; there is no token revocation or refresh-token store yet.
- Auth persistence is SQLite for the dev lane; that is appropriate here, but multi-instance production auth should move to a shared DB.
- No Alembic-style migration system yet; current init path is auto-create-on-start for the single `users` table.
- Password policy is still minimal (length >= 8). Stronger rules and reset flows can be added later.
- Mock API keys / usage / billing auth-adjacent endpoints remain mock-only and were intentionally left alone.

## Verification performed
Smoke-tested auth routes in an isolated FastAPI app using the updated router and a temporary SQLite DB:
- register
- login
- me
- change-password
- login with new password
- logout

Result: pass (`AUTH_SMOKE_OK`)
