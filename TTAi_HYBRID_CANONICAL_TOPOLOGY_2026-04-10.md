# TTAi Hybrid Canonical Topology — 2026-04-10

## Mục tiêu
Chốt topology thật của hệ TTAi Super Model Hybrid, xác định:
- port nào đang chạy
- port nào nên chạy
- vai trò chính của từng port
- entry path thật từ WordPress/chat.tuetue.vn
- canonical runtime path cho hybrid inference

---

# I. Topology hiện tại (từ audit)

## 1.1. Ports hiện tại (verified 2026-04-10 22:47)
| Port | Service | Vai trò | Trạng thái hiện tại |
|------|---------|---------|---------------------|
| **8000** | FastAPI | control-plane + account/API backend + portal + admin + hybrid endpoints | ✅ Đang chạy (NSSM service `TTAiFastAPI8000`) |
| **8005** | `ttai_hybrid_v2_fixed.py` | local hybrid execution engine | ❌ Tắt (không có process) |
| **8013** | TTAi Debug | debug/experimental runtime | ❌ Tắt (không có process) |
| **8015** | `simple_proxy.py` / TTAiSimpleProxy | load balancer / routing front door | ❌ Tắt (không có process) |
| **8075** | RAG-V2 | memory / retrieval backend | ✅ Đang chạy (Python process PID 14244, RAG-V2 backend) |
| **8090** | collector/control dashboard | monitoring/control surface | ❌ Không có process |
| **100.89.201.7:8000** | remote FastAPI | remote execution engine (vannt-work-op) | ✅ Đang chạy (có 4 model: qwen3-vl:8b, gemma3:12b, deepseek-r1:8b, gemma3:4b) |

## 1.2. WordPress / chat.tuetue.vn entry path
### Xác minh từ plugin code + WordPress screenshot
WordPress plugin `ttai-chat-plugin` (version 1.1.7) có logic:
1. `get_option('ttai_chat_api_endpoint')` từ WordPress database
2. Nếu không có, lấy từ env `TTAI_CHAT_API`
3. Nếu không có, default là `'http://host.docker.internal:8015/api/chat'`

### Những gì đã xác minh từ screenshot WordPress
- Frontend chat tại `https://chat.tuetue.vn` gửi request tới `https://chat.tuetue.vn/wp-admin/admin-ajax.php`
- Status code trả về tại lớp WordPress AJAX là `200 OK`
- Plugin active:
  - `TTAi Chat Interface` v1.1.7
  - `TTAi Dashboard Control` v0.1.0
- UI chat vẫn báo lỗi: `Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.`

### Kết luận hiện tại về entry path
- **Browser-facing entry path**: `chat.tuetue.vn` → `wp-admin/admin-ajax.php`
- **Backend target phía sau WordPress**: chưa chốt tuyệt đối vì cần payload/response hoặc settings plugin, nhưng theo plugin code thì default target là `http://host.docker.internal:8015/api/chat`
- Vì `8015` đang tắt, đây là giả thuyết mạnh nhất cho nguyên nhân lỗi hiện tại.

### FastAPI 8000 có endpoint `/api/chat`
Endpoint tồn tại, nhưng WordPress hiện chưa được chứng minh là đang gọi trực tiếp endpoint này.

## 1.3. CLI Proxy integration
- `127.0.0.1:8317` = CLI Proxy internal endpoint
- `CLI_PROXY_API_KEY=cliproxy-dev-token` trong service config
- FastAPI 8000 có thể gọi CLI Proxy cho cloud inference

---

# II. Topology đề xuất (canonical)

## 2.1. Nguyên tắc
- Một port, một vai trò chính
- Không để business logic lẫn với execution logic
- Control plane tách khỏi runtime execution
- Entry path phải rõ ràng

## 2.2. Canonical roles

| Port | Role | Responsibility | Dependencies |
|------|------|----------------|--------------|
| **8000** | **Control/Account Backend** | auth, API keys, usage, quota, billing, admin APIs, portal UI | PostgreSQL, Redis, CLI Proxy |
| **8015** | **Hybrid Routing Front Door** | request routing, load balancing, failover, hedging, trace propagation | 8005, remote 8000, CLI Proxy |
| **8005** | **Local Hybrid Execution Engine** | local model execution, fallback logic, provider selection, usage truth recording | local Ollama, CLI Proxy |
| **remote 8000** | **Remote Execution Engine** | remote model execution (vannt-work-op) | remote Ollama, Tailscale |
| **8075** | **Memory Backend** | RAG-V2 retrieval, memory namespace management | vector DB, embedding service |
| **WordPress** | **Customer Surface** | public chat UI, landing, docs, marketing | gọi 8015 hoặc 8000 |

## 2.3. Canonical request flow
```
WordPress/chat.tuetue.vn
        ↓
    [8015] Hybrid Routing Front Door
        ↓ (policy: 60/30/10)
    [8005] Local Hybrid Execution Engine
        ↓ (fallback logic)
    [local Ollama] OR [remote 8000] OR [CLI Proxy]
        ↓
    Response → 8015 → WordPress
        ↓
    [8000] ghi usage truth (từ trace)
```

## 2.4. Control flow
```
Control Dashboard (UI)
        ↓
    [8000] Control APIs
        ↓
    Policy update → 8015
    Node on/off → 8005 / remote 8000
    Provider on/off → CLI Proxy config
```

---

# III. Xác minh topology thật

## 3.1. Đã trả lời (Phase 0 findings)
1. WordPress plugin hiện gọi port nào? → **Chưa biết chắc, default là 8015 nhưng 8015 tắt. Cần kiểm tra WordPress admin.**
2. `8015` có phải canonical entry cho hybrid không? → **Theo design yes, nhưng hiện tắt.**
3. `8005` có phải canonical execution runtime không? → **Theo design yes, nhưng hiện tắt.**
4. Remote runtime (`100.89.201.7:8000`) còn sống không? → **✅ YES, đang chạy với 4 model.**
5. `8000` hiện có hybrid endpoints không? Nếu có, nên giữ hay chuyển? → **Có `/api/chat` và `/api/hybrid/chat`. Nên chuyển sang 8005/8015 trong Phase 3.**

## 3.2. Kiểm tra WordPress plugin config
Cần đọc:
- `wordpress-chat-plugin.php`
- plugin settings trong WordPress admin
- network trace từ browser DevTools

## 3.3. Kiểm tra service status
```powershell
# FastAPI 8000
Get-Service -Name TTAiFastAPI8000

# RAG 8075
Get-Service -Name RAGService8075

# Các service khác (nếu có)
Get-Process -Name python | Where-Object {$_.CommandLine -match "8005|8013|8015"}
```

## 3.4. Kiểm tra remote node
```powershell
# Kiểm tra kết nối Tailscale
ping 100.89.201.7

# Kiểm tra port 8000 remote
Test-NetConnection -ComputerName 100.89.201.7 -Port 8000
```

---

# IV. Gap giữa topology hiện tại và canonical

## 4.1. Gaps cần đóng
| Gap | Mức độ | Hành động |
|-----|--------|-----------|
| WordPress gọi 8000 thay vì 8015 | Cao | Cần xác minh và điều chỉnh |
| 8015 tắt | Cao | Khôi phục với vai trò rõ |
| 8005 tắt | Cao | Khôi phục với config mới |
| Remote node không rõ trạng thái | Trung | Kiểm tra và xác nhận |
| 8000 đang gánh hybrid logic | Cao | Tách hybrid endpoints ra 8005/8015 |
| Control dashboard không điều hành được node/model | Cao | Thêm control APIs |

## 4.2. Ưu tiên đóng gap
1. Xác minh WordPress entry path
2. Khôi phục 8015 với vai trò routing front door
3. Khôi phục 8005 với execution role
4. Xác nhận remote node
5. Tách hybrid logic khỏi 8000

---

# V. Decision log

## 5.1. Decisions đã chốt
1. **8000** = control-plane + account/API backend (giữ)
2. **8015** = hybrid routing front door (khôi phục)
3. **8005** = local hybrid execution engine (khôi phục)
4. **8075** = memory backend (giữ)
5. **WordPress** = customer surface only (không business logic)

## 5.2. Decisions cần xác minh
1. WordPress hiện gọi port nào? → **TODO (cần WordPress admin access)**
2. Remote node còn sống? → **✅ YES, đang chạy với 4 model**
3. 8000 có hybrid endpoints nào cần chuyển? → **Có `/api/chat` và `/api/hybrid/chat`. Nên chuyển trong Phase 3.**

## 5.3. Timeline
- **Ngay**: xác minh WordPress path
- **Ngay**: kiểm tra service status
- **Sớm**: khôi phục 8015
- **Sớm**: khôi phục 8005
- **Sau**: tách hybrid logic khỏi 8000

---

# VI. Next steps

## 6.1. Immediate (Phase 0)
1. Đọc WordPress plugin config
2. Kiểm tra service status (8000, 8075, 8005, 8015)
3. Kiểm tra remote node
4. Cập nhật topology này với findings thật

## 6.2. Short-term (Phase 1)
1. Khôi phục 8015 với canonical role
2. Khôi phục 8005 với execution role
3. Benchmark path: WordPress → 8015 → 8005 → local/remote
4. Điều chỉnh WordPress plugin nếu cần

## 6.3. Medium-term (Phase 2)
1. Tách hybrid endpoints khỏi 8000
2. Thêm control APIs cho dashboard
3. Cập nhật config resource-aware

---

# VII. References

- `TTAi_HYBRID_RUNTIME_TRACE_MAP.md`
- `TTAi_SUPER_MODEL_HYBRID_ARCHITECTURE.md`
- `memory/2026-04-02.md` (runtime trace từng hoạt động)
- `memory/2026-03-30.md` (remote node setup)
- WordPress plugin files

---

**Lưu ý:** Tài liệu này là canonical truth cho topology TTAi Hybrid.  
Mọi thay đổi về port/service role phải được cập nhật ở đây.
