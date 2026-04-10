# TTAi Home Node Service Pressure Audit — 2026-04-10

## Scope
Audit node `vannt-home-zq` / `vannt-home-pc` to identify:
- service nào đang chạy thực sự
- service nào đang giữ RAM/CPU đáng kể
- service nào có giá trị vận hành hiện tại
- service nào nên giữ / dừng / chuyển / chỉ bật khi cần

---

# I. Executive summary

Home node hiện đang gánh cùng lúc nhiều service nền liên quan đến TTAi:
- FastAPI account/control backend
- RAG service
- CLI Proxy
- Control Dashboard collector
- Ollama local service

### Kết luận nhanh
1. **Service nặng nhất hiện tại là `TTAiRagService`**
   - WS khoảng **432 MB**
   - PM khoảng **1.02 GB**
   - lắng nghe port **8075**
   - đây là mức dùng tài nguyên đáng kể nhưng vẫn ở ngưỡng chấp nhận được nếu thật sự đang phục vụ memory path / benchmark / shadow runtime.

2. **Ollama trên home node là gánh nặng kiến trúc đáng nghi hơn RAG**
   - có 2 process `ollama.exe`
   - PM xấp xỉ **~1 GB** mỗi process view
   - home node là máy yếu, không nên là nơi giữ local model runtime thường trực nếu không thật sự cần.

3. **FastAPI 8000 + CLI Proxy + ControlDashboard đều khá nhẹ**
   - FastAPI 8000: WS ~73 MB
   - CLI Proxy: WS ~25 MB
   - Control Dashboard: WS ~15 MB
   - ba service này không phải thủ phạm chính làm máy nặng.

4. **Vấn đề chiến lược hiện tại không phải chỉ là “RAM cao”**
   - mà là **home node đang gánh sai loại service**.
   - node này phù hợp hơn với role control/account/coordination hơn là inference/model hosting.

---

# II. Verified runtime listeners

## Listening ports
- `8000` → PID `10416` → FastAPI backend
- `8075` → PID `14244` → RAG service
- `8090` → PID `5712` → Control Dashboard collector
- `8317` → PID `5792` → CLI Proxy

## Not listening / currently off
- `8005` → OFF
- `8013` → OFF
- `8015` → OFF

---

# III. Service-to-process mapping

| Service | PID | Listener | Working Set | Private Memory | Assessment |
|---|---:|---|---:|---:|---|
| `TTAiFastAPI8000` | 10416 | 8000 | ~73 MB | ~63 MB | Nhẹ, giữ lại |
| `TTAiRagService` | 14244 | 8075 | ~432 MB | ~1.02 GB | Nặng vừa, cần quyết định role |
| `TTAiControlDashboard` | 5712 | 8090 | ~15 MB | ~50 MB | Rất nhẹ, nhưng cần đánh giá giá trị thật |
| `TTAiCLIProxy` | 5792 | 8317 | ~25 MB | ~62 MB | Nhẹ, hữu ích |
| `OllamaServe` / `ollama.exe` | 7928, 9372 | n/a | ~97 MB + ~28 MB WS | ~1.0 GB + ~0.97 GB PM | Gánh nặng đáng kể, không nên giữ nếu home node không chạy model |

> Lưu ý: `Working Set` phản ánh RAM đang resident; `Private Memory` cho thấy footprint logic có thể lớn hơn. Với Ollama và RAG, PM cao đáng quan tâm hơn nhìn thoáng qua WS.

---

# IV. Detailed assessment by service

## 1. `TTAiFastAPI8000`
### Role
- control-plane backend
- account/API backend
- portal/admin/auth/usage/quota/billing
- hiện cũng đang chứa hybrid endpoints cũ

### Resource impact
- thấp

### Operational value
- cao

### Recommendation
- **KEEP on home node**

### Notes
- Đây là service đúng vai trò nhất cho home node.
- Về lâu dài nên giảm hybrid execution logic khỏi đây, nhưng không nên dừng.

---

## 2. `TTAiRagService`
### Role
- RAG-V2 compatibility/memory backend
- port 8075
- hiện là backend shadow/compatibility surface đã được harden gần đây

### Resource impact
- trung bình đến cao
- ~432 MB resident RAM là có thể chấp nhận được
- PM ~1 GB cho thấy workload/bibliography vector/embedding stack không hề nhỏ

### Operational value
- cao nếu đang dùng cho:
  - memory benchmarks
n  - shadow challenger
  - future memory productization
- thấp nếu chưa có request thật hoặc chưa cần chạy 24/7

### If move to `vannt-home-pc`
#### Pros
- giảm áp lực cho `vannt-home-zq`
- tách memory service khỏi account/control backend
- phù hợp nếu `vannt-home-pc` là máy chuyên nền hơn

#### Risks
1. **Network hop tăng thêm**
   - nếu `memory_search` hoặc future APIs cần local low-latency, sẽ tăng latency
2. **Service coupling**
   - cần cập nhật callers nào đang trỏ `8075`
3. **Operational complexity tăng**
   - thêm 1 node phải theo dõi
4. **Nếu `vannt-home-pc` không ổn định hoặc chậm I/O**
   - memory recall có thể tệ hơn

#### Conclusion
- **Có thể chuyển**, không phải blocker lớn về kỹ thuật
- nhưng chỉ nên chuyển nếu mục tiêu là **giảm tải home-zq** và `vannt-home-pc` đủ ổn định
- nếu footprint ~432 MB WS là chấp nhận được và RAG cần chạy liên tục, **có thể tạm giữ lại**

### Recommendation
- **KEEP for now, but mark as MOVE-CANDIDATE**

---

## 3. `TTAiControlDashboard`
### Role
- collector/control dashboard service
- lắng nghe 8090

### Resource impact
- rất nhẹ

### Operational value
- hiện chưa rõ cao hay thấp
- WordPress plugin có `TTAI_CONTROL_API` default là `http://localhost:8090`
- nghĩa là service này có thể vẫn là dependency cho model management/UI control phía WordPress

### Risks if remove
- có thể làm hỏng các hành vi plugin liên quan model list/select
- có thể làm mất một lớp collector cũ mà chưa chuyển sang 8000

### Recommendation
- **KEEP for now until dependency trace is complete**
- không phải ưu tiên dừng vì nó rất nhẹ

---

## 4. `TTAiCLIProxy`
### Role
- cloud/CLI provider bridge
- port 8317

### Resource impact
- nhẹ

### Operational value
- cao
- đang là một phần quan trọng trong fallback/cloud strategy

### Recommendation
- **KEEP**

---

## 5. `OllamaServe` / local Ollama
### Role
- local model hosting

### Resource impact
- đáng kể đối với home node yếu
- khả năng gây:
  - tăng RAM nền
  - warm model pressure
  - disk I/O
  - CPU spikes
  - overall sluggishness

### Strategic mismatch
- home node **không nên** là nơi chạy model inference nặng thường trực
- remote node `vannt-work-op` đang có:
  - `qwen3-vl:8b`
  - `gemma3:12b`
  - `deepseek-r1:8b`
  - `gemma3:4b`
- remote node phù hợp hơn hẳn cho inference hosting

### If stop Ollama on home node
#### Benefits
- giảm tải rõ rệt
- giải phóng RAM/CPU nền
- giảm contention với FastAPI / browser / WordPress / tooling

#### Impact
1. các route local-only inference sẽ mất
2. endpoint `/api/ollama/*` trên 8000 có thể không còn meaningful local path
3. nếu hybrid logic đang assume local model available, cần update policy/fallback

### Conclusion
- **Đây là candidate số 1 để bỏ khỏi home node**
- về kiến trúc, home node nên giữ role control/account, không nên là inference host

### Recommendation
- **STOP / DISABLE on home node**, sau khi xác minh không còn critical caller cần local Ollama

---

# V. WordPress / plugin path implications

## Current known path
- browser → `chat.tuetue.vn/wp-admin/admin-ajax.php`
- WordPress plugin default chat target → `http://host.docker.internal:8015/api/chat`
- `8015` currently OFF

## Important consequence
Vấn đề WordPress chat hiện tại **không phải do FastAPI 8000 nặng**.
Khả năng cao hơn là:
- plugin đang forward vào target không tồn tại hoặc sai role
- AJAX layer vẫn thành công 200 OK nhưng backend inside plugin fail

## Optimization implication
Không nên vội kết luận “bật lại 8015 là xong”.
Cần trước tiên chốt:
- WordPress có thật sự đang dùng default `8015` không
- hay đang dùng `ttai_chat_api_endpoint` custom
- nếu dùng `8015`, kiến trúc mới có còn nên giữ 8015 trên home node không

---

# VI. Keep / Stop / Move / On-demand recommendations

## KEEP on `vannt-home-zq`
- `TTAiFastAPI8000`
- `TTAiCLIProxy`
- `TTAiControlDashboard` (tạm thời)

## KEEP for now, MOVE-CANDIDATE
- `TTAiRagService`

## STOP / DISABLE candidate
- `OllamaServe`

## ON-DEMAND ONLY
- future `8005`
- future `8013`
- future `8015`

---

# VII. Strategic node role proposal

## `vannt-home-zq`
### Proposed role
- Control plane
- Account/API backend
- Portal/admin
- Lightweight coordination
- Optional memory service (temporary)

### Not ideal for
- local model hosting
- heavy hybrid execution
- warm model pool

## `vannt-work-op`
### Proposed role
- Main inference host
- remote model executor
- heavy model hosting
- future hybrid execution runtime

## Optional `vannt-home-pc`
### Proposed role
- secondary infra/support node
- potential RAG hosting candidate
- backups / support services / detached workloads

---

# VIII. Recommendation order

## Immediate
1. Xác minh dependency thật của local Ollama
2. Xác minh WordPress target endpoint thật
3. Audit whether `TTAiControlDashboard` is still required by active plugin path

## Near-term
4. Stop/disable local Ollama on home node if no critical dependency
5. Keep RAG on home temporarily unless pressure becomes visible
6. Decide whether RAG should move to `vannt-home-pc`

## Medium-term
7. Rebuild hybrid path so home node no longer needs local model runtime
8. Shift inference role toward `vannt-work-op`

---

# IX. Final recommendation

## Strong recommendation
- **Do not add more always-on hybrid services to home node yet**
- **Do not restore 8005/8015 blindly on home node**
- **First remove or de-emphasize local Ollama**
- **Keep FastAPI + CLIProxy as the core lightweight base**
- **Treat RAG as optional-medium load, acceptable for now, movable later**

## Practical interpretation
Nếu chỉ chọn một thứ để làm máy nhẹ đi rõ nhất,
**ưu tiên số 1 là xem xét bỏ Ollama khỏi home node**.

Nếu chỉ chọn một thứ cần phân tích thêm trước khi di chuyển,
**ưu tiên số 2 là RAG 8075**.

Nếu chỉ chọn một thứ không cần lo ngay,
**Control Dashboard 8090** gần như không đáng kể về tài nguyên.
