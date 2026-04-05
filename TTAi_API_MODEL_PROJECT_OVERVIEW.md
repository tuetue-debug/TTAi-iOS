# TTAi API Model - Project Overview

_Last updated: 2026-04-05_

## 1. Purpose

TTAi API Model is the overall architecture for Tuệ Tuệ's product, control plane, and backend intelligence stack.

This project is intentionally split into separate surfaces so the system can grow cleanly:
- **User/Product surface**
- **Admin/Control surface**
- **Backend/Core intelligence surface**

At the center of the system is **TTAi Super Model Hybrid**, which acts as the core inference and orchestration brain. Over time, this layer is expected to evolve into Tuệ Tuệ's own model/core intelligence foundation.

---

## 2. Domain / Surface Architecture

### 2.1 `chat.tuetue.vn`
**Role:** End-user / product UI

Primary purpose:
- User chat experience
- Product-facing interaction surface
- Later: login, plans, subscriptions, personal usage, and billing views

Planned functions:
- Chat playground / assistant UI
- Authenticated user workspace
- Usage overview for end users
- Plan/package selection
- Subscription and billing views
- Navigation to docs/help and possibly control links for authorized admins

Design rule:
- `chat.tuetue.vn` should stay product-facing and user-friendly
- It should call backend APIs from `api.tuetue.vn`
- It should not directly own core billing/quota/model logic

---

### 2.2 `control.tuetue.vn`
**Role:** Admin / operator dashboard

Primary purpose:
- Internal operations console
- System monitoring and control plane UI
- Model/provider/Ollama/core management surface

Planned functions:
- Usage dashboard
- Billing dashboard
- Quota monitoring
- System health overview
- Provider/model health and warm-up status
- Control actions for model/provider/core behavior
- Admin tools for debugging, failover, and operational visibility

Design rule:
- `control.tuetue.vn` should be an admin UI, not the place where core business logic lives
- It should consume APIs from `api.tuetue.vn`
- It should not duplicate backend logic

---

### 2.3 `api.tuetue.vn`
**Role:** Backend core / control plane / service API

Primary purpose:
- FastAPI backend
- Chat API
- Usage metering
- Quota enforcement
- Billing logic
- Admin APIs
- Future auth / tenant / API key / subscription logic

Current and planned functions:
- `/api/chat`
- Usage metering and event ledger
- Billing summary and quota status APIs
- Admin usage / quota / billing endpoints
- Future auth/session management
- Future tenant management
- Future subscription/package APIs
- Future provider/model control APIs

Design rule:
- `api.tuetue.vn` is the real backend system
- This is where business rules, quota, billing, orchestration, and admin control APIs should live

---

## 3. TTAi Super Model Hybrid

### Definition
**TTAi Super Model Hybrid** is the main core intelligence layer of the whole system.

It is responsible for:
- Query classification
- Model/provider routing
- Hybrid inference strategy
- Fallback logic
- Local + remote AI coordination
- Future memory/RAG/core-brain behavior

### Long-term vision
This layer is not just a temporary backend.
It is intended to become the evolving core brain of Tuệ Tuệ:
- Own orchestration logic
- Own memory strategy
- Own routing intelligence
- Eventually, its own model/core identity and intelligence stack

### Current technical identity
Today it already includes:
- FastAPI runtime
- Load balancing
- Query classification
- Ollama integration
- CLI proxy fallback
- Usage metering
- Billing/quota foundations

---

## 4. WordPress Positioning

### WordPress should remain responsible for:
- Public website
- Landing pages
- Content
- Documentation (light/public)
- Marketing pages
- Basic public-facing information

### WordPress should NOT become the home of:
- Core quota logic
- Billing logic
- Tenant management logic
- API key logic
- Admin/control-plane backend logic
- Core inference/orchestration logic

### Decision
WordPress stays in the public/content layer.
Core application/backend logic stays in FastAPI / TTAi backend.

---

## 5. Architecture Principles

### 5.1 Surface separation
Keep these layers separate:
- Product UI (`chat.*`)
- Control/Admin UI (`control.*`)
- Backend/Core (`api.*`)

### 5.2 UI calls API
- `chat.tuetue.vn` calls `api.tuetue.vn`
- `control.tuetue.vn` calls `api.tuetue.vn`
- Backend logic remains centralized in API/core services

### 5.3 Do not collapse backend logic into CMS
Even if WordPress is used for presentation, CMS should not own the backend control plane.

### 5.4 Build backend-first
The project should continue in this order:
1. Stabilize backend core
2. Build admin/control console
3. Build user/product surface

---

## 6. Current Backend Progress

### Completed foundations
- Usage metering schema
- Admin read APIs
- Cost estimation v1
- Billing flags v1
- Tenant/API-key aware billing v2
- Billing-aware admin filters
- Billing summary dashboard v1
- Persisted billing config v3
- Quota enforcement v1
- Admin quota status endpoints
- Live verification on FastAPI 8000

### Important related commits
- `d4ffee7` - Add usage billing flags v1
- `dfbcc2b` - Add tenant and API key billing rules v2
- `14df3b2` - Add billing-aware usage admin filters
- `2727dc3` - Add billing summary dashboard v1
- `8d55759` - Add persisted billing config v3 with admin endpoints
- `f8d22a4` - Add quota enforcement v1 and fix NSSM helper
- `6614757` - Add admin quota status endpoints

---

## 7. Recommended Execution Roadmap

## Phase A — Stabilize `api.tuetue.vn`
Goal: Make backend/core admin foundation solid and consistent.

Tasks:
1. Deploy latest quota/admin foundation to live backend
2. Verify live endpoints for quota status, billing summary, and admin usage
3. Standardize route naming / namespaces (`/api/v1/...`)
4. Improve admin auth boundaries
5. Continue provider/model/system control APIs

---

## Phase B — Build `control.tuetue.vn` MVP
Goal: Create a real admin/operator console on top of backend APIs.

Recommended MVP tabs:
1. **Overview**
   - request totals
   - health
   - cost overview
   - billable vs non-billable

2. **Quota**
   - current usage
   - remaining quota
   - blocked keys/tenants

3. **Billing**
   - billing summary
   - per tenant
   - per API key

4. **Models**
   - providers
   - warm status
   - fallback usage
   - model health

5. **System**
   - service health
   - control operations
   - operational diagnostics

---

## Phase C — Build `chat.tuetue.vn` Product Surface
Goal: Turn the chat UI into a real product experience.

Recommended milestones:
1. Chat experience MVP
2. User login/auth
3. Plans / packages / subscriptions
4. User usage dashboard
5. User billing pages
6. Tenant/user self-service controls

---

## Phase D — Evolve Toward a Real Core Brain
Goal: Push TTAi Super Model Hybrid toward a stronger independent intelligence layer.

Potential directions:
- Better routing and orchestration
- Memory/RAG evolution
- Persistent learning architecture
- Model specialization
- Custom model/core development
- Stronger system identity for Tuệ Tuệ

---

## 8. Execution Checklist

### Immediate checklist
- [ ] Deploy latest quota + admin foundation to live `api.tuetue.vn`
- [ ] Verify live quota status endpoints
- [ ] Verify live billing summary endpoints
- [ ] Standardize backend route namespaces
- [ ] Define admin auth / RBAC plan
- [ ] Draft `control.tuetue.vn` MVP layout and tabs
- [ ] Identify required APIs for Control MVP
- [ ] Plan `chat.tuetue.vn` auth + plans + subscription phase

### Medium-term checklist
- [ ] Move billing/quota config from file-based config toward DB-backed storage
- [ ] Add audit logs for admin changes
- [ ] Add provider/model control actions through API
- [ ] Add safer write APIs for billing/quota config management
- [ ] Add customer/user-facing usage endpoints

---

## 9. Final Guiding Statement

**TTAi API Model** is the full system architecture around Tuệ Tuệ's product surface, control surface, and backend intelligence.

**TTAi Super Model Hybrid** is the core backend intelligence layer — the seed of Tuệ Tuệ's future model/core brain.

The correct long-term shape is:
- `chat.tuetue.vn` = product
- `control.tuetue.vn` = admin/ops console
- `api.tuetue.vn` = backend/control plane
- WordPress = public site/content/docs/marketing
