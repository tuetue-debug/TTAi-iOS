# TTAi Simple Proxy Canonical Role — 2026-04-10

## Mục tiêu
Chốt vai trò chuẩn của `TTAiSimpleProxy` (port 8015) trong kiến trúc TTAi mới.

---

# I. Core conclusion

`TTAiSimpleProxy` là một thành phần **hữu ích và đáng giữ**.
Tuy nhiên, trong kiến trúc mới, nó chỉ nên giữ **một vai trò chuẩn duy nhất**:

## **Canonical Role:**
### `Hybrid Routing Front Door under Control Plane Governance`

Nghĩa là:
- nó là cửa vào routing cho hybrid chat path
- nó hoạt động dưới sự giám sát và điều khiển của Control Dashboard
- nó không phải business backend
- nó không phải execution truth layer
- nó không phải policy authority độc lập

---

# II. Vai trò đúng của 8015

## 1. Nhận request từ public/customer-facing surfaces
Ví dụ:
- WordPress chat surface
- future chat surfaces
- lightweight internal callers

## 2. Quyết định routing theo control state
8015 không tự hard-code chiến lược dài hạn.
Thay vào đó, nó phải dùng state do control plane cấp:
- enabled backends
- preferred primary
- safe mode
- hedge on/off
- maintenance flags

## 3. Giám sát health cơ bản
- backend available/unavailable
- latency observation
- cooldown backend chết

## 4. Propagate trace
- request id
- route decision
- backend selected
- hedge happened or not

## 5. Ghi routing telemetry
- selected backend
- latency
- failover event
- hedge event
- degraded state

---

# III. Những gì 8015 không nên làm

## 1. Không nên là business/account backend
Không auth/account/quota/billing/portal/admin ở đây.

## 2. Không nên là execution engine
Không gọi provider/model cuối cùng theo kiểu phức tạp nếu có thể tránh.
Execution truth nên ở backend sâu hơn.

## 3. Không nên tự quyết chiến lược độc lập
Không hard-code mãi:
- backend list
- traffic weights
- safe mode
- local-first / remote-first

## 4. Không nên tự recovery mù
Auto recovery chỉ nên xảy ra nếu được control plane bật rõ ràng.

## 5. Không nên là canonical metering anchor
Vì nó không biết chắc provider/model/token truth cuối cùng.

---

# IV. Relationship with Control Dashboard

## 4.1. 8015 phải là managed module
Dashboard control phải nhìn thấy và điều khiển được 8015 như một module riêng.

## 4.2. Dashboard phải quản 8015 được ở các mức sau
### Runtime visibility
- service status
- current backend pool
- current healthy/unhealthy backends
- current mode
- current hedge status

### Runtime control
- enable/disable 8015
- enable/disable từng backend trong pool
- switch safe mode
- enable/disable hedge
- set preferred primary
- set maintenance mode

### Observability
- route history
- recent failures
- recent failovers
- latency by backend
- degraded incidents

## 4.3. Ý nghĩa
8015 không chỉ là một process.
Nó phải là **một module được điều hành bởi dashboard**.

---

# V. Canonical data contract between 8015 and dashboard

## Dashboard → 8015
Dashboard/control plane cung cấp:
- backend pool state
- backend enabled flags
- routing mode
- hedge config
- maintenance mode
- safe mode

## 8015 → Dashboard
8015 phản hồi:
- active runtime status
- backend health snapshot
- recent route decisions
- failover counters
- last degraded ticket
- build/runtime identity

---

# VI. Canonical operating modes

## Mode 1 — `stabilize`
- hedge off
- preferred backend = safest known path
- no auto-recovery
- low complexity routing

## Mode 2 — `balanced`
- primary backend + controlled failover
- hedge optional
- standard production behavior

## Mode 3 — `remote-first`
- ưu tiên `vannt-work-op`
- home node giảm inference pressure

## Mode 4 — `maintenance`
- từ chối request mới hoặc route sang fallback safe path
- dùng khi backend pool đang thay đổi

## Mode 5 — `diagnostic`
- verbose logging
- no blind recovery
- controlled test routing

---

# VII. Canonical backend classes

## Backend class A — Stabilization backend
Ví dụ:
- `localhost:8000`

## Backend class B — Primary inference backend
Ví dụ:
- `100.89.201.7:8000`

## Backend class C — Optional local execution backend
Ví dụ:
- `localhost:8005`

### Note
Class C không nên mặc định active nếu home node không phù hợp.

---

# VIII. Strategic guidance

## Current phase
8015 nên được coi là:
- một module tốt
- nhưng chưa canonical
- cần được refactor thành control-plane-managed routing layer

## Future phase
Khi hoàn thiện, 8015 có thể trở thành:
- default routed chat entry
- safe front door cho WordPress/public chat
- measurable routing layer under dashboard control

---

# IX. Final statement

`TTAiSimpleProxy` không phải thứ nên bỏ.
Nó là thứ nên **chuẩn hóa lại vai trò**.

### Câu định nghĩa cuối cùng:
> 8015 là Hybrid Routing Front Door của TTAi, chịu sự giám sát và điều khiển bởi Control Dashboard, dùng để route request đến các backend inference phù hợp mà không tự mang business logic hay execution truth.
