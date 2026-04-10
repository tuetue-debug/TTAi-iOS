# TTAi Simple Proxy Dashboard Control Spec — 2026-04-10

## Mục tiêu
Đặc tả cách `TTAiSimpleProxy` (8015) phải được giám sát, benchmark, và điều khiển bởi Control Dashboard.

---

# I. Core requirement

`8015` không được coi là một service nền “có thì tốt”.
Nó phải là một **dashboard-governed runtime module**.

Dashboard phải giúp trả lời ngay các câu hỏi sau:
1. `8015` có đang chạy không?
2. Nó đang route tới đâu?
3. Nó đang ưu tiên backend nào?
4. Hedge có đang bật không?
5. Nó có đang làm chậm chat path không?
6. Backend nào thực sự trả lời request?
7. Nó có đang làm tăng latency cho `chat.tuetue.vn` không?

---

# II. Dashboard visibility requirements

## 2.1. Module card for 8015
Dashboard phải có card/module riêng cho `TTAiSimpleProxy` gồm:
- service status: running/stopped/degraded
- version/build marker
- current mode
- current preferred backend
- hedge status
- last degraded incident

## 2.2. Backend pool view
Hiển thị pool backend hiện tại:
- backend id
- url
- role
- enabled/disabled
- healthy/unhealthy
- latency rolling average
- last error
- current weight

## 2.3. Routing visibility
Hiển thị:
- last 20 route decisions
- backend selected count
- failover count
- hedge count
- degraded count

## 2.4. End-user path correlation
Rất quan trọng:
Dashboard phải cho thấy latency theo từng lớp:
- WordPress AJAX receive time
- proxy routing time
- backend response time
- total user-perceived latency

---

# III. Dashboard control requirements

## 3.1. Runtime controls
Dashboard phải điều khiển được:
- enable/disable 8015
- restart 8015
- switch mode
- enable/disable hedge
- set hedge delay

## 3.2. Backend controls
Dashboard phải điều khiển được:
- enable/disable từng backend
- set preferred backend
- set backend weight
- maintenance mode per backend
- drain backend from active routing

## 3.3. Policy controls
Dashboard phải điều khiển được:
- remote-first mode
- stabilize mode
- balanced-lite mode
- diagnostic mode

---

# IV. Benchmark requirements

## 4.1. Benchmark must be first-class
Benchmark không phải phụ kiện.
Với 8015, benchmark là bắt buộc vì nghi ngờ hiện tại là:
> proxy layer có thể đang làm tăng độ trễ đáng kể từ user chat path.

## 4.2. Benchmark questions
Benchmark phải trả lời được:
1. đi qua 8015 có chậm hơn direct path không?
2. chậm bao nhiêu ms / giây?
3. chậm do routing layer hay do backend target?
4. hedge có cải thiện hay làm tệ hơn?
5. remote-first có tốt hơn local-first không?

## 4.3. Benchmark paths
### Required paths
1. `WordPress -> 8000/api/chat`
2. `WordPress -> 8015/api/chat -> remote 8000`
3. `WordPress -> 8015/api/chat -> local 8000`
4. `Direct -> 8000/api/chat`
5. `Direct -> remote 8000/api/chat`
6. `Direct -> 8015/api/chat`

## 4.4. Benchmark metrics
- total response time
- proxy overhead time
- backend time
- success rate
- failover occurrence
- hedge occurrence
- user-perceived latency percentile (p50 / p95)

## 4.5. Benchmark display in dashboard
Dashboard nên có:
- last benchmark run
- comparison chart (direct vs proxy)
- route overhead ms
- recommended mode based on results

---

# V. Remote-first priority requirement

## Strategic requirement
Do hạ tầng `vannt-work-op` khỏe hơn, proxy/dashboard phải hỗ trợ:

# **Remote-first routing with higher weight for remote Ollama/inference**

## Why
- home node yếu
- remote node mạnh hơn
- inference nặng nên ưu tiên remote
- home node nên giảm pressure

## Required controls
Dashboard phải có:
- toggle: `remote-first = on/off`
- remote weight slider
- local fallback weight slider
- safe fallback path selector

## Recommended default for next phase
### `remote-first balanced-lite`
- remote work-op: **80%**
- local 8000 stabilization: **20%**
- local heavy executor 8005: **0% by default**
- hedge: OFF initially

---

# VI. Proposed API/control surface

## Example control endpoints
```http
GET  /control-api/proxy/state
POST /control-api/proxy/enable
POST /control-api/proxy/disable
POST /control-api/proxy/restart
PUT  /control-api/proxy/mode
PUT  /control-api/proxy/hedge
GET  /control-api/proxy/backends
PUT  /control-api/proxy/backends/{id}
POST /control-api/proxy/backends/{id}/enable
POST /control-api/proxy/backends/{id}/disable
POST /control-api/proxy/backends/{id}/drain
POST /control-api/proxy/benchmark/run
GET  /control-api/proxy/benchmark/latest
```

---

# VII. Suggested benchmark workflow

## Step 1 — direct baseline
Đo direct call:
- local 8000
- remote 8000

## Step 2 — proxy path
Đo qua 8015 với mode `stabilize`

## Step 3 — compare overhead
Tính:
- proxy added latency
- route variance
- error rate delta

## Step 4 — try remote-first mode
Đo lại với remote-first weight cao

## Step 5 — dashboard recommendation
Dashboard gợi ý mode phù hợp nhất theo benchmark result

---

# VIII. Success criteria

## 8015 is acceptable only if:
- latency overhead is measurable and acceptable
- routing behavior is visible
- dashboard can disable problematic backends quickly
- remote-first mode reduces home pressure
- user-perceived chat latency improves or at least does not regress badly

## 8015 is not acceptable if:
- it is just another opaque layer
- it increases latency without visibility
- it cannot be tuned live from dashboard

---

# IX. Final recommendation

The next phase should treat `8015` as:
- a control-plane managed routing module
- a benchmarked latency-sensitive component
- a remote-first coordinator

That is the only way it remains useful without becoming the next hidden bottleneck.
