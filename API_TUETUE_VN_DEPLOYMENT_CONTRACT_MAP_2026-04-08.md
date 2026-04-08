# API.TUETUE.VN Deployment Contract Map (2026-04-08)

## Objective
Map the real deployment contract of `api.tuetue.vn` after the hardening sprint, separating:
- required non-dev settings
- recommended dev settings
- optional/runtime-dependent settings
- risky defaults that should not silently survive into a serious deployment lane

---

# 1. Environment identity / deployment lane
## Variables observed
- `ENVIRONMENT`
- `ENV`
- `APP_ENV`
- `TTAI_ENV`

## Current behavior
Runtime environment resolves from the first populated value in that order.

## Deployment decision
### Canonical variable for deployment docs
- `ENVIRONMENT`

### Allowed non-dev values
- `prod`
- `production`
- `staging`

### Allowed dev-like values
- `dev`
- `development`
- `local`
- `test`

### Recommendation
Use only:
- `ENVIRONMENT=development` for dev lane
- `ENVIRONMENT=production` (or `staging`) for serious lane

Avoid mixing aliases in deployment docs.

---

# 2. Auth / JWT contract
## Variables observed
- `TTAI_JWT_SECRET`
- `JWT_SECRET`
- `FASTAPI_JWT_SECRET`

## Canonical deployment variable
- `TTAI_JWT_SECRET`

## Non-dev requirement
For `ENVIRONMENT in {production, staging, prod}`:
- `TTAI_JWT_SECRET` is required
- fallback secret must not be relied on

## Dev lane behavior
If missing:
- app may use development fallback secret
- warning appears in logs

## Deployment judgment
### REQUIRED for non-dev
- `TTAI_JWT_SECRET`

### RISK if omitted in serious lane
- auth integrity is unacceptable
- token trust collapses

---

# 3. Auth DB / dev seeding
## Variables observed
- `TTAI_AUTH_DB_PATH`
- `TTAI_AUTH_SEED_TEST_USER`
- `TTAI_AUTH_SEED_EMAIL`
- `TTAI_AUTH_SEED_NAME`
- `TTAI_AUTH_SEED_PASSWORD`

## Current behavior
- auth DB defaults to local SQLite under `data/auth_dev.sqlite3`
- dev seed user may be created in dev-like lanes

## Deployment judgment
### REQUIRED to decide explicitly in non-dev
- `TTAI_AUTH_DB_PATH` (or explicit acceptance of default path if intentionally local-only)
- `TTAI_AUTH_SEED_TEST_USER=0`

### Strong recommendation
Disable dev seed in any serious lane.

### Risk if left loose
- surprise seeded accounts in wrong lane
- unclear auth state pathing

---

# 4. Admin / control auth contract
## Variables observed
- `TTAI_ADMIN_TOKEN`
- `FASTAPI_ADMIN_TOKEN`
- `TTAI_CONTROL_COOKIE_SECURE`

## Current behavior
- admin/control auth token resolves from env
- control cookie secure behavior depends on env/config helper

## Deployment judgment
### REQUIRED for serious lane
- explicit admin token (`TTAI_ADMIN_TOKEN` preferred)
- secure cookie posture should be reviewed explicitly

### Recommendation
Document control/admin auth separately from end-user auth to avoid confusion.

---

# 5. CLI proxy / model runtime integration
## Variables observed
- `CLI_PROXY_URL`
- `CLI_PROXY_API_KEY`

## Current behavior
- chat fallback / selected provider path may call CLI proxy
- default URL falls back to `https://127.0.0.1:8317`

## Deployment judgment
### REQUIRED if serious lane depends on CLI proxy
- `CLI_PROXY_URL`
- `CLI_PROXY_API_KEY` when proxy expects auth

### Risk if omitted or left implicit
- fallback path may behave unpredictably
- local assumptions may leak into non-local lane

---

# 6. Ollama runtime integration
## Variables observed
- `OLLAMA_BASE_URL`
- `OLLAMA_MAX_WORKERS`
- `MAX_WORKERS`
- `OLLAMA_REQUEST_TIMEOUT`
- `TIMEOUT`

## Deployment judgment
### REQUIRED if lane depends on Ollama
- `OLLAMA_BASE_URL`

### Recommended
- explicit worker/timeout settings instead of relying on generic defaults

### Risk if omitted
- runtime assumptions may be wrong for remote/self-hosted topology

---

# 7. Billing / quota operational data
## Files in current design
- `data/billing_config.json`
- usage ledger JSONL
- auth SQLite

## Deployment judgment
### Must be acknowledged in serious lane
These are not full ops-grade storage contracts yet.

### Recommendation
Before serious deployment claims, explicitly document:
- where billing config lives
- backup expectations
- how usage ledger retention is handled
- what durability guarantees exist today vs later

---

# 8. Deployment contract by category

## REQUIRED FOR NON-DEV / SERIOUS LANE
- `ENVIRONMENT=production` (or `staging`)
- `TTAI_JWT_SECRET=<strong-secret>`
- `TTAI_ADMIN_TOKEN=<strong-secret>`
- `TTAI_AUTH_SEED_TEST_USER=0`
- explicit decision for `TTAI_AUTH_DB_PATH`
- explicit decision for `CLI_PROXY_URL` / `CLI_PROXY_API_KEY` if proxy path is used
- explicit decision for `OLLAMA_BASE_URL` if Ollama path is used

## RECOMMENDED FOR DEV LANE
- `ENVIRONMENT=development`
- optional `TTAI_JWT_SECRET` (fallback tolerated for local only)
- optional dev seed settings if intentionally used
- explicit local runtime URLs where possible

## OPTIONAL / RUNTIME-DEPENDENT
- worker counts / request timeouts
- cookie secure override depending on deployment topology
- quota/billing config content itself

## RISKY DEFAULTS TO ELIMINATE IN SERIOUS LANE
- fallback JWT secret
- implicit dev seed user
- implicit local CLI proxy URL assumptions
- implicit local Ollama URL assumptions
- unspoken file-path defaults for auth/billing data

---

# 9. Current conclusion
The codebase is now strong enough that the next deployment-phase work should focus on:
1. explicit env contract adoption
2. non-dev secret/token discipline
3. explicit runtime dependency decisions
4. preventing dev defaults from leaking into serious deployment

Status: **Deployment contract map complete.**
