# TTAiSimpleProxy Evaluation and Redesign — 2026-04-10

## Mục tiêu
Đánh giá đúng vai trò của `Hybrid Proxy / TTAiSimpleProxy` (port 8015), lý do nó từng hữu ích, lý do có thể gây vấn đề, và hướng điều chỉnh để dùng được trong các phase tiếp theo.

---

# I. Executive conclusion

## Kết luận ngắn
- **Bật lại `TTAiSimpleProxy` đúng là đơn giản về thao tác kỹ thuật**.
- Nhưng **không nên xem việc bật lại là giải pháp hoàn chỉnh**.
- `TTAiSimpleProxy` hiện là một **routing shim hữu dụng nhưng còn lẫn vai trò**, mang assumptions cũ, và nếu dùng nguyên trạng thì dễ kéo hệ quay lại trạng thái khó kiểm soát.

## Nhận định chiến lược
`TTAiSimpleProxy` **đáng giữ**, nhưng phải được **giảm vai trò và chuẩn hóa lại** thành:
- lightweight routing front door
- trace propagation layer
- backend availability selector
- failover/hedge coordinator

Nó **không nên** tiếp tục là nơi gánh:
- policy chiến lược đầy đủ
- business/account logic
- assumptions cứng về backend cũ
- auto-recovery mù mà không có control-plane authority

---

# II. Những gì đã xác minh được

## 2.1. Runtime identity
Từ runtime trace trước đây:
- Port `8015`
- service identity: `TTAi Load Balancer`
- version: `1.1.0`
- backends:
  - `http://localhost:8005`
  - `http://localhost:8000`
  - `http://100.89.201.7:8000`
- hedge enabled: `true`
- hedge delay: `0.35s`

## 2.2. Current code anchor
File đọc được: `simple_proxy.py`

Các đặc điểm chính:
- FastAPI app riêng
- danh sách backend hard-coded
- health monitor nền mỗi 5 giây
- cooldown backend lỗi 90 giây
- có hedged request giữa local/remote
- gọi target endpoint cố định là `/api/chat`
- có trigger `auto_recovery.ps1` nếu all backends fail

## 2.3. Backend list hiện tại trong code
```python
BACKENDS = [
    "http://localhost:8005",
    "http://localhost:8000",
    "http://100.89.201.7:8000"
]
```

## 2.4. Request logic hiện tại
- request vào `POST /api/chat`
- proxy chọn backend theo `BACKEND_PRIORITY`
- có thể tạo hedged request sang pool còn lại
- backend thành công đầu tiên sẽ thắng
- nếu tất cả fail → trả `503` + trigger recovery script

---

# III. Điểm mạnh của TTAiSimpleProxy

## 3.1. Vai trò routing layer là đúng
Tách một lớp proxy riêng để:
- định tuyến request
- tách entry path khỏi execution path
- gom health state
- failover/fallback

=> Đây là hướng kiến trúc tốt.

## 3.2. Có hedge/failover thực dụng
Ý tưởng hedge `0.35s` là hợp lý trong bối cảnh:
- local runtime có thể chậm
- remote runtime có thể nhanh hơn cho vài loại query
- hệ cần practical availability hơn là purity

## 3.3. Có health-aware cooldown
`COOLDOWN_SECONDS = 90` là một cơ chế nhỏ nhưng hữu ích, tránh hammer backend chết.

## 3.4. Có log routing event
`logs/load_balancer.jsonl` là nền tốt cho:
- route telemetry
- latency analysis
- error analysis

=> rất đáng giữ.

---

# IV. Điểm yếu / vấn đề hiện tại

## 4.1. Hard-coded topology cũ
Proxy hiện assume:
- `8005` luôn là local hybrid runtime
- `8000` luôn là local legacy/hybrid backend
- `100.89.201.7:8000` luôn là remote backend

Vấn đề là topology hiện tại đã drift:
- `8005` đang OFF
- `8000` giờ đã là control/account/API backend mạnh hơn xưa
- remote backend đang sống nhưng vai trò cần chốt lại

=> Proxy đang mang **assumption cũ**, không phải control-state-aware topology.

## 4.2. Lẫn routing với policy
Proxy đang làm lẫn:
- backend ordering
- hedge strategy
- health memory
- recovery trigger

Nhưng chưa có tách rõ giữa:
- policy do control plane quyết định
- availability runtime thực tế
- execution truth ở backend sâu hơn

## 4.3. Auto recovery có thể nguy hiểm nếu không có authority
Khi all backends fail, proxy gọi `auto_recovery.ps1`.
Điều này có thể hữu ích, nhưng nếu không có control-plane authority và audit log rõ:
- dễ tạo hành vi restart mù
- dễ gây service churn
- khó chứng minh hệ đang làm gì

## 4.4. Hedge có thể tăng tải nếu dùng sai node
Hedged request là con dao hai lưỡi:
- tốt khi backend primary có latency variance
- xấu nếu node yếu bị buộc nhận request song song không cần thiết

Đặc biệt trên `vannt-home-zq`, nếu `8005` local runtime nặng và `8015` hedge sang local quá hăng, máy càng ì.

## 4.5. Chưa phải canonical billing/account anchor
Proxy chỉ biết backend nào phản hồi trước, chưa chắc biết:
- provider cuối cùng
- model cuối cùng
- fallback chain thật
- token truth thật

=> không nên để nó thành truth writer cho metering/billing.

---

# V. Đánh giá câu hỏi quan trọng: có nên bật lại không?

## Câu trả lời ngắn
### Có thể bật lại rất nhanh.
Nhưng:
### **không nên bật lại nguyên trạng rồi coi như đã khôi phục xong.**

## Khi nào nên bật lại?
Nên bật lại khi một trong hai điều đúng:

### A. Mục tiêu là diagnostic / temporary restore
- cần kiểm tra lại đường WordPress cũ
- cần chứng minh path `WordPress -> 8015 -> backend` có còn hoạt động không
- bật tạm để đo và quan sát

### B. Mục tiêu là restore có kiểm soát
- đã chốt role mới cho 8015 là lightweight routing layer
- đã chốt backend pool hợp lệ
- đã chốt hedge policy mới
- đã xác định home node không bị inference pressure quá mức

## Khi nào không nên bật lại nguyên trạng?
- khi backend list chưa được chuẩn hóa
- khi 8005 vẫn là local heavy path không mong muốn
- khi home node đang chịu áp lực từ Ollama/local inference
- khi WordPress target chưa được đổi/ghi nhận rõ

---

# VI. Vai trò đúng của 8015 trong kiến trúc mới

## 8015 nên là gì?
### `Hybrid Routing Front Door`
Nhiệm vụ đúng:
1. nhận request từ WordPress / public chat surface
2. kiểm tra backend availability
3. route theo policy do control plane cấp
4. propagate trace id
5. log route decision
6. failover khi backend chết

## 8015 không nên là gì?
1. không nên chứa logic business/account
2. không nên tự quyết toàn bộ policy chiến lược một cách hard-coded
3. không nên assume local model host luôn active
4. không nên tự recovery mù nếu chưa có control authority
5. không nên là nơi ghi billing truth cuối cùng

---

# VII. Redesign recommendations

## 7.1. Reduce backend pool to valid canonical choices
Thay vì giữ nguyên list cũ, nên chuyển sang pool theo role.

### Giai đoạn tạm thời
Ưu tiên pool nhẹ hơn:
- `http://localhost:8000` (temporary stabilization path)
- `http://100.89.201.7:8000` (remote executor path)

### Không nên đưa `8005` vào pool mặc định ngay
cho tới khi quyết định rõ:
- `8005` còn phù hợp không
- có nên chạy local execution trên home node không

## 7.2. Make hedge policy configurable
Hiện `HEDGE_REQUESTS_ENABLED = True` và `HEDGE_DELAY_SECONDS = 0.35` là cứng.
Nên đưa thành config/control state:
- enable/disable hedge
- hedge only remote-first
- hedge only on latency class
- safe mode: no hedge

## 7.3. Remove blind auto-recovery by default
`trigger_auto_recovery(ticket)` nên bị hạ xuống:
- log + alert first
- recovery only when explicitly enabled by control plane

## 7.4. Add runtime proof endpoints
Nên thêm:
- `/health`
- `/runtime-state`
- `/backend-pool`
- `/policy`
- `/build-proof`

để chứng minh proxy đang route theo cái gì.

## 7.5. Add control-plane integration
8015 nên đọc state từ control backend/Redis thay vì hard-code:
- enabled backends
- safe mode
- preferred primary
- hedge enable
- maintenance flags

---

# VIII. Practical recommendation for current phase

## For current recovery direction
### Recommendation
**Không dùng 8015 làm bước đầu tiên để khôi phục chat.**

### Thay vào đó
1. tạm ổn định WordPress qua `8000/api/chat`
2. audit local Ollama / local heavy path
3. đánh giá lại `8005`
4. rồi mới refactor `8015`

## Why
Vì 8015 hiện hữu ích, nhưng đang gắn chặt vào topology cũ.
Nếu bật lại ngay, nó có thể:
- khôi phục path cũ
- nhưng cũng kéo theo complexity cũ
- và làm khó việc phase hóa kiến trúc mới

---

# IX. Final decision stance

## TTAiSimpleProxy có nên bị bỏ hẳn không?
### Không.
Nó vẫn có giá trị kiến trúc rõ ràng.

## TTAiSimpleProxy có nên bật lại nguyên trạng không?
### Cũng không.

## TTAiSimpleProxy nên làm gì tiếp theo?
### Được giữ lại và tái thiết kế thành:
- lightweight routing front door
- controlled, observable, policy-aware
- không phụ thuộc cứng vào local-heavy assumptions

---

# X. Phase guidance

## Phase hiện tại
- evaluate and redesign proxy role
- do not treat “service ON” as success

## Phase kế tiếp
- decide canonical backend pool
- decide whether `8005` remains in pool
- decide whether WordPress should temporarily bypass 8015

## Phase sau nữa
- restore/refactor 8015 under control-plane architecture

---

# XI. Recommended next documents / actions

1. `TTAi_SIMPLE_PROXY_CANONICAL_ROLE_2026-04-10.md`
2. `TTAi_SIMPLE_PROXY_BACKEND_POOL_REDESIGN_2026-04-10.md`
3. `TTAi_SIMPLE_PROXY_SAFE_RESTORE_PLAN_2026-04-10.md`

Nếu cần thao tác thực tế sau đó, mới bước sang phase restore có kiểm soát.
