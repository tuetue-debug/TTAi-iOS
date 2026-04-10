# TTAi Proxy Phase B Build Plan — 2026-04-11

## Mục tiêu
Chuyển proxy module từ **read-only visibility** sang **live controls** dưới quyền điều khiển của Control Dashboard.

Phase B tập trung vào việc cho operator chỉnh được:
- mode
- hedge
- backend enabled/disabled
- backend weights

Phase B chưa chạy benchmark execution, nhưng phải tạo nền rất tốt cho Phase C.

---

# I. Phase B scope

## In scope
### Backend controls
- set proxy mode
- set hedge enabled / delay
- enable/disable backend
- update backend weights

### Frontend controls
- mode selector
- hedge toggle
- hedge delay input
- backend enable/disable buttons
- backend weight inputs/sliders

### Persistence / state
- a lightweight proxy control state store
- runtime-visible current config

## Out of scope
- benchmark execution runner
- charting direct-vs-proxy data
- automatic recommendation engine
- full topology rewrite

---

# II. Design principle

## 2.1. Dashboard is the authority
Proxy config must not remain hidden in hard-coded Python constants only.
Dashboard control is the operational authority.

## 2.2. Phase B uses overlay control state
Phase B does **not** need to fully rewrite `simple_proxy.py` yet.
Instead, it can introduce a control-state layer that:
- stores desired proxy config
- is shown in dashboard
- becomes the future runtime source of truth

## 2.3. Remote-first default remains locked
Default control posture remains:
- remote `100.89.201.7:8000` → 80
- local `localhost:8000` → 20
- local `8005` → 0
- hedge off initially
- mode = `stabilize` or `remote-first`

---

# III. Files to create / update

## Create
### 1. `repos/TTAi-deployment/fastapi/proxy_control_state.py`
Purpose:
- persist dashboard-controlled proxy configuration
- read/write mode, hedge, backend enabled flags, backend weights

## Update
### 2. `repos/TTAi-deployment/fastapi/proxy_state.py`
Purpose:
- merge live/code-derived state with control-state overlay
- reflect dashboard-controlled weights/enabled flags

### 3. `repos/TTAi-deployment/fastapi/main.py`
Add write endpoints:
- `/control-api/proxy/mode`
- `/control-api/proxy/hedge`
- `/control-api/proxy/backends/{id}/enable`
- `/control-api/proxy/backends/{id}/disable`
- `/control-api/proxy/backends/{id}/weight`

### 4. `repos/TTAi-deployment/control-frontend/app.js`
Add controls in Overview proxy panels.

---

# IV. Control state model

## 4.1. Suggested storage
Use a JSON file first for speed and transparency.

### Example path
- `workspace/state/proxy_control_state.json`

## 4.2. Suggested schema
```json
{
  "version": 1,
  "updated_at": "2026-04-11T00:00:00Z",
  "mode": "remote-first",
  "hedge": {
    "enabled": false,
    "delay_seconds": 0.35
  },
  "backends": {
    "local-fastapi-8000": {
      "enabled": true,
      "weight": 20
    },
    "remote-workop-8000": {
      "enabled": true,
      "weight": 80
    },
    "local-hybrid-8005": {
      "enabled": false,
      "weight": 0
    }
  }
}
```

## 4.3. Why file-backed first
- simple
- inspectable
- easy rollback
- enough for current phase

Later can move to Redis or richer control store.

---

# V. New backend endpoints

## 5.1. Set mode
### Endpoint
`PUT /control-api/proxy/mode`

### Request
```json
{ "mode": "stabilize|remote-first|balanced-lite|diagnostic" }
```

### Effect
- update control state
- log action

## 5.2. Set hedge
### Endpoint
`PUT /control-api/proxy/hedge`

### Request
```json
{ "enabled": false, "delay_seconds": 0.35 }
```

## 5.3. Enable backend
### Endpoint
`POST /control-api/proxy/backends/{id}/enable`

## 5.4. Disable backend
### Endpoint
`POST /control-api/proxy/backends/{id}/disable`

## 5.5. Update weight
### Endpoint
`PUT /control-api/proxy/backends/{id}/weight`

### Request
```json
{ "weight": 80 }
```

---

# VI. Backend implementation tasks

## Task 1 — create `proxy_control_state.py`
Functions:
- `load_proxy_control_state()`
- `save_proxy_control_state()`
- `set_proxy_mode(mode)`
- `set_proxy_hedge(enabled, delay)`
- `set_backend_enabled(backend_id, enabled)`
- `set_backend_weight(backend_id, weight)`

## Task 2 — overlay control state in `proxy_state.py`
When building backend list:
- replace default enabled/weight/preferred with control-state values if present
- expose current mode/hedge from control state

## Task 3 — add new request models in `main.py`
Need simple payload models for:
- mode update
- hedge update
- weight update

## Task 4 — add endpoints to `main.py`
All must require `get_current_control_user`.

## Task 5 — log actions
Prefer using existing control action history framework.

---

# VII. Frontend implementation tasks

## 7.1. Overview panel upgrade
### Proxy Status panel
Add:
- mode dropdown
- hedge toggle
- hedge delay display/input

### Proxy Backend Pool panel
Add per backend:
- enable/disable button
- weight input
- apply button

## 7.2. Suggested UX approach
### Keep it simple
Do not build a huge settings page yet.
Embed controls directly into existing Overview proxy panels.

## 7.3. New JS functions
- `updateProxyMode(mode)`
- `updateProxyHedge(enabled, delay)`
- `toggleProxyBackend(id, enabled)`
- `updateProxyBackendWeight(id, weight)`

After each mutation:
- reload overview

---

# VIII. Validation rules

## Mode
Allowed values:
- `stabilize`
- `remote-first`
- `balanced-lite`
- `diagnostic`

## Hedge delay
- numeric
- between `0.0` and `5.0` seconds

## Weight
- integer
- between `0` and `100`

## Backend id
Allowed current ids:
- `local-fastapi-8000`
- `remote-workop-8000`
- `local-hybrid-8005`

---

# IX. Acceptance criteria

## Backend accepted when
- mode can be changed via API
- hedge config can be updated via API
- backend enabled/disabled state can be updated via API
- backend weight can be updated via API
- `/control-api/proxy/state` reflects latest control state
- `/control-api/proxy/backends` reflects latest control state

## Frontend accepted when
- operator can change mode from Overview
- operator can toggle hedge from Overview
- operator can toggle backend enabled state from Overview
- operator can adjust backend weight from Overview
- changes persist after page reload

## Product accepted when
Operator can do these from dashboard without touching code:
1. switch to remote-first
2. keep 8005 at 0/off
3. lower local 8000 to 20
4. disable a problematic backend quickly

---

# X. Risks and mitigation

## Risk 1 — control state exists but proxy runtime does not yet obey it fully
Mitigation:
- Phase B explicitly focuses on dashboard-governed control layer first
- full runtime obedience can be tightened in later phase

## Risk 2 — operator confusion if UI controls exist but 8015 is still off
Mitigation:
- display service status clearly
- label controls as config state / desired state

## Risk 3 — stale defaults remain in `simple_proxy.py`
Mitigation:
- control-state overlay must visually dominate in dashboard output

---

# XI. Recommended next step after Phase B

After Phase B is live:
- move immediately to Phase C benchmark execution
- compare direct vs proxy
- test remote-first vs stabilize
- decide whether 8015 should be restored, and under what mode

---

# XII. Final statement

Phase B makes proxy control real.
Without it, Phase C benchmark would only measure a mostly static configuration.
With it, benchmark becomes operationally useful because the team can change config and measure the effect immediately.
