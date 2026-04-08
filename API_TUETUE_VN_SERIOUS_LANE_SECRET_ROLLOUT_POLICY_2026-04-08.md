# API.TUETUE_VN Serious-Lane Secret & Rollout Policy (2026-04-08)

## Objective
Define the minimum secret/rollout discipline required before `api.tuetue.vn` can be treated as a serious deployment lane rather than an advanced dev/testing lane.

---

# 1. Secret strength floor
## JWT secret
### Policy
For serious lanes, the JWT secret should be:
- explicitly configured
- high-entropy
- at least 32 bytes / strong random equivalent

### Why
Short HMAC secrets weaken trust and already triggered warnings in testing.
A serious lane should not normalize that weakness.

### Recommendation
Move toward:
- warning first if below threshold
- later hard-fail serious lane if below threshold

This keeps rollout disciplined without causing reckless breakage today.

---

# 2. Serious-lane required secrets
## Minimum required
- `TTAI_JWT_SECRET`
- `TTAI_ADMIN_TOKEN`

## Strong recommendation
Both should be:
- generated separately
- not reused across roles/surfaces
- not stored casually in tracked files

---

# 3. Override policy
## Allowed only as controlled diagnostics
### `TTAI_AUTH_EXPOSE_FLOW_TOKENS=true` outside dev-like lane
This should be treated as:
- temporary
- controlled
- explicitly risky

### Policy judgment
Allowed only for tightly controlled diagnostics, not as normal rollout posture.

## Not acceptable as normal serious-lane posture
- relying on fallback JWT secret
- allowing dev seed user creation
- relying on implicit local runtime URLs for serious rollout

---

# 4. Minimum rollout checklist
A lane should not be described as serious-rollout-ready unless at least these are true:

## Required
1. `ENVIRONMENT` is explicitly non-dev (`production` / `staging`)
2. `TTAI_JWT_SECRET` is explicitly configured
3. `TTAI_ADMIN_TOKEN` is explicitly configured
4. dev seed user is disabled
5. auth flow token exposure is not left on casually
6. runtime dependencies (CLI proxy / Ollama) are explicit, not accidental defaults

## Strongly recommended
7. JWT secret meets strength floor
8. delivery provider plan is chosen
9. auth delivery bridge has a real provider path or explicit rollout limitation note
10. operator understands deprecated/internal/debug surfaces are not the public contract

---

# 5. Rollout claim discipline
## Do NOT claim
- "production-ready"
- "serious-lane complete"
- "fully hardened"

unless the minimum checklist above is satisfied and external delivery integration is accounted for.

## Safer truthful labels
Before that point, use labels like:
- `deployment-aware foundation`
- `serious-lane-prep`
- `external-integration-pending`

---

# 6. Recommended next move after this policy
Once this policy is accepted, the next practical step is:
- implement a first provider interface/stub or real delivery adapter path
- then perform a rollout readiness pass against the checklist above

---

# 7. Final conclusion
A serious lane is not defined by intent; it is defined by discipline.
This policy establishes the minimum discipline for secrets, overrides, and rollout claims.

Status: **Serious-lane secret/rollout policy complete.**
