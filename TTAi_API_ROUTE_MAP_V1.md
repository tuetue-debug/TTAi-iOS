# TTAi API Route Map v1

_Last updated: 2026-04-05_

## Goal
Standardize the TTAi backend around clearer API namespaces while preserving backward compatibility for current live clients.

## Namespace policy
- **Preferred canonical namespace:** `/api/v1/...`
- **Legacy compatibility namespace:** existing `/api/...` routes remain available during migration
- **Root/system compatibility:** `/health` and `/health/detailed` remain, with `/api/v1/system/...` added as canonical aliases

---

## 1. Public / Product API
Used by `chat.tuetue.vn` and future user-facing clients.

### Chat
- Legacy: `POST /api/chat`
- Canonical: `POST /api/v1/chat`

### Classification
- Legacy: `POST /api/classify`
- Canonical: `POST /api/v1/classify`

- Legacy: `POST /api/classify/batch`
- Canonical: `POST /api/v1/classify/batch`

### Hybrid compatibility
- Legacy: `POST /api/hybrid/chat`
- Canonical: `POST /api/v1/hybrid/chat`

### User placeholders
- Legacy: `GET /api/users`
- Canonical: `GET /api/v1/users`

- Legacy: `POST /api/users`
- Canonical: `POST /api/v1/users`

---

## 2. Admin API
Used by `control.tuetue.vn` and internal operator tooling.

### Usage
- Legacy: `GET /api/admin/usage/events`
- Canonical: `GET /api/v1/admin/usage/events`

- Legacy: `GET /api/admin/usage/summary`
- Canonical: `GET /api/v1/admin/usage/summary`

- Legacy: `GET /api/admin/usage/users/{target_user_id}`
- Canonical: `GET /api/v1/admin/usage/users/{target_user_id}`

- Legacy: `GET /api/admin/usage/billing-summary`
- Canonical: `GET /api/v1/admin/usage/billing-summary`

### Quota
- Legacy: `GET /api/admin/quota/status`
- Canonical: `GET /api/v1/admin/quota/status`

- Legacy: `GET /api/admin/quota/status/users/{target_user_id}`
- Canonical: `GET /api/v1/admin/quota/status/users/{target_user_id}`

### Billing config
- Legacy: `GET /api/admin/billing/config`
- Canonical: `GET /api/v1/admin/billing/config`

- Legacy: `PUT /api/admin/billing/config`
- Canonical: `PUT /api/v1/admin/billing/config`

### Control dashboard proxy
- Canonical only (already namespaced):
  - `GET /api/v1/admin/control-dashboard`
  - `GET /api/v1/admin/control-dashboard/health-summary`
  - `GET /api/v1/admin/control-dashboard/providers`

---

## 3. System / Operations API
Used for operator/system/runtime visibility.

### Health
- Legacy: `GET /health`
- Canonical: `GET /api/v1/system/health`

- Legacy: `GET /health/detailed`
- Canonical: `GET /api/v1/system/health/detailed`

### Load balancer / provider control
- Legacy: `GET /api/loadbalancer/metrics`
- Canonical: `GET /api/v1/system/loadbalancer/metrics`

- Legacy: `GET /api/loadbalancer/providers`
- Canonical: `GET /api/v1/system/loadbalancer/providers`

- Legacy: `POST /api/loadbalancer/providers/{provider_name}/disable`
- Canonical: `POST /api/v1/system/loadbalancer/providers/{provider_name}/disable`

- Legacy: `POST /api/loadbalancer/providers/{provider_name}/enable`
- Canonical: `POST /api/v1/system/loadbalancer/providers/{provider_name}/enable`

### Test/debug endpoints
- Legacy: `GET /api/test/classification`
- Canonical: `GET /api/v1/test/classification`

- Legacy: `GET /api/test/loadbalancer`
- Canonical: `GET /api/v1/test/loadbalancer`

---

## 4. Model API
Used for provider/model/runtime visibility and warm-up controls.

### Models
- Legacy: `GET /api/models/status`
- Canonical: `GET /api/v1/models/status`

- Legacy: `GET /api/models/status/{model_name}`
- Canonical: `GET /api/v1/models/status/{model_name}`

- Legacy: `POST /api/models/warmup/{model_name}`
- Canonical: `POST /api/v1/models/warmup/{model_name}`

- Legacy: `POST /api/models/warmup/all`
- Canonical: `POST /api/v1/models/warmup/all`

### Ollama
- Legacy: `GET /api/ollama/models`
- Canonical: `GET /api/v1/ollama/models`

- Legacy: `GET /api/ollama/health`
- Canonical: `GET /api/v1/ollama/health`

- Legacy: `POST /api/ollama/generate`
- Canonical: `POST /api/v1/ollama/generate`

- Legacy: `POST /api/ollama/chat`
- Canonical: `POST /api/v1/ollama/chat`

---

## 5. Access model guidance

### Public/product-facing
- `/api/v1/chat`
- `/api/v1/classify`
- `/api/v1/classify/batch`
- future `/api/v1/auth/*`
- future `/api/v1/user/*`
- future `/api/v1/subscription/*`

### Admin-only
- `/api/v1/admin/usage/*`
- `/api/v1/admin/quota/*`
- `/api/v1/admin/billing/*`
- `/api/v1/admin/control-dashboard/*`

### Internal/system/operator
- `/api/v1/system/*`
- `/api/v1/models/*`
- `/api/v1/ollama/*`
- `/api/v1/test/*` (should eventually be internal/dev only)

---

## 6. Migration rule
For now:
- keep both legacy and canonical routes active
- migrate clients and docs toward `/api/v1/...`
- once `chat.tuetue.vn` and `control.tuetue.vn` are stable on canonical endpoints, legacy routes can be deprecated in a later phase
