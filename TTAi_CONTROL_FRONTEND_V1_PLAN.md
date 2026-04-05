# TTAi Control Frontend v1 Plan

_Last updated: 2026-04-05_

## 1. Decision

`control.tuetue.vn` will be built as a **dedicated frontend**.

It is no longer treated as a WordPress-admin-centric experience.
WordPress may remain as a supporting/admin-side integration point if needed, but it is not the main control surface.

### Final architectural stance
- `api.tuetue.vn` = backend / control plane / source of truth
- `control.tuetue.vn` = dedicated frontend / operator dashboard
- WordPress admin = secondary/supporting only

---

## 2. Frontend vision

Control v1 should feel like a real operator console:
- dark theme
- clean and modern
- metric-first
- fast to scan
- useful before it is fancy

This is not a marketing site.
This is not a CMS dashboard.
This is an operator surface for visibility and decision-making.

---

## 3. Scope for v1

## Phase 1 pages / modules
The first meaningful frontend should prioritize these modules:
1. **Overview**
2. **Quota**
3. **Billing**
4. **Errors**

## Deferred to later frontend phases
- Models
- System
- Usage deep drilldowns
- write actions
- config editors
- advanced charts

Reason:
- backend support is already strongest for Overview/Quota/Billing/Errors
- these modules deliver the most immediate operator value
- they are read-heavy and lower risk

---

## 4. Data source policy

All control frontend data should come from FastAPI admin endpoints.

### Main v1 endpoints
- `/api/v1/admin/overview`
- `/api/v1/admin/quota/blocked`
- `/api/v1/admin/quota/status`
- `/api/v1/admin/usage/billing-summary`
- `/api/v1/admin/errors/summary`

### Supporting endpoints
- `/api/v1/admin/usage/events`
- `/api/v1/admin/usage/summary`
- `/api/v1/system/health`
- `/api/v1/system/health/detailed`

---

## 5. Frontend architecture recommendation

## Recommended implementation shape
### A lightweight dedicated dashboard app

Possible implementation styles:
- static HTML/CSS/JS app with fetch layer
- lightweight React app
- lightweight Vue app

### Recommendation for current phase
Use the **lightest clean implementation that supports maintainable components**.

Priority is:
- fast build
- easy deployment
- clean file structure
- easy iteration

Not priority:
- big framework complexity too early
- overengineering routing/state management

---

## 6. Auth model for control frontend

This must be handled carefully.

### Hard rule
Do not expose production admin token directly in public frontend code.

### Near-term acceptable options
1. **same-origin backend proxy** for control frontend requests
2. **server-injected secure session model**
3. **temporary protected deployment behind admin-only access + proxy layer**

### Recommendation
For the first real control frontend build, design it assuming:
- frontend should not hardcode bearer token
- backend/proxy/session handling will be the eventual safe path

During local/internal development, temporary token-based testing can happen, but it is not the final architecture.

---

## 7. Layout plan

## Global layout
- left sidebar navigation
- top header bar
- main content area with cards + tables + status blocks

### Sidebar items for v1
- Overview
- Quota
- Billing
- Errors

### Later sidebar items
- Models
- System
- Usage
- Settings

---

## 8. Page design plan

## Overview page
### Goal
Fast status check of the whole system.

### Sections
- health KPI cards
- usage KPI cards
- billable cost snapshot
- blocked quota snapshot
- recent error highlights

### Main data source
- `/api/v1/admin/overview`

### Suggested widgets
- Health status
- Window events
- Billable cost
- Blocked event count
- Top provider
- Top quota issue
- Recent errors list

---

## Quota page
### Goal
Monitor who is getting blocked and why.

### Sections
- blocked quota summary cards
- breakdown tables (tenant / API key / user / reason)
- quota lookup form
- recent blocked events table

### Main data sources
- `/api/v1/admin/quota/blocked`
- `/api/v1/admin/quota/status`

---

## Billing page
### Goal
See estimated cost and billable activity quickly.

### Sections
- total estimated cost
- billable vs non-billable
- tenant breakdown
- API key breakdown
- provider breakdown

### Main data source
- `/api/v1/admin/usage/billing-summary`

---

## Errors page
### Goal
See operational issues without digging through raw logs.

### Sections
- error count cards
- breakdown by status / HTTP status / provider / model
- top error signatures
- recent errors table

### Main data source
- `/api/v1/admin/errors/summary`

---

## 9. Component map

### Shared components
- `Sidebar`
- `TopBar`
- `PageHeader`
- `KpiCard`
- `SummaryPanel`
- `BreakdownList`
- `DataTable`
- `StatusBadge`
- `EmptyState`
- `ErrorState`
- `LoadingState`

### Page-specific components
#### Overview
- `OverviewHealthCards`
- `OverviewRecentErrors`
- `OverviewBillingSnapshot`
- `OverviewQuotaSnapshot`

#### Quota
- `QuotaBlockedCards`
- `QuotaBreakdownTable`
- `QuotaLookupForm`
- `QuotaRecentBlockedTable`

#### Billing
- `BillingCostCards`
- `BillingBreakdownTable`
- `BillingProviderBreakdown`

#### Errors
- `ErrorBreakdownCards`
- `ErrorSignatureList`
- `RecentErrorsTable`

---

## 10. API-to-UI mapping

## Overview
- Health status → `overview.health.summary.status`
- Window events → `overview.usage.window_event_count`
- Billable cost → `overview.billing.summary.billable_estimated_cost`
- Blocked events → `overview.quota.blocked_event_count`
- Recent errors → `overview.alerts.recent_errors`

## Quota
- Blocked event count → `quota.blocked_event_count`
- Breakdown tables → `tenant_breakdown`, `api_key_breakdown`, `user_breakdown`, `reason_breakdown`
- Recent blocked → `recent_blocked`
- Lookup detail → `/api/v1/admin/quota/status`

## Billing
- KPI cards → `summary.total_estimated_cost`, `billable_estimated_cost`, `non_billable_estimated_cost`
- breakdowns → `tenant_breakdown`, `api_key_breakdown`, `provider_breakdown`, `billable_mode_breakdown`

## Errors
- error count → `error_event_count`
- breakdowns → `status_breakdown`, `http_status_breakdown`, `provider_breakdown`, `model_breakdown`
- signature list → `top_error_signatures`
- recent errors → `recent_errors`

---

## 11. UX guidelines

### Visual style
- dark background
- strong contrast
- restrained color palette
- blue/purple accents acceptable
- red/yellow only for alert semantics

### Information density
- medium-high density
- should feel like an operator console, not a marketing page

### Interaction style
- minimal clicks
- clear filters
- easy scanning
- no noisy animation

---

## 12. Risk control rules

- do not make frontend depend on legacy WordPress plugin decisions
- do not block control progress on WordPress admin work
- do not require risky write actions for v1 usefulness
- do not overbuild state management before pages are proven
- do not leak admin secrets into public client code

---

## 13. Suggested implementation order

## Step 1
Create frontend shell:
- sidebar
- topbar
- route/page skeleton
- dark theme base

## Step 2
Implement Overview page fully
- this becomes the first visible real control dashboard page

## Step 3
Implement Quota page

## Step 4
Implement Billing page

## Step 5
Implement Errors page

## Step 6
Refine loading/error states and navigation

## Step 7
Then expand toward Models / System / Usage

---

## 14. Definition of success for v1

Control Frontend v1 is successful when:
- `control.tuetue.vn` clearly behaves as the main control surface
- operator can understand system state from Overview alone
- quota/billing/error visibility is available without digging through raw JSON
- the frontend depends cleanly on `api.tuetue.vn`
- the architecture remains clean enough to extend later

---

## 15. Final statement

The right next move is not to beautify WordPress admin.

The right next move is to build a dedicated `control.tuetue.vn` frontend that:
- treats `api.tuetue.vn` as the backend truth
- starts with Overview + Quota + Billing + Errors
- uses a dark operator-dashboard style
- stays simple, structured, and extensible
