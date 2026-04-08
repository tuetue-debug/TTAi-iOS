# API.TUETUE.VN Part 4 — Truth Pass & Smoke-Test Plan (2026-04-08)

## 4.1 Contract truth pass

### A. Auth surface
#### READY / USABLE FOUNDATION
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/me` *(transitional; should later deprecate in favor of `/api/v1/account/profile`)*
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/sessions`
- `POST /api/v1/auth/logout`
- `PUT /api/v1/auth/change-password`

#### BETA / INTERNAL-VERIFY
- `GET /api/v1/auth/api-key/me`
  - useful for verification/testing of API-key auth path
  - not necessarily a final public product endpoint

#### DEPRECATED
- `GET /api/v1/auth/api-keys`
- `GET /api/v1/auth/usage/stats`
- `GET /api/v1/auth/billing/summary`

### B. Account surface
#### READY / USABLE FOUNDATION
- `GET /api/v1/account/profile`
- `PUT /api/v1/account/profile`
- `GET /api/v1/account/usage/summary`
- `GET /api/v1/account/usage/events`
- `GET /api/v1/account/billing/summary`
- `GET /api/v1/account/billing/limits`
- `GET /api/v1/account/api-keys`
- `POST /api/v1/account/api-keys`
- `DELETE /api/v1/account/api-keys/{key_id}`

### C. Product/runtime surface
#### READY BUT STILL TECHNICALLY PARTIAL
- `POST /api/v1/chat`
  - strong orchestration foundation exists
  - should still be treated as integration-sensitive until smoke-tested with auth + api-key paths

#### REAL / SYSTEM-ORIENTED
- `/api/v1/system/*`
- `/api/v1/models/*`
- `/api/v1/ollama/*`
- `/api/v1/classify`
- `/api/v1/classify/batch`

### D. Admin/control surfaces
#### INTERNAL / ADMIN / CONTROL
- `/api/v1/admin/*`
- `/control-api/*`
- `/control-auth/*`
- `/api/v1/admin/control-dashboard*`

### E. HIDE / CLEAN UP LATER
- `/api/v1/users`
- `/api/users`
- `/api/test/*`
- legacy `/api/*` aliases where versioned route exists

---

## 4.2 Smoke-test plan (next execution step)

### Auth flow
1. register
2. login
3. me
4. refresh
5. sessions
6. logout current refresh token
7. logout all sessions
8. login again
9. change password
10. login with new password

### Account flow
11. get profile
12. update profile
13. get usage summary
14. get usage events
15. get billing summary
16. get billing limits
17. create api key
18. list api keys
19. verify API key identity with `/api/v1/auth/api-key/me`
20. revoke api key

### Chat integration flow
21. call `/api/v1/chat` with user_id payload/header path
22. call `/api/v1/chat` with API key auth path
23. verify usage event captures `user_id` / `api_key_id` correctly
24. verify account usage/billing surfaces reflect that traffic

---

## Current judgment before smoke tests
### Strongly improved
- auth lifecycle is now materially better than before
- account surface now exists as a truthful layer
- API keys moved from mock-ish UI surface to real persistence + verification path

### Still needs proof-by-test
- refresh/logout/session revocation behavior in practice
- API-key-authenticated chat path end-to-end
- account usage/billing reflection after chat traffic

Status: **4.1 COMPLETE, 4.2 READY TO RUN**
