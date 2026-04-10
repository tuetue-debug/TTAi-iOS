# TTAi Proxy Phase A Build Plan — 2026-04-11

## Mục tiêu
Biến nhánh tài liệu về `TTAiSimpleProxy` thành kế hoạch build cụ thể cho **Phase A: read-only visibility first**.

Phase A không nhằm điều khiển proxy ngay.
Phase A nhằm đạt được 3 thứ:
1. dashboard nhìn thấy `8015` như một module thật
2. dashboard nhìn thấy backend pool thật
3. dashboard có chỗ để hiển thị benchmark/latest result

---

# I. Phase A scope

## In scope
### Backend
- `GET /control-api/proxy/state`
- `GET /control-api/proxy/backends`
- `GET /control-api/proxy/benchmark/latest`

### Frontend
- proxy status card
- backend pool table
- benchmark latest summary panel

### Data plumbing
- source runtime state from actual service/config
- no write controls yet
- no restart/enable/disable yet
- no benchmark execution yet

## Out of scope
- live mode switching
- backend enable/disable mutations
- hedge toggle mutations
- run benchmark button
- topology rewrite complete

---

# II. Files to create / update

## Create
### 1. `repos/TTAi-deployment/fastapi/proxy_state.py`
Purpose:
- provide read-only state for proxy runtime
- read active service/runtime facts
- expose backend pool data in normalized shape

### 2. `repos/TTAi-deployment/fastapi/proxy_benchmark.py`
Purpose:
- initially provide placeholder/latest result loading
- later extend for benchmark execution in Phase C

## Update
### 3. `repos/TTAi-deployment/fastapi/main.py`
Add new endpoints:
- `/control-api/proxy/state`
- `/control-api/proxy/backends`
- `/control-api/proxy/benchmark/latest`

### 4. `repos/TTAi-deployment/fastapi/control_dashboard/static/dashboard.js`
Add loaders/renderers:
- `loadProxyState()`
- `loadProxyBackends()`
- `loadProxyBenchmark()`

### 5. `repos/TTAi-deployment/fastapi/control_dashboard/static/dashboard.html`
Add UI containers for:
- proxy module card
- backend pool table
- benchmark summary

---

# III. Backend design details

## 3.1. `proxy_state.py` responsibilities

### Function A — `get_proxy_runtime_state()`
Return:
- service_up/down/degraded
- service_name
- build/version if known
- current_mode (best effort)
- preferred_backend (best effort)
- hedge_enabled (best effort)
- last_probe timestamp

### Function B — `get_proxy_backends_state()`
Return normalized backend entries:
- id
- url
- role
- node
- enabled
- healthy
- latency_ms
- error
- preferred
- weight

### Function C — `probe_proxy_health()`
Probe:
- `http://localhost:8015/`
- `http://localhost:8015/health`

### Function D — `probe_backend_health(url)`
Best-effort check backend root/health.

## 3.2. Initial truth strategy
Phase A có thể chấp nhận **best-effort truth**, theo thứ tự:
1. live probe of 8015 if running
2. code/config-derived backend list if 8015 is off
3. overlay with audited canonical assumptions from current docs

### Important
Không được hard-code fake “operational” nếu service đang off.

## 3.3. Source priority for backend pool
### Priority order
1. live 8015 root response if available
2. `simple_proxy.py` code-derived pool
3. canonical redesign defaults

### Initial normalized roles
- `localhost:8000` → `stabilization`
- `100.89.201.7:8000` → `primary-inference`
- `localhost:8005` → `optional-local-executor`

---

# IV. API response contracts

## 4.1. `GET /control-api/proxy/state`
```json
{
  "summary": {
    "service_status": "running|stopped|degraded",
    "service_name": "TTAiSimpleProxy",
    "port": 8015,
    "mode": "stabilize",
    "preferred_backend": "remote-workop-8000",
    "hedge_enabled": false,
    "backend_count": 3,
    "healthy_backend_count": 2,
    "last_probe": "2026-04-11T00:00:00Z"
  },
  "runtime": {
    "live": false,
    "source": "code-derived|live-probe|mixed",
    "version": "1.1.0",
    "backends": ["http://localhost:8005", "http://localhost:8000", "http://100.89.201.7:8000"]
  }
}
```

## 4.2. `GET /control-api/proxy/backends`
```json
{
  "summary": {
    "count": 3,
    "healthy": 2,
    "enabled": 2,
    "source": "code-derived"
  },
  "items": [
    {
      "id": "local-fastapi-8000",
      "url": "http://localhost:8000",
      "role": "stabilization",
      "node": "vannt-home-zq",
      "enabled": true,
      "healthy": true,
      "preferred": false,
      "weight": 20,
      "latency_ms": 120,
      "error": null
    }
  ]
}
```

## 4.3. `GET /control-api/proxy/benchmark/latest`
```json
{
  "available": false,
  "summary": {
    "last_run": null,
    "status": "not_run"
  },
  "results": null,
  "notes": [
    "Benchmark execution is planned for Phase C"
  ]
}
```

---

# V. Frontend design details

## 5.1. Proxy status card
Fields:
- status badge
- mode
- preferred backend
- hedge enabled
- healthy backends / total
- last probe

## 5.2. Backend pool table
Columns:
- Name / ID
- URL
- Role
- Node
- Enabled
- Healthy
- Latency
- Preferred
- Weight
- Error

### Phase A note
Actions column may display placeholder text `Phase B`.

## 5.3. Benchmark latest panel
Display:
- last run
- current status (`not_run`, `available`)
- if no data, show note that benchmark execution lands in Phase C

---

# VI. Dashboard JS task list

## Task A — add DOM hooks
Need new elements in HTML:
- `proxyStatusCard`
- `proxyBackendTable`
- `proxyBenchmarkPanel`

## Task B — add loader functions
### `loadProxyState()`
- fetch `/control-api/proxy/state`
- render status card

### `loadProxyBackends()`
- fetch `/control-api/proxy/backends`
- render backend rows

### `loadProxyBenchmark()`
- fetch `/control-api/proxy/benchmark/latest`
- render latest summary

## Task C — wire into `refreshAll()`
Add these calls to main refresh pipeline.

---

# VII. Backend task list

## Task 1 — create `proxy_state.py`
Implement:
- lightweight probing
- code-derived backend parsing or explicit normalized mapping
- backend health probing

## Task 2 — create `proxy_benchmark.py`
Implement:
- `get_latest_proxy_benchmark()` placeholder
- future file path constants for benchmark result storage

## Task 3 — extend `main.py`
Add 3 read-only endpoints using control auth:
- `/control-api/proxy/state`
- `/control-api/proxy/backends`
- `/control-api/proxy/benchmark/latest`

## Task 4 — ensure no fake operational claims
If 8015 is down, endpoint must say so clearly.

---

# VIII. Acceptance criteria for Phase A

## Backend accepted when
- `/control-api/proxy/state` returns valid JSON
- `/control-api/proxy/backends` returns normalized pool data
- `/control-api/proxy/benchmark/latest` returns clean placeholder or real latest data

## Frontend accepted when
- dashboard renders a visible proxy card
- dashboard renders backend pool table
- dashboard renders benchmark latest panel
- refresh cycle includes proxy module without breaking existing panels

## Product accepted when
Operator can answer:
1. is 8015 up or down?
2. what backends would it use?
3. which backend is conceptually preferred?
4. is there benchmark data yet?

---

# IX. Risks

## Risk 1 — 8015 off means live truth is partial
Mitigation:
- expose `source` field (`live-probe`, `code-derived`, `mixed`)

## Risk 2 — code-derived pool may differ from future redesign pool
Mitigation:
- keep role mapping explicit and label source clearly

## Risk 3 — dashboard HTML may need structural edits
Mitigation:
- add isolated proxy section rather than refactor all existing layout at once

---

# X. Recommended next step after Phase A

Immediately after Phase A lands:
- move to Phase B live controls
- then Phase C benchmark execution

This sequence preserves clarity:
1. see it
2. control it
3. measure it

---

# XI. Final statement

Phase A is the bridge from documents to reality.
If done well, it gives the team a truthful dashboard view of `8015` without prematurely restoring or mutating the proxy runtime.
