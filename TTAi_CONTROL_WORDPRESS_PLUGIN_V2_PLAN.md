# TTAi Control WordPress Plugin v2 Plan

_Last updated: 2026-04-05_

## 1. Purpose

This document defines the correct next architecture for `control.tuetue.vn` using the existing WordPress admin plugin approach, but upgraded into a cleaner and safer **Control Plugin v2**.

The goal is to build the control dashboard in a way that is:
- secure enough for current production phase
- aligned with existing backend/API foundations
- maintainable and extensible
- less hacky than quick demo-style UI injection

This plan explicitly avoids the "show it immediately no matter what" approach.

---

## 2. Architectural decision

## Chosen direction
### `control.tuetue.vn` = WordPress admin plugin v2 + FastAPI admin backend

That means:
- WordPress remains the admin shell / page host for now
- FastAPI remains the control-plane backend and source of truth
- the plugin fetches data from FastAPI admin endpoints
- the browser should not hold raw admin bearer tokens directly in public JS

---

## 3. What v2 is NOT

Control Plugin v2 is **not**:
- a front-end hack that hardcodes admin token in browser JS
- a one-off dashboard patch just to display cards fast
- a collector-only dashboard pretending to be the full control plane
- a full standalone SPA rewrite at this stage

---

## 4. Core design principles

### 4.1 Backend remains the source of truth
All real operational/business/control data should come from FastAPI:
- `/api/v1/admin/overview`
- `/api/v1/admin/usage/*`
- `/api/v1/admin/usage/billing-summary`
- `/api/v1/admin/quota/*`
- `/api/v1/admin/errors/summary`
- `/api/v1/models/*`
- `/api/v1/system/*`

### 4.2 Token stays server-side
Admin token should be stored in plugin settings / server config and used only in server-side requests.

### 4.3 UI is read-heavy first
The first real plugin v2 should focus on:
- read-only visibility
- stable rendering
- minimal risk to the live backend

### 4.4 Write actions come later
High-risk actions must be deferred until:
- clearer UX confirmation exists
- audit/logging strategy exists
- RBAC direction is clearer

---

## 5. Security model for plugin v2

## Server-side fetch model
### Plugin PHP should:
- store `api_base_url`
- store `admin_token`
- call FastAPI with `wp_remote_get()` / `wp_remote_post()`
- render the data server-side or expose sanitized AJAX endpoints via WordPress admin

## Browser should NOT:
- know the raw `TTAI_ADMIN_TOKEN`
- call protected FastAPI endpoints directly with secret bearer token

## Minimum acceptable v2 security
- WordPress admin capability check: `manage_options`
- plugin settings stored server-side
- FastAPI admin token used only server-side
- no hardcoded production admin token in public JS

---

## 6. Current live assets that must be protected

The v2 work must preserve these already-working pieces:
- FastAPI 8000 runtime
- CLI proxy integration
- usage metering
- billing summary
- quota enforcement
- quota status endpoints
- admin token validation v1
- canonical `/api/v1/...` namespaces

### Critical environment values that must not be broken
- `CLI_PROXY_API_KEY`
- `TTAI_ADMIN_TOKEN`

### Critical route safety rules
- do not remove legacy routes yet
- do not destabilize `/api/chat`
- test new backend logic on temp ports before production

---

## 7. Plugin v2 information architecture

## Tab 1 — Overview
### Goal
Top-level operator snapshot.

### Data sources
- `/api/v1/admin/overview`

### Contents
- system health cards
- usage window event count
- billable estimated cost
- blocked quota count
- recent errors highlights

### Risk
- read-only / safe

---

## Tab 2 — Usage
### Goal
Inspect recent request activity and usage drilldowns.

### Data sources
- `/api/v1/admin/usage/events`
- `/api/v1/admin/usage/summary`
- `/api/v1/admin/usage/users/{target_user_id}`

### Contents
- event table
- filters
- top users/providers/models
- user drilldown

### Risk
- read-only / safe

---

## Tab 3 — Billing
### Goal
Operator visibility into estimated cost and billable activity.

### Data sources
- `/api/v1/admin/usage/billing-summary`
- `/api/v1/admin/billing/config` (read-only in early phase)

### Contents
- total estimated cost
- billable vs non-billable
- tenant breakdown
- API key breakdown
- provider breakdown
- billing config viewer

### Risk
- mostly read-only in v2 phase 1

---

## Tab 4 — Quota
### Goal
Monitor quota state and blocked traffic.

### Data sources
- `/api/v1/admin/quota/status`
- `/api/v1/admin/quota/status/users/{target_user_id}`
- `/api/v1/admin/quota/blocked`

### Contents
- lookup by tenant/api key/user
- remaining quota details
- blocked entities summary
- recent blocked events

### Risk
- read-only / safe

---

## Tab 5 — Models
### Goal
Inspect provider/model/runtime readiness.

### Data sources
- `/api/v1/models/status`
- `/api/v1/models/status/{model_name}`
- `/api/v1/system/loadbalancer/metrics`
- `/api/v1/system/loadbalancer/providers`
- `/api/v1/ollama/health`
- `/api/v1/ollama/models`

### Contents
- model status table
- provider health
- load balancer metrics
- Ollama availability

### Risk
- read-only / safe

---

## Tab 6 — System
### Goal
Platform health and operator diagnostics.

### Data sources
- `/api/v1/system/health`
- `/api/v1/system/health/detailed`
- optional legacy collector proxy data if still useful

### Contents
- service health
- detailed runtime health
- supporting diagnostics

### Risk
- read-only in initial v2

---

## 8. Plugin v2 implementation pattern

## Option A — server-rendered tabs (recommended first)
Each WP admin tab loads data server-side in PHP and renders HTML.

### Benefits
- simplest security model
- token never leaves server
- easiest to reason about
- easiest to debug in current setup

### Tradeoff
- less dynamic than SPA-style interactions

## Option B — WordPress admin AJAX proxy (phase 2 if needed)
Browser calls WordPress AJAX actions, and WP calls FastAPI server-side.

### Benefits
- more dynamic UI
- still avoids exposing FastAPI admin token

### Tradeoff
- more moving parts than server-rendered MVP

## Recommendation
Start with **Option A** for plugin v2 phase 1.

---

## 9. Plugin v2 settings model

### Required settings
- `collector_url` (legacy/optional)
- `collector_token` (legacy/optional)
- `api_base_url`
- `admin_token`

### Suggested defaults
- `collector_url = http://localhost:8090`
- `api_base_url = http://127.0.0.1:8000`

### Notes
- `collector_*` should become secondary over time
- `api_*` should become the main configuration path

---

## 10. Migration strategy from current plugin

## Current state
The existing plugin is a small collector-focused page.
It is not yet a real control-plane dashboard.

## v2 migration rule
Do not destroy the current page abruptly.
Instead:
1. keep current plugin entry point
2. refactor internal rendering into tab-based sections
3. move collector widgets into a legacy/supporting section
4. make FastAPI-backed dashboard sections primary

### Transition preference
- same plugin slug if possible
- cleaner internal structure
- same admin menu entry

---

## 11. What should be deferred

These should NOT be phase-1 plugin v2 goals:
- provider enable/disable buttons
- model warmup buttons
- billing config editor UX
- quota policy editor UX
- failover/restart actions
- complex charts before the data model is normalized

These can come after the read-only dashboard is stable.

---

## 12. Implementation order

## Phase 1 — plugin architecture cleanup
- refactor plugin settings model
- add FastAPI server-side fetch helper
- separate collector helper vs API helper
- create tabbed page skeleton

## Phase 2 — Overview tab
- use `/api/v1/admin/overview`
- render cards and basic highlights

## Phase 3 — Usage / Billing / Quota tabs
- connect read-only drilldowns
- simple filters where useful

## Phase 4 — Models / System tabs
- render model/provider/health data
- keep write actions hidden/deferred

## Phase 5 — auth/UX hardening
- improve error handling
- better empty states
- better secret handling guidance
- possibly move token storage to safer config if needed

## Phase 6 — selective write actions
- only after confirm UX + audit plan

---

## 13. Non-negotiable guardrails

- do not hardcode production admin token in browser JS
- do not break `/api/chat`
- do not overwrite service env carelessly
- do not remove legacy routes yet
- do not ship risky write actions before read-only dashboard is stable
- do not treat collector-only widgets as the full control plane

---

## 14. Final statement

The correct near-term implementation for `control.tuetue.vn` is:

### WordPress admin plugin v2
with:
- server-side FastAPI admin API integration
- tab-based control UI
- read-only first rollout
- admin token kept server-side
- existing live backend preserved and reused

This gives Tuệ Văn a control dashboard that is:
- correct for the current architecture
- fast enough to build now
- much safer than a rushed frontend hack
- extensible toward a fuller control plane later
