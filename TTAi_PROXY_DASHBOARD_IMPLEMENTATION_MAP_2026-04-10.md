# TTAi Proxy Dashboard Implementation Map — 2026-04-10

## Mục tiêu
Map từ tài liệu chiến lược/spec hiện tại sang code thực tế của dashboard/control hiện có, để biết chính xác:
- cái gì đã có
- cái gì dùng lại được
- cái gì đang hard-code / stale
- cái gì phải thêm để dashboard quản được `TTAiSimpleProxy` (8015) thật
- cái gì cần để benchmark proxy overhead và remote-first routing

---

# I. Executive summary

## Kết luận nhanh
Code dashboard/control hiện tại **chưa phải control plane thật**, nhưng đã có một khung khá hữu dụng để mở rộng.

### Những gì đã có thể tận dụng
- `control_dashboard/static/dashboard.js` đã có cấu trúc load nhiều panel song song
- `main.py` đã có `control-api/*` namespace
- đã có control action history (`/control-api/actions`, `/control-api/actions/run`)
- đã có models/system/topology endpoints
- đã có auth/session lane cho dashboard

### Những gì đang là gap lớn
- dashboard JS hiện vẫn dựa nhiều vào API collector cũ (`/api/*`) và token hard-coded
- topology endpoint đang chứa **inventory hard-coded / stale**, không phản ánh runtime thật
- chưa có endpoint nào dành riêng cho `proxy state / backend pool / hedge / mode / benchmark`
- chưa có panel UI cho proxy module
- chưa có benchmark runner/control surface nào cho direct-vs-proxy latency

### Kết luận thực thi
Có thể đi tiếp theo hướng:
1. **mở rộng `control-api/*` thay vì dựng lane mới**
2. **thêm module proxy vào dashboard hiện có**
3. **tách dần khỏi collector-style `/api/*` legacy calls**

---

# II. Current frontend state (`dashboard.js`)

## 2.1. Current API usage in dashboard.js
Dashboard hiện gọi 2 nhóm endpoint:

### Legacy-ish `/api/*`
- `/api/models`
- `/api/models/select`
- `/api/workloads`
- `/api/health-summary`
- `/api/vector/backup`

### Newer `/control-api/*`
- `/control-api/overview`
- `/control-api/errors`
- `/control-api/quota`
- `/control-api/billing`

## 2.2. Frontend structure hiện tại
Dashboard UI đang có các panel:
- overall status
- overview metrics
- billing/quota/error summaries
- model selectors
- GPU metrics
- vector stats
- service health list
- backup trigger

## 2.3. Reusable frontend patterns
Có thể tái dùng ngay:
- `loadAdminOverview()` pattern cho summary panels
- `renderSummaryList()` cho mini metric blocks
- `refreshAll()` orchestration
- periodic refresh 30s

## 2.4. Frontend issues/gaps
### 1. Hard-coded secrets in JS
- `CONTROL_TOKEN`
- `ADMIN_TOKEN`

Điều này rất không đẹp cho production control surface.

### 2. Mixed API eras
Dashboard hiện đang pha trộn:
- collector APIs cũ
- control-api mới

### 3. No proxy module
Không có UI nào cho:
- 8015 status
- backend pool
- hedge
- remote-first
- benchmark

---

# III. Current backend state (`main.py`)

## 3.1. Existing useful control endpoints
Đã có sẵn:
- `GET /control-api/overview`
- `GET /control-api/quota`
- `GET /control-api/billing`
- `GET /control-api/errors`
- `GET /control-api/models`
- `GET /control-api/system`
- `GET /control-api/topology`
- `GET /control-api/usage`
- `GET /control-api/session`
- `GET /control-api/actions`
- `POST /control-api/actions/run`

## 3.2. Existing action framework
`/control-api/actions/run` hiện đã có framework xử lý action với:
- validation
- action history log
- actor/session tracking
- status success/error recording

Đây là nền rất tốt để mở rộng thêm nhóm action cho proxy.

## 3.3. Existing topology endpoint problem
`/control-api/topology` hiện trả về inventory hard-coded, ví dụ:
- 8005 = operational
- 8015 = operational
- WordPress = offline
- FastAPI Original = offline

Trong khi audit runtime thật vừa xác nhận khác đáng kể.

### Kết luận
`/control-api/topology` hiện là **mock/stale topology endpoint**, không thể dùng làm truth source cho control plane.

## 3.4. Existing models/system endpoints useful but incomplete
### `GET /control-api/models`
Hữu ích cho:
- provider summary
- warm model counts
- ollama visibility

Nhưng chưa có:
- proxy backend pool
- route mode
- remote-first weighting

### `GET /control-api/system`
Hữu ích cho:
- health summary
- workloads
- alerts

Nhưng chưa expose proxy-specific runtime state.

---

# IV. What can be reused directly for proxy control

## 4.1. Reuse `control-api` namespace
Không cần tạo namespace mới.

### Đề xuất
Thêm dưới `control-api/proxy/*`:
- `GET /control-api/proxy/state`
- `GET /control-api/proxy/backends`
- `PUT /control-api/proxy/mode`
- `PUT /control-api/proxy/hedge`
- `POST /control-api/proxy/enable`
- `POST /control-api/proxy/disable`
- `POST /control-api/proxy/restart`
- `POST /control-api/proxy/backends/{id}/enable`
- `POST /control-api/proxy/backends/{id}/disable`
- `PUT /control-api/proxy/backends/{id}/weight`
- `POST /control-api/proxy/benchmark/run`
- `GET /control-api/proxy/benchmark/latest`

## 4.2. Reuse control action history
Mọi thao tác proxy nên ghi qua action log hiện có.
Ví dụ action names mới:
- `proxy_enable`
- `proxy_disable`
- `proxy_restart`
- `proxy_mode_set`
- `proxy_backend_enable`
- `proxy_backend_disable`
- `proxy_weight_update`
- `proxy_benchmark_run`

## 4.3. Reuse dashboard refresh orchestration
`refreshAll()` có thể mở rộng thêm:
- `loadProxyState()`
- `loadProxyBenchmark()`
- `loadProxyTelemetry()`

---

# V. What must be added in backend

## 5.1. New proxy state source
Hiện chưa có source chuẩn cho:
- current 8015 runtime status
- backend pool
- mode
- hedge settings
- preferred backend

### Cần thêm
Một module kiểu:
- `fastapi/proxy_control.py`
hoặc
- `fastapi/proxy_state.py`

Module này chịu trách nhiệm:
- đọc config/state của 8015
- trả runtime state cho dashboard
- cập nhật control state

## 5.2. New benchmark runner
Cần một runner rõ ràng cho benchmark direct-vs-proxy.

### Đề xuất file/module
- `fastapi/proxy_benchmark.py`

### Nhiệm vụ
- chạy test paths chuẩn
- đo latency
- lưu latest result
- trả summary cho dashboard

## 5.3. Replace stale topology with live topology
`/control-api/topology` cần được refactor từ hard-coded inventory thành live-derived topology.

### Có thể lấy từ:
- service status
- real port listeners
- live configured backend pool
- WordPress integration facts (manual metadata nếu cần)

---

# VI. What must be added in frontend

## 6.1. New proxy module UI
Thêm các section mới trong dashboard HTML/JS:

### A. Proxy status card
- service status
- mode
- preferred backend
- hedge on/off

### B. Backend pool table
- backend id/url/role
- enabled
- healthy
- latency
- weight
- actions

### C. Benchmark panel
- direct local avg
- direct remote avg
- proxy avg
- proxy overhead
- p50/p95
- run benchmark button

### D. Telemetry panel
- recent route selections
- failovers
- degraded count

## 6.2. New JS loaders/actions
Cần thêm functions:
- `loadProxyState()`
- `loadProxyBenchmark()`
- `loadProxyTelemetry()`
- `toggleProxy()`
- `setProxyMode()`
- `toggleProxyBackend()`
- `updateProxyWeight()`
- `runProxyBenchmark()`

---

# VII. Recommended implementation order

## Phase A — Read-only visibility first
### Backend
1. `GET /control-api/proxy/state`
2. `GET /control-api/proxy/backends`
3. `GET /control-api/proxy/benchmark/latest` (placeholder if needed)

### Frontend
4. proxy status card
5. backend pool table
6. benchmark read panel

## Phase B — Live controls
### Backend
7. `PUT /control-api/proxy/mode`
8. `PUT /control-api/proxy/hedge`
9. backend enable/disable endpoints
10. weight update endpoint

### Frontend
11. mode selector
12. backend toggles
13. weight sliders
14. hedge toggle

## Phase C — Benchmark execution
### Backend
15. `POST /control-api/proxy/benchmark/run`
16. benchmark persistence/latest result

### Frontend
17. run benchmark button
18. direct-vs-proxy chart
19. recommended mode banner

## Phase D — Topology truth cleanup
20. refactor `/control-api/topology`
21. stop using stale hard-coded inventory
22. align topology with actual runtime/service truth

---

# VIII. Concrete file touch map

## Backend likely files to edit
- `repos/TTAi-deployment/fastapi/main.py`
- `repos/TTAi-deployment/fastapi/control_dashboard/static/dashboard.js`
- `repos/TTAi-deployment/fastapi/control_dashboard/static/dashboard.html`

## Backend likely files to create
- `repos/TTAi-deployment/fastapi/proxy_state.py`
- `repos/TTAi-deployment/fastapi/proxy_benchmark.py`

## Optional later
- `repos/TTAi-deployment/fastapi/proxy_control_actions.py`

---

# IX. Key architectural decisions now locked

## 1. `8015` is useful but must be dashboard-governed
Locked.

## 2. Benchmark is mandatory
Locked.

## 3. Remote-first priority for `vannt-work-op`
Locked.
Suggested default phase weight:
- remote `100.89.201.7:8000` = 80
- local `localhost:8000` = 20
- local `8005` = 0 by default

## 4. Do not restore old assumptions blindly
Locked.

---

# X. Final implementation stance

The dashboard/control stack already has enough structure to evolve into a real proxy control plane.
What is missing is not a new system from scratch, but a **focused extension**:
- add proxy state
- add proxy control
- add proxy benchmark
- replace stale topology

That is the cleanest path from documents to working implementation.
