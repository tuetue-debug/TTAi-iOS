# TTAi API BILLING DATA MODEL

## 1. Purpose

This document defines the minimum viable data model for:
- API provisioning
- usage metering
- quota enforcement
- billing
- payment tracking
- admin/support operations

It is designed to be implementation-oriented.
The goal is to reduce ambiguity before backend coding begins.

---

## 2. Design Principles

1. **One canonical ledger for usage**
   - Every chargeable or quota-relevant request must produce a usage event.

2. **Tenant-first model**
   - Billing and API provisioning should attach primarily to a tenant/account, not just an individual user.

3. **Separate identity from billing**
   - Users/auth identities should be independent from plans, invoices, and payment records.

4. **Audit everything important**
   - Key creation, rotation, plan changes, manual adjustments, refunds, suspensions, and admin actions should all be logged.

5. **Support phased rollout**
   - Data model should support starting simple (manual billing) and evolving later to full payment automation.

---

## 3. Entity Overview

The recommended data model is organized into 7 groups:

1. Identity and tenant
2. API credentials and access control
3. Usage metering
4. Plans and subscriptions
5. Billing and invoicing
6. Payments and credits
7. Admin / support / audit

---

## 4. Identity and Tenant Layer

## 4.1 `users`
Purpose:
- Represents a human account in the system.

Minimum fields:
- `id` (uuid, pk)
- `email` (string, unique, nullable for some auth flows)
- `display_name` (string)
- `status` (enum: active, suspended, invited, deleted)
- `is_admin` (bool)
- `created_at`
- `updated_at`
- `last_login_at` (nullable)

Notes:
- A user can belong to one or more tenants.
- A user may be both customer-side and admin-side depending on role.

## 4.2 `auth_identities`
Purpose:
- Stores external login provider bindings.

Minimum fields:
- `id` (uuid, pk)
- `user_id` (fk -> users.id)
- `provider` (enum: google, apple, email, other)
- `provider_subject` (string)
- `email` (string, nullable)
- `created_at`
- `updated_at`

Notes:
- A user may have multiple auth identities.

## 4.3 `tenants`
Purpose:
- Represents a billable account/customer entity.
- Can be an individual customer or an organization.

Minimum fields:
- `id` (uuid, pk)
- `name` (string)
- `slug` (string, unique)
- `tenant_type` (enum: individual, organization)
- `status` (enum: active, suspended, trial, closed)
- `owner_user_id` (fk -> users.id)
- `billing_email` (string, nullable)
- `country_code` (string, nullable)
- `currency` (string, default `USD` or local chosen base)
- `created_at`
- `updated_at`

## 4.4 `tenant_members`
Purpose:
- Maps users to tenants with roles.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `user_id` (fk -> users.id)
- `role` (enum: owner, admin, developer, billing, viewer, support)
- `status` (enum: active, invited, removed)
- `created_at`
- `updated_at`

---

## 5. API Credentials and Access Control

## 5.1 `api_keys`
Purpose:
- Stores machine credentials for API customers.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `label` (string)
- `public_key_id` (string, unique)
- `secret_hash` (string)
- `status` (enum: active, revoked, expired, disabled)
- `environment` (enum: test, production)
- `created_by_user_id` (fk -> users.id, nullable)
- `created_at`
- `last_used_at` (nullable)
- `revoked_at` (nullable)
- `expires_at` (nullable)

Notes:
- Never store raw secret after creation; only hashed secret.
- `public_key_id` is safe to show in UI.

## 5.2 `api_key_scopes`
Purpose:
- Defines what an API key is allowed to do.

Minimum fields:
- `id` (uuid, pk)
- `api_key_id` (fk -> api_keys.id)
- `scope_type` (enum: model_access, endpoint_access, rate_limit_profile, tenant_capability)
- `scope_value` (string)
- `created_at`

Examples:
- model access to `gemma3:4b`
- model access to premium providers only on business plans
- endpoint access to `/v1/chat` but not admin routes

## 5.3 `api_key_events`
Purpose:
- Audit log of API credential changes.

Minimum fields:
- `id` (uuid, pk)
- `api_key_id` (fk -> api_keys.id)
- `tenant_id` (fk -> tenants.id)
- `event_type` (enum: created, rotated, revoked, reactivated, scope_changed)
- `actor_user_id` (fk -> users.id, nullable)
- `reason` (string, nullable)
- `metadata_json` (json, nullable)
- `created_at`

---

## 6. Usage Metering Layer

## 6.1 `usage_events`
Purpose:
- Canonical ledger of requests for metering, reporting, and later billing.

This is the most important table in the whole billing system.

Minimum fields:
- `id` (uuid, pk)
- `timestamp` (datetime indexed)
- `tenant_id` (fk -> tenants.id, nullable for free-anonymous traffic)
- `user_id` (fk -> users.id, nullable)
- `api_key_id` (fk -> api_keys.id, nullable)
- `channel` (enum: portal_chat, wordpress_chat, api, admin_test, internal)
- `request_id` (string, unique-ish trace id)
- `session_id` (string, nullable)
- `provider` (string)
- `model` (string)
- `routing_path` (string, nullable)  # e.g. local_ollama / remote_ollama / cloud_api
- `input_tokens` (integer, default 0)
- `output_tokens` (integer, default 0)
- `total_tokens` (integer, default 0)
- `latency_ms` (integer, nullable)
- `status` (enum: success, error, timeout, fallback, rejected)
- `http_status` (integer, nullable)
- `estimated_cost` (decimal, nullable)
- `currency` (string, nullable)
- `source_ip` (string, nullable)
- `metadata_json` (json, nullable)
- `created_at`

Notes:
- This table should be append-only except for correction workflows.
- Even if billing is not live yet, this table should exist first.

## 6.2 `usage_daily`
Purpose:
- Daily rollups for fast dashboard reads.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `user_id` (fk -> users.id, nullable)
- `api_key_id` (fk -> api_keys.id, nullable)
- `date` (date)
- `request_count` (integer)
- `input_tokens` (integer)
- `output_tokens` (integer)
- `total_tokens` (integer)
- `success_count` (integer)
- `error_count` (integer)
- `estimated_cost` (decimal)
- `created_at`
- `updated_at`

## 6.3 `usage_monthly`
Purpose:
- Monthly rollups for billing and quota checks.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `year_month` (string, e.g. `2026-04`)
- `request_count`
- `total_tokens`
- `estimated_cost`
- `created_at`
- `updated_at`

## 6.4 `provider_cost_events`
Purpose:
- Internal cost accounting of provider usage.

Minimum fields:
- `id` (uuid, pk)
- `usage_event_id` (fk -> usage_events.id)
- `provider` (string)
- `model` (string)
- `internal_cost_estimate` (decimal)
- `currency` (string)
- `created_at`

Purpose:
- compare cost to revenue later
- support margin reporting

---

## 7. Plans and Subscription Layer

## 7.1 `plans`
Purpose:
- Catalog of commercial offerings.

Minimum fields:
- `id` (uuid, pk)
- `code` (string, unique)
- `name` (string)
- `plan_type` (enum: free, subscription, prepaid, enterprise)
- `status` (enum: active, archived)
- `billing_period` (enum: none, monthly, yearly, prepaid)
- `base_price` (decimal)
- `currency` (string)
- `created_at`
- `updated_at`

## 7.2 `plan_features`
Purpose:
- Store quota and feature limits by plan.

Minimum fields:
- `id` (uuid, pk)
- `plan_id` (fk -> plans.id)
- `feature_key` (string)
- `feature_value` (string)
- `created_at`

Examples:
- `monthly_token_limit=1000000`
- `max_api_keys=5`
- `allowed_model_tier=premium`
- `rate_limit_rpm=60`

## 7.3 `subscriptions`
Purpose:
- Links a tenant to a plan over time.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `plan_id` (fk -> plans.id)
- `status` (enum: active, trialing, paused, cancelled, expired)
- `started_at`
- `current_period_start`
- `current_period_end`
- `trial_ends_at` (nullable)
- `cancelled_at` (nullable)
- `billing_anchor_at` (nullable)
- `created_at`
- `updated_at`

---

## 8. Billing Layer

## 8.1 `billing_cycles`
Purpose:
- Represents a closed/open accounting period for a tenant.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `subscription_id` (fk -> subscriptions.id, nullable)
- `period_start`
- `period_end`
- `status` (enum: open, pending_invoice, invoiced, closed)
- `usage_cost_total` (decimal)
- `fixed_fee_total` (decimal)
- `discount_total` (decimal)
- `tax_total` (decimal)
- `amount_due` (decimal)
- `currency` (string)
- `created_at`
- `updated_at`

## 8.2 `invoices`
Purpose:
- Formal billing records.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `billing_cycle_id` (fk -> billing_cycles.id, nullable)
- `invoice_number` (string, unique)
- `status` (enum: draft, issued, paid, overdue, void, cancelled)
- `currency` (string)
- `subtotal` (decimal)
- `discount_total` (decimal)
- `tax_total` (decimal)
- `total_amount` (decimal)
- `amount_paid` (decimal)
- `amount_due` (decimal)
- `issued_at` (nullable)
- `due_at` (nullable)
- `paid_at` (nullable)
- `created_at`
- `updated_at`

## 8.3 `invoice_lines`
Purpose:
- Line-item breakdown for invoices.

Minimum fields:
- `id` (uuid, pk)
- `invoice_id` (fk -> invoices.id)
- `line_type` (enum: subscription_fee, usage_fee, overage, discount, tax, manual_adjustment)
- `description` (string)
- `quantity` (decimal)
- `unit_price` (decimal)
- `amount` (decimal)
- `metadata_json` (json, nullable)
- `created_at`

## 8.4 `manual_adjustments`
Purpose:
- Admin/support corrections to billing.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `invoice_id` (fk -> invoices.id, nullable)
- `adjustment_type` (enum: credit, debit, waiver, support_adjustment)
- `amount` (decimal)
- `currency` (string)
- `reason` (string)
- `actor_user_id` (fk -> users.id)
- `created_at`

---

## 9. Payments and Credits Layer

## 9.1 `payment_methods`
Purpose:
- Stores references to external payment methods.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `provider` (string)
- `provider_ref` (string)
- `method_type` (enum: card, bank_transfer, wallet, manual)
- `status` (enum: active, inactive, expired)
- `is_default` (bool)
- `created_at`
- `updated_at`

## 9.2 `payment_transactions`
Purpose:
- Tracks payment attempts and results.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `invoice_id` (fk -> invoices.id, nullable)
- `payment_method_id` (fk -> payment_methods.id, nullable)
- `provider` (string)
- `provider_payment_id` (string, nullable)
- `status` (enum: pending, authorized, succeeded, failed, cancelled, refunded)
- `amount` (decimal)
- `currency` (string)
- `failure_reason` (string, nullable)
- `processed_at` (nullable)
- `created_at`
- `updated_at`

## 9.3 `credit_balances`
Purpose:
- Optional prepaid credits / stored value for tenant.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `balance_amount` (decimal)
- `currency` (string)
- `updated_at`

## 9.4 `credit_events`
Purpose:
- Audit trail for credit changes.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `event_type` (enum: topup, usage_deduction, refund, manual_adjustment, expiry)
- `amount` (decimal)
- `currency` (string)
- `reference_id` (string, nullable)
- `reason` (string, nullable)
- `created_at`

---

## 10. Admin / Support / Audit Layer

## 10.1 `admin_audit_logs`
Purpose:
- Tracks internal sensitive actions.

Minimum fields:
- `id` (uuid, pk)
- `actor_user_id` (fk -> users.id)
- `target_type` (string)
- `target_id` (string)
- `action` (string)
- `reason` (string, nullable)
- `metadata_json` (json, nullable)
- `created_at`

## 10.2 `support_actions`
Purpose:
- Tracks user/tenant support operations.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `actor_user_id` (fk -> users.id)
- `action_type` (enum: investigate_usage, reset_key, grant_credit, suspend_tenant, reactivate_tenant, override_quota)
- `notes` (string)
- `created_at`

## 10.3 `risk_flags`
Purpose:
- Flags abuse, billing, or operational concerns.

Minimum fields:
- `id` (uuid, pk)
- `tenant_id` (fk -> tenants.id)
- `flag_type` (enum: abuse, unpaid_invoice, abnormal_usage, failed_payments, compromised_key)
- `status` (enum: open, monitoring, resolved)
- `details` (string)
- `created_at`
- `resolved_at` (nullable)

---

## 11. Minimal Relationships Summary

- one `user` can have many `auth_identities`
- one `tenant` can have many `tenant_members`
- one `tenant` can have many `api_keys`
- one `api_key` can have many `api_key_scopes`
- one `tenant` can have many `usage_events`
- one `tenant` can have one active `subscription` at a time (simplify first)
- one `billing_cycle` can generate one or more `invoices`
- one `invoice` has many `invoice_lines`
- one `tenant` can have many `payment_transactions`
- all sensitive actions should map into `admin_audit_logs`

---

## 12. Minimum Viable Schema for Phase 1

To start implementation without overbuilding, the minimum useful subset is:

### Identity
- `users`
- `tenants`
- `tenant_members`

### API provisioning
- `api_keys`
- `api_key_scopes`
- `api_key_events`

### Metering
- `usage_events`
- `usage_daily`

### Billing-lite
- `plans`
- `plan_features`
- `subscriptions`

### Admin audit
- `admin_audit_logs`

This subset is enough to support:
- API key issuance
- usage tracking
- quota computation
- admin visibility
- future billing expansion

---

## 13. Suggested Implementation Order

## Step 1
Implement tables/entities for:
- `tenants`
- `tenant_members`
- `api_keys`
- `usage_events`
- `usage_daily`
- `plans`
- `subscriptions`
- `admin_audit_logs`

## Step 2
Add backend instrumentation so every request creates `usage_events`.

## Step 3
Add admin-only read views for:
- usage by tenant
- usage by api key
- current quotas
- top cost drivers

## Step 4
Add customer-facing API key management.

## Step 5
Add invoices and payment rails after usage metering is trusted.

---

## 14. Validation Checklist Before Coding

Before implementation starts, confirm these decisions:
- billing currency strategy
- free-vs-paid plan boundaries
- what counts as billable token/event
- whether WordPress chat traffic and direct API traffic share the same ledger
- whether free users create usage events without a tenant
- whether anonymous traffic gets a pseudo-tenant or separate channel model
- whether invoices are initially manual or automated

---

## 15. Next Recommended File

After this file, the next practical file should be:
- `TTAi_USAGE_METERING_IMPLEMENTATION_PLAN.md`

That file should define:
- where usage events are generated in FastAPI
- exact request lifecycle hooks
- token estimation method
- aggregation jobs
- admin read APIs needed first
