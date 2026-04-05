# TTAi API PROVISIONING, BILLING, AND ADMIN PLAN

## 1. Purpose

This document defines the product/business control layer required for TTAi to move from a technically working AI system into a commercially operable platform.

It focuses on:
- API provisioning
- user and tenant control
- quota / token usage tracking
- billing / payment / invoice foundations
- admin and support operations
- phased implementation planning

This is intentionally separate from the system ops dashboard.

---

## 2. Important Distinction

## 2.1 System Control Dashboard
Current dashboard work is primarily about:
- service health
- topology
- provider scores
- workloads
- queue / RAG / load balancer visibility
- alerts for operations

This is an **operations dashboard**.

## 2.2 Business / Admin Control Plane
What is still needed is a separate product/business layer for:
- account management
- API customer onboarding
- plan assignment
- API key issuance
- token metering
- usage reports
- invoicing / billing / payment tracking
- admin support actions

This document is about that second layer.

---

## 3. What Already Exists

## 3.1 Technical foundations already available
The project already has strong foundations that can support this next layer:

### A. Identity / access direction
- JWT-based auth has been referenced in current implementation notes
- `is_admin` path already exists conceptually and in admin route flow
- portal has login path and protected admin access direction

### B. Stable infrastructure layer
- FastAPI exists as the core service layer
- WordPress portal exists as user-facing entry point
- production DB stack exists
- Docker-based production operations are working
- control dashboard services exist

### C. Operational metrics/logging already exist
The system already logs data that can later support billing/usage models:
- provider metrics
- load balancer logs
- RAG stats
- workload queue state
- system health

### D. Product thinking already exists
The intended flow has been described clearly:
- free chat users
- registered users
- API customers / organizations
- admin / operator hierarchy

This means the conceptual model is already present.

---

## 4. What Does Not Yet Exist (or is not yet confirmed as implemented)

These areas should be treated as not-yet-complete product workstreams:

## 4.1 API provisioning lifecycle
Missing or not yet validated:
- API key creation flow
- API key revoke / rotate / expire flow
- model access scope per key
- environment separation (test / prod keys)
- key ownership mapping to tenant/account

## 4.2 Metering engine
Missing or not yet validated:
- request-level usage tracking per user/key
- input token and output token tracking
- provider/model-level usage attribution
- cost estimation per request
- daily/monthly usage rollups

## 4.3 Billing system
Missing or not yet validated:
- subscription plans
- package/credit system
- invoice records
- billing ledger
- overage charging rules
- billing periods / statements

## 4.4 Payments
Missing or not yet validated:
- payment method storage strategy
- payment gateway integration
- payment success/failure state machine
- refund / adjustment handling

## 4.5 Customer control panel
Missing or not yet validated:
- self-service API key management
- usage dashboard per customer
- quota visibility
- billing history
- invoice download
- team / organization controls

## 4.6 Admin business panel
Missing or not yet validated:
- tenant/customer list
- plan assignment UI
- usage anomaly controls
- manual billing adjustment tools
- admin support actions
- revenue vs provider cost reporting

---

## 5. Product Actors and Flows

## 5.1 Actor A — Free End User
Characteristics:
- uses chat UI without full paid account
- limited requests / session / token budget
- entry-level product experience

Needs:
- temporary identity/session
- anti-abuse controls
- usage cap
- optional upgrade path

## 5.2 Actor B — Registered Chat User
Characteristics:
- signs in via Apple / Google / email path
- can have persistent preferences and usage history
- may later upgrade to paid or API usage

Needs:
- user profile
- auth identity
- usage tracking
- plan status
- saved sessions/history if desired

## 5.3 Actor C — API Customer / Tenant
Characteristics:
- individual or organization consuming API directly
- needs machine credentials and reporting

Needs:
- tenant/account
- API keys
- quotas / packages / credits
- usage reports
- invoices / payment records
- control panel

## 5.4 Actor D — Admin / Operator / Support
Characteristics:
- internal business/operator role
- different from system-level ops dashboard

Needs:
- user/tenant lookup
- plan assignment / suspension
- API key overrides
- usage and anomaly review
- invoice / payment support tools
- limited support impersonation or investigation tools

---

## 6. Recommended System Modules

## 6.1 Identity and Tenant Module
Responsibilities:
- users
- organizations / tenants
- roles and memberships
- auth provider bindings (Google, Apple, email)

Core entities:
- User
- Tenant
- TenantMember
- Role
- AuthIdentity

## 6.2 API Provisioning Module
Responsibilities:
- create and rotate keys
- assign scopes and models
- enforce active/revoked state
- support environment separation

Core entities:
- ApiKey
- ApiKeyScope
- ApiCredentialEvent

## 6.3 Usage Metering Module
Responsibilities:
- log request usage
- estimate cost and token counts
- aggregate usage by period
- support both chat and direct API usage

Core entities:
- UsageEvent
- UsageAggregateDaily
- UsageAggregateMonthly
- ProviderCostEvent

## 6.4 Billing Module
Responsibilities:
- plans
- pricing
- quotas
- overages
- invoicing
- billing period closeout

Core entities:
- Plan
- PlanFeature
- Subscription
- BillingCycle
- Invoice
- InvoiceLine
- CreditBalance
- OverageRule

## 6.5 Payment Module
Responsibilities:
- payment provider integration
- payment intent / receipt state
- reconcile invoices and payments

Core entities:
- PaymentMethod
- PaymentTransaction
- PaymentAttempt
- Refund

## 6.6 Admin Business Control Module
Responsibilities:
- admin view over tenants/customers
- usage + financial summary
- support actions
- overrides and audit

Core entities:
- AdminAuditLog
- SupportAction
- ManualAdjustment
- CustomerRiskFlag

---

## 7. Suggested Data Model (High-Level)

## 7.1 Identity / tenant tables
- `users`
- `auth_identities`
- `tenants`
- `tenant_members`
- `roles`

## 7.2 API access tables
- `api_keys`
- `api_key_scopes`
- `api_key_events`

## 7.3 Usage tables
- `usage_events`
- `usage_daily`
- `usage_monthly`
- `provider_cost_events`

## 7.4 Billing tables
- `plans`
- `subscriptions`
- `billing_cycles`
- `invoices`
- `invoice_lines`
- `credit_balances`
- `manual_adjustments`

## 7.5 Payment tables
- `payment_methods`
- `payment_transactions`
- `refunds`

## 7.6 Admin/support tables
- `admin_audit_logs`
- `support_actions`
- `risk_flags`

---

## 8. Minimum Event Model for Usage Metering

Every paid/API-relevant request should eventually produce a usage event roughly containing:
- event_id
- timestamp
- tenant_id
- user_id (nullable)
- api_key_id (nullable)
- channel (`portal_chat`, `api`, `wordpress_chat`, etc.)
- request_type
- model/provider selected
- input_tokens
- output_tokens
- total_tokens
- latency_ms
- status (`success`, `error`, `timeout`, `fallback`)
- estimated_cost
- request_id / trace_id

This event model is critical because:
- billing depends on it
- admin investigation depends on it
- product analytics depends on it
- abuse/risk detection depends on it

---

## 9. Suggested UX Surfaces

## 9.1 End-user portal surfaces
- login / signup
- chat usage badge / quota notice
- upgrade CTA
- account page

## 9.2 API customer panel
- dashboard summary
- current plan
- key management
- usage charts
- invoices and payment history
- quota / token consumption view

## 9.3 Admin business panel
- customer list
- active subscriptions
- current high-usage tenants
- failed payments / overdue invoices
- support tools
- key revocation / quota override actions

## 9.4 System ops dashboard (existing track)
Should remain separate from business dashboard but may be linked from admin navigation.

---

## 10. Recommended Architecture Separation

Do **not** try to force all concerns into the current control dashboard collector.

Recommended separation:

### A. System Control Dashboard
Purpose:
- topology, health, provider status, workloads, alerts

### B. Business/Admin Control Plane
Purpose:
- users, tenants, API keys, quotas, usage, invoices, payments, support

### C. Shared foundational data
Possible shared areas:
- auth
- request logging
- trace IDs
- provider usage events

This keeps ops concerns and business concerns cleanly separated.

---

## 11. Implementation Phases

## Phase 0 — Discovery and design (Immediate)
Deliverables:
- this planning document
- clarified scope boundaries
- core entity map
- implementation phases

## Phase 1 — Metering foundation (Highest priority)
Goal:
Before charging anyone, the system must measure usage reliably.

Deliverables:
- usage event schema
- request tracing IDs
- token counting / estimate pipeline
- provider/model attribution
- daily/monthly aggregation

Success criteria:
- every paid/API request can be measured consistently
- admin can inspect usage by user/key/tenant

## Phase 2 — API key provisioning
Goal:
Enable direct API customers in a controlled way.

Deliverables:
- create/revoke/rotate API keys
- assign scopes and plans
- enforce quotas and rate limits
- admin key management surface

Success criteria:
- tenants can receive credentials
- system can identify traffic by key and tenant

## Phase 3 — Plan / quota / billing core
Goal:
Add product controls without yet requiring full payment automation.

Deliverables:
- plan catalog
- subscriptions
- quota enforcement
- usage summary pages
- invoice records (even if manually settled first)

Success criteria:
- each tenant is mapped to a plan
- usage and overage can be computed
- invoices can be produced internally

## Phase 4 — Payment integration
Goal:
Move from internal accounting to real commercial operation.

Deliverables:
- payment provider integration
- payment methods
- paid invoice lifecycle
- payment failure handling

Success criteria:
- subscription can be paid and reconciled automatically

## Phase 5 — Admin/support maturity
Goal:
Provide full internal business control.

Deliverables:
- support actions
- overrides
- suspension controls
- revenue/cost reporting
- dispute / refund / adjustment tooling

Success criteria:
- admin/support can operate the business safely

---

## 12. Recommended Immediate Execution Plan

## Step 1 — Formalize data model
Create a schema/planning file next that defines:
- core tables/entities
- relationships
- minimum fields
- audit requirements

## Step 2 — Instrument usage tracking in FastAPI
Before UI work, add backend event generation for:
- user/chat/API requests
- provider/model chosen
- token estimate
- latency
- success/failure

## Step 3 — Define plan model
Start simple:
- free
- registered basic
- API starter
- API business

Each with:
- request limits
- token limits
- model access scopes
- support level

## Step 4 — Build admin-first visibility
Before customer self-service, build internal admin visibility for:
- usage by tenant/user
- top active keys
- quota breaches
- failed requests
- estimated cost

## Step 5 — Add self-service API provisioning
After internal controls are stable, expose controlled customer-facing key management.

---

## 13. Risks to Avoid

- mixing system-ops dashboard with business billing dashboard into one confusing subsystem
- charging before usage metering is trustworthy
- issuing API keys before tenant ownership/audit is clear
- building payment first before usage/accounting foundations are correct
- creating too many ad-hoc data stores without a traceable canonical ledger

---

## 14. Documentation Discipline Rules

To avoid losing time again, this workstream should follow strict documentation rules:

1. Every phase must have a named doc/file.
2. Every implemented module must record:
   - file path
   - owner purpose
   - endpoints added
   - env vars added
   - DB tables added
3. Every progress update must separate:
   - implemented
   - partial
   - planned
4. Never describe a business subsystem as complete unless the full flow is testable end-to-end.
5. Maintain one canonical progress review for this workstream.

---

## 15. Current Assessment of This Workstream

### Current maturity
- **API provisioning + billing + admin business layer:** ~20–35%

### Reason
Strong platform foundations exist, but the actual commercial control-plane modules are still mostly design-stage or partial groundwork.

---

## 16. Next Recommended Files

After this document, the next most useful files to create are:
1. `TTAi_API_BILLING_DATA_MODEL.md`
2. `TTAi_USAGE_METERING_IMPLEMENTATION_PLAN.md`
3. `TTAi_ADMIN_BUSINESS_DASHBOARD_SCOPE.md`
4. `TTAi_API_PROVISIONING_EXECUTION_CHECKLIST.md`

---

## 17. Immediate Next Action

The next implementation step should be:
- define the data model and minimum entities first
- then instrument FastAPI usage events
- then expose admin internal visibility
- then move toward customer-facing provisioning and billing
