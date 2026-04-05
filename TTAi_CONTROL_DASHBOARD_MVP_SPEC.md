# TTAi Control Dashboard MVP Spec

_Last updated: 2026-04-05_

## 1. Purpose

`control.tuetue.vn` is the admin/operator console for the TTAi system.

Its role is to give clear operational visibility into:
- API usage
- quota and billing state
- model/provider/runtime health
- system status
- controlled admin actions

This MVP should prioritize **safe visibility first**.
That means:
- read-only features first
- low-risk actions second
- high-risk mutation actions later, with clear confirmation and auth boundaries

---

## 2. Guiding principle

### Build order for Control MVP
1. **Read-only dashboards first**
2. **Read + filtered drill-down second**
3. **Low-risk admin actions later**
4. **High-risk write actions only after UI discipline and audit plan**

### Non-goal for MVP
Do **not** try to turn Control into a full DevOps console immediately.
MVP should help the operator see the system clearly without increasing the chance of breaking the live stack.

---

## 3. Current protected live foundations

The dashboard MVP must respect the fact that the following are already live and should not be destabilized:
- `TTAiFastAPI8000` on port `8000`
- CLI proxy integration through `https://127.0.0.1:8317`
- usage metering
- billing summary
- quota enforcement
- quota status APIs
- billing config APIs
- `/api/v1/...` canonical routes
- admin token validation v1

### Protected env assumptions
The service currently depends on these env vars in NSSM `AppEnvironmentExtra`:
- `CLI_PROXY_API_KEY=cliproxy-dev-token`
- `TTAI_ADMIN_TOKEN=<production secret>`

---

## 4. MVP modules

## Module A — Overview
Purpose: fast top-level health and business snapshot.

### MVP contents
- service health
- detailed health snapshot
- total request counts (windowed)
- total estimated cost
- billable vs non-billable split
- top tenant/API key/provider summaries

### Recommended sources
- `GET /api/v1/system/health`
- `GET /api/v1/system/health/detailed`
- `GET /api/v1/admin/usage/summary`
- `GET /api/v1/admin/usage/billing-summary`

### Risk level
- **Read-only / safe**

---

## Module B — Usage
Purpose: inspect request flow and recent metering events.

### MVP contents
- recent usage events table
- filters by:
  - tenant
  - api key
  - provider
  - model
  - status
  - billable flags
- user-specific usage drilldown

### Recommended sources
- `GET /api/v1/admin/usage/events`
- `GET /api/v1/admin/usage/summary`
- `GET /api/v1/admin/usage/users/{target_user_id}`

### Risk level
- **Read-only / safe**

---

## Module C — Billing
Purpose: understand estimated cost and billable activity.

### MVP contents
- billing summary
- per tenant estimated cost
- per API key estimated cost
- provider cost breakdown
- billable mode breakdown
- current billing config viewer

### Recommended sources
- `GET /api/v1/admin/usage/billing-summary`
- `GET /api/v1/admin/billing/config`

### Risk level
- **Read-only for MVP**
- billing config editing should be deferred behind stronger UI safeguards

---

## Module D — Quota
Purpose: monitor quota usage and identify blocked or near-limit consumers.

### MVP contents
- quota lookup by tenant/api key/user
- remaining request/token/cost allowance
- blocked entities and reasons
- quick quota diagnostics panel

### Recommended sources
- `GET /api/v1/admin/quota/status`
- `GET /api/v1/admin/quota/status/users/{target_user_id}`

### Risk level
- **Read-only / safe**

---

## Module E — Models
Purpose: inspect runtime model/provider state.

### MVP contents
- provider list
- load balancer metrics
- model status list
- individual model status
- Ollama health
- Ollama model list

### Recommended sources
- `GET /api/v1/system/loadbalancer/metrics`
- `GET /api/v1/system/loadbalancer/providers`
- `GET /api/v1/models/status`
- `GET /api/v1/models/status/{model_name}`
- `GET /api/v1/ollama/health`
- `GET /api/v1/ollama/models`

### Risk level
- **Read-only / safe**

---

## Module F — System
Purpose: operator visibility into the running platform.

### MVP contents
- service health summary
- detailed health snapshot
- control dashboard proxy data if needed
- diagnostics links / operator quick actions section (read-focused initially)

### Recommended sources
- `GET /api/v1/system/health`
- `GET /api/v1/system/health/detailed`
- `GET /api/v1/admin/control-dashboard`
- `GET /api/v1/admin/control-dashboard/health-summary`
- `GET /api/v1/admin/control-dashboard/providers`

### Risk level
- **Mostly read-only in MVP**

---

## 5. Deferred write actions (not default for MVP)

These actions exist or will exist, but should not be first-class dashboard actions until the UI has confirmations, role checks, and safer auditability.

### Existing high-risk actions
- `POST /api/v1/system/loadbalancer/providers/{provider_name}/disable`
- `POST /api/v1/system/loadbalancer/providers/{provider_name}/enable`
- `POST /api/v1/models/warmup/{model_name}`
- `POST /api/v1/models/warmup/all`
- `PUT /api/v1/admin/billing/config`

### Rule
These should be placed under:
- secondary operator sections
- explicit confirmation dialogs
- admin token protected flows
- ideally action audit logging in a later phase

---

## 6. API mapping matrix

| Control module | Need | Current API status | Notes |
|---|---|---|---|
| Overview | health summary | Available | Safe MVP |
| Overview | usage summary | Available | Safe MVP |
| Overview | billing summary | Available | Safe MVP |
| Usage | event table | Available | Safe MVP |
| Usage | user drilldown | Available | Safe MVP |
| Billing | billing summary | Available | Safe MVP |
| Billing | billing config view | Available | Safe MVP |
| Quota | quota lookup | Available | Safe MVP |
| Models | provider metrics | Available | Safe MVP |
| Models | model status | Available | Safe MVP |
| Models | Ollama health/models | Available | Safe MVP |
| System | control dashboard proxy | Available | Admin auth required |
| System | restart/failover controls | Missing / deferred | Do later |
| Billing | safer config patch UI | Missing | Do later |
| Overview | aggregate KPI endpoint | Optional improvement | Could simplify frontend |

---

## 7. Missing or desirable endpoints for later

These are not required for MVP launch, but would improve the dashboard later.

### Nice-to-have next endpoints
1. **Combined overview endpoint**
   - a single admin endpoint that aggregates:
     - health
     - usage summary
     - billing summary
     - quota highlights

2. **Blocked quota list endpoint**
   - list keys/tenants/users currently denied by quota

3. **Top error endpoint**
   - summarize frequent failures by provider/model/status

4. **Read-only billing config metadata endpoint**
   - simpler UI payload for config version / updated_at / counts

5. **Audit trail endpoints**
   - especially once write actions appear in Control

---

## 8. UI layout suggestion

## Top navigation / sidebar
- Overview
- Usage
- Billing
- Quota
- Models
- System

## Page layout idea
### Overview page
- health cards
- request + cost summary cards
- top tenants/providers widgets
- recent alerts/notes

### Usage page
- filter bar
- events table
- user drilldown panel

### Billing page
- cost cards
- billable breakdown charts
- tenant/api key breakdown tables
- billing config viewer

### Quota page
- search/lookup form
- quota result panel
- blocked/near-limit highlights

### Models page
- provider table
- model status cards
- Ollama health widget

### System page
- health detail
- proxy collector data
- protected operator actions section (disabled/hidden initially)

---

## 9. Safety / do-not-break rules

Control work must follow these rules:

### Route safety
- do not remove legacy routes yet
- prefer `/api/v1/...` from the dashboard

### Deployment safety
- test backend changes on temp ports first
- do not push large API refactors straight to `:8000`

### Env safety
- do not overwrite NSSM `AppEnvironmentExtra` incorrectly
- always preserve:
  - `CLI_PROXY_API_KEY`
  - `TTAI_ADMIN_TOKEN`

### Chat safety
- avoid risky rewrites to `/api/chat`
- protect the live chat path from dashboard-related churn

### Write-action safety
- high-risk actions should remain secondary
- require admin auth
- later add explicit confirmation and audit trail

---

## 10. Recommended next implementation order

### Step 1
Build the Control MVP as **read-only first** using already-available endpoints.

### Step 2
Add a frontend-friendly overview aggregation endpoint only if the UI becomes too chatty.

### Step 3
Add limited admin actions with confirmation flows:
- model warm-up
- provider enable/disable

### Step 4
Add stronger admin auth / RBAC / audit logs.

### Step 5
Add higher-risk config editing UX (billing/quota settings) only after auditability is ready.

---

## 11. Final MVP statement

For the first real version of `control.tuetue.vn`:
- make it highly useful for visibility
- keep it mostly read-only
- treat write actions as privileged and delayed
- build on the current live API foundation without destabilizing the core TTAi backend
