# TTAi Hybrid Strategic Recovery and Phased Rebuild — 2026-04-10

## Mục tiêu tài liệu
Biến các nhận định rời rạc về TTAi Super Model Hybrid thành một hướng đi chiến lược có thể hành động được:
1. Khôi phục hệ thống theo đúng nghĩa chiến lược, không chỉ bật service.
2. Điều chỉnh và nâng cấp theo phase rõ ràng.
3. Tái cấu trúc dần thành hệ module hóa có thể điều khiển thật qua Control Dashboard.

---

# I. Kết luận chiến lược cốt lõi

## 1. Hệ thống không thiếu thành phần, đang thiếu kiến trúc vận hành chuẩn
TTAi hiện đã có gần đủ các mảnh quan trọng:
- Hybrid execution runtimes
- Load balancer / proxy layer
- FastAPI account/control backend
- WordPress customer surface
- CLI Proxy cloud access
- RAG-V2 memory backend
- Control dashboard surface

Vấn đề chính không phải là “chưa có hệ”, mà là:
- topology thật chưa được chốt thành canonical truth
- control dashboard chưa có đủ quyền điều hành thật
- execution, policy, availability và business logic còn lẫn nhau
- nhiều runtime path từng hoạt động nhưng chưa được hợp nhất thành một mô hình vận hành chuẩn

## 2. Khôi phục đúng nghĩa = strategic recovery
Khôi phục hệ không nên hiểu là:
- bật lại 8005, 8013, 8015 rồi tiếp tục chạy như cũ

Khôi phục đúng nên hiểu là:
- kiểm tra topology thật
- xác nhận vai trò từng port/service
- phục hồi theo thứ tự chiến lược
- loại bỏ assumptions cũ không còn hợp với tài nguyên hiện tại
- tái dựng hệ theo mô hình có thể nâng cấp dần lên platform core

## 3. TTAi Hybrid phải được nâng từ “một cụm service AI” thành “core platform”
Hệ này nên trở thành nền chính để:
- cấp token API
- bán account/chat usage
- điều phối local / remote / cloud inference
- cung cấp memory-enhanced AI bằng RAG-V2
- gắn lên OpenClaw và các client khác
- sau này mở sang customer-specific AI / project-specific memory

---

# II. Mục tiêu chiến lược dài hạn

## Strategic Goal A — Canonical Hybrid Core
Xây dựng một lõi hybrid inference có thể chứng minh được:
- ai nhận request
- ai chọn route
- ai thực thi model thật
- ai ghi usage truth
- ai chịu trách nhiệm fallback

## Strategic Goal B — Real Control Plane
Control Dashboard phải trở thành nơi điều hành thật:
- bật/tắt node
- bật/tắt model
- bật/tắt provider cloud
- đổi traffic policy
- force safe mode / local-only / remote-only / cloud-only
- xem health + active route + load state theo thời gian thực

## Strategic Goal C — Account + API + Memory Product Platform
TTAi không chỉ trả text.
TTAi cần trở thành:
- inference platform
- account platform
- memory platform

Trong đó RAG-V2 là lớp giá trị gia tăng chiến lược.

---

# III. Định nghĩa 3 lớp sản phẩm cốt lõi

## 1. Inference Layer
Chịu trách nhiệm:
- hybrid routing
- local/remote/cloud execution
- fallback
- latency/cost balancing
- provider/model truth

## 2. Platform Layer
Chịu trách nhiệm:
- auth
- API keys
- usage
- quota
- billing
- plans / packages
- admin/control APIs

## 3. Memory Layer
Chịu trách nhiệm:
- RAG-V2
- retrieval
- memory namespaces / datasets
- account/project customization
- premium product differentiation

**Nguyên tắc:** Không để 3 lớp này lẫn vai trò với nhau.

---

# IV. Nguyên tắc tái thiết kế

## Principle 1 — Một port, một vai trò chính
Đề xuất canonical roles:
- `8000` → control-plane + account/API backend
- `8015` → hybrid routing front door / proxy
- `8005` → local hybrid execution runtime
- `remote 8000` hoặc runtime tương đương → remote execution runtime
- `8075` → memory / RAG backend

## Principle 2 — Policy không được trộn với execution
Cần tách rõ:
- policy (60/30/10, priority, on/off)
- availability (health, warm, capacity)
- execution (gọi model thật)
- business/account logic (usage, quota, billing)

## Principle 3 — Resource-aware configuration
Không hard-code assumptions kiểu “local luôn có 3 model”.
Cấu hình phải phản ánh đúng tài nguyên thật:
- `vannt-home-pc` = lightweight local executor
- `vannt-work-op` = heavier dual-model executor
- cloud = overflow / premium path

## Principle 4 — Proofable runtime
Mỗi service quan trọng cần có:
- health endpoint
- runtime identity
- active backend/provider info
- build proof / version proof
- control state visibility

## Principle 5 — Dashboard phải có authority thật
Không chỉ xem trạng thái, mà phải điều hành được.

---

# V. Phase roadmap đề xuất

# Phase 0 — Strategic Recovery Baseline
## Mục tiêu
Không bật lại mù. Chốt lại sự thật của hệ trước đã.

## Deliverables
1. Canonical topology document
2. Runtime trace for real entry paths
3. Port/service ownership map
4. WordPress / chat.tuetue.vn active target map
5. Current control-dashboard capability gap list

## Câu hỏi phải trả lời xong trong Phase 0
- WordPress/chat hiện đang gọi port nào?
- `8015` có phải canonical entry cho hybrid không?
- `8005` có phải canonical execution runtime không?
- `8000` hiện nên giữ vai trò gì, bỏ vai trò gì?
- remote runtime hiện thực thi gì và gọi qua đâu?

## Output chiến lược
Sau phase này phải có một sơ đồ topology thật, không còn tranh cãi.

---

# Phase 1 — Controlled Recovery of Hybrid Runtime
## Mục tiêu
Khôi phục hybrid theo cách tối thiểu nhưng đúng vai trò.

## Phạm vi
- phục hồi `8015` như routing/proxy front door
- phục hồi `8005` như execution runtime local
- xác nhận remote execution path
- không đưa thêm logic business phức tạp vào runtime recovery

## Việc cần làm
1. Start lại các runtime cần thiết theo thứ tự
2. Benchmark lại từng path:
   - 8015 → 8005
   - 8015 → remote
   - direct 8005
   - direct 8000 nếu còn cần
3. Ghi lại latency, success rate, failure mode
4. Loại bỏ route/path thừa hoặc gây rối

## Nguyên tắc
Recovery trước, nhưng recovery phải tạo nền cho redesign.

---

# Phase 2 — Control Plane Hardening
## Mục tiêu
Biến Control Dashboard từ monitoring veneer thành control plane thật.

## Tính năng tối thiểu cần có
1. Node on/off
2. Model on/off
3. Provider on/off
4. Traffic weight editor
5. Safe modes:
   - local only
   - remote only
   - cloud only
   - balanced
6. Health + warm + capacity state
7. Active route / current backend visibility

## Tại sao phase này quan trọng
Không có control plane thật thì hybrid system sẽ luôn khó điều hành và khó mở rộng.

---

# Phase 3 — Platform Separation
## Mục tiêu
Tách rõ Platform Layer khỏi Inference Layer.

## Hướng tách
- `8000` giữ account/API/control/business logic
- hybrid runtime giữ execution truth
- usage/billing chỉ lấy truth từ execution layer + trace propagation

## Kết quả mong muốn
- dễ trace
- dễ billing
- dễ debug
- dễ benchmark
- dễ mở ra external API product

---

# Phase 4 — Memory Productization
## Mục tiêu
Đưa RAG-V2 thành capability sản phẩm thật, không chỉ là backend phụ.

## Hướng đi
- account-level memory
- project/org-ready memory namespace
- upload/index data flows
- retrieval controls
- premium feature packaging

## Giá trị chiến lược
Đây là lớp tạo khác biệt lớn nhất so với AI API thường.

---

# Phase 5 — Commercial Platform Readiness
## Mục tiêu
Chuyển từ hệ nội bộ mạnh sang nền có thể bán ra.

## Thành phần
- plans/packages
- token metering chuẩn
- account dashboard rõ ràng
- memory-enabled premium offers
- ops visibility
- SLA-ish internal benchmarks

---

# VI. Đề xuất khôi phục theo hướng “nâng cấp chiến lược”

## Bước 1 — Chốt canonical topology trước khi bật hàng loạt
Đây là bước bắt buộc.
Nếu không, chỉ cần bật lại service là hệ sẽ quay về trạng thái “nhiều lớp chạy nhưng không ai là sự thật”.

## Bước 2 — Khôi phục theo xương sống tối thiểu
Thứ tự đề xuất:
1. `8005` execution runtime
2. remote execution runtime
3. `8015` routing front door
4. xác nhận WordPress/chat entry path
5. chỉ giữ `8000` cho control/account/backend role

## Bước 3 — Loại bỏ assumptions cũ khỏi config
Ví dụ:
- local machine không phải nơi giữ nhiều model nặng
- remote node mới là nơi gánh reasoning nặng hơn
- dashboard phải phản ánh đúng điều đó

## Bước 4 — Tạo benchmark chuẩn cho từng path
Không benchmark chung chung.
Benchmark theo từng tuyến thực tế.

## Bước 5 — Biến dashboard thành nơi điều hành thật
Nếu control plane không điều hành được, scale platform sẽ luôn đau.

---

# VII. Hướng module hóa dần qua Control Dashboard

## Module A — Runtime Module
- local executor
- remote executor
- cloud providers
- routing front door

## Module B — Policy Module
- traffic weights
- failover policy
- route preference
- safety mode

## Module C — Business Module
- auth
- key issuance
- usage/quota
- billing/limits

## Module D — Memory Module
- RAG-V2 retrieval
- memory namespace management
- indexing / dataset ops
- memory-enhanced plans

## Module E — Observability Module
- health
- latency
- route choice
- active model/provider
- error heatmap
- build/runtime proofs

**Mục tiêu:** mỗi module có thể điều khiển, thay thế, hoặc mở rộng mà không phá toàn bộ hệ.

---

# VIII. Đề xuất ưu tiên thực thi ngay

## Ưu tiên 1 — Chốt tài liệu canonical topology
Không có nó thì mọi recovery đều mơ hồ.

## Ưu tiên 2 — Controlled recovery cho 8005/8015/remote path
Khôi phục đúng xương sống hybrid.

## Ưu tiên 3 — Dashboard gap analysis
Xem thiếu gì để thành control plane thật.

## Ưu tiên 4 — Trace WordPress/chat.tuetue.vn entry path
Đây là bước cực quan trọng nếu sản phẩm thật sẽ dùng path này.

## Ưu tiên 5 — Strategic benchmark pack
Làm benchmark theo path + cost + latency + failover + memory value.

---

# IX. Kết luận cuối

TTAi Super Model Hybrid không nên được sửa như một cụm bug.
Nó nên được tái cấu trúc như một nền tảng AI core.

Khôi phục hệ thống lần này nên được hiểu là:
- phục hồi đúng xương sống runtime
- xác lập topology chuẩn
- tách control plane khỏi execution
- chuẩn hóa đường phát triển thành platform API/account/memory

Nếu làm đúng, TTAi sẽ không chỉ “chạy lại”, mà sẽ tiến gần hơn tới mục tiêu ban đầu:
- một lõi AI hybrid thực dụng
- có thể bán API/token/account
- có thể gắn memory cá nhân hóa
- có thể vận hành bằng dashboard như một platform thực thụ
