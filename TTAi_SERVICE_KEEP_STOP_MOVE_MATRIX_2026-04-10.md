# TTAi Service Keep / Stop / Move Matrix — 2026-04-10

## Mục tiêu
Ra quyết định ngắn gọn, rõ ràng cho từng service đang hoặc sẽ tham gia hệ TTAi trên home node.

---

# I. Decision matrix

| Service | Current Node | Current State | Resource Pressure | Business Value | Decision | Rationale |
|---|---|---|---|---|---|---|
| `TTAiFastAPI8000` | home-zq | Running | Low | Very High | **KEEP** | Core account/control/API backend |
| `TTAiCLIProxy` | home-zq | Running | Low | High | **KEEP** | Lightweight cloud/provider bridge |
| `TTAiControlDashboard` | home-zq | Running | Very Low | Medium/Unknown | **KEEP (temporary)** | Very light, may still be plugin dependency |
| `TTAiRagService` | home-zq | Running | Medium | High | **KEEP now / MOVE later candidate** | Useful, but heavier than core backend |
| `OllamaServe` | home-zq | Running | High | Low on this node | **STOP candidate** | Wrong workload for weak node |
| `8005` hybrid runtime | home-zq | Off | Would add load | Medium/High | **ON-DEMAND only** | Do not restore blindly on home |
| `8013` debug runtime | home-zq | Off | Would add load | Low | **DO NOT RESTORE now** | Debug path only |
| `8015` simple proxy | home-zq | Off | Low/Medium | High if used | **RESTORE only after path decision** | Must not come back without canonical role |
| remote FastAPI 8000 | work-op | Running | Appropriate there | High | **KEEP / EXPAND role** | Better inference host |

---

# II. Specific answers to current questions

## 1. RAG 8075 có chuyển sang `vannt-home-pc` được không?
### Short answer
- **Có thể chuyển**
- **Không có blocker kỹ thuật lớn**
- nhưng **không bắt buộc phải chuyển ngay** vì footprint hiện tại tuy đáng kể nhưng chưa phải thứ sai vai trò nhất trên home node

### Best interpretation
- Nếu cần giảm tải dần, RAG là **move candidate hợp lý**
- Nhưng nếu chỉ muốn giảm máy chậm nhanh nhất, **ưu tiên dừng Ollama trước**

## 2. Các python.exe 50–70 MB có nên bỏ không?
### Mapping likely
- ~73 MB = FastAPI8000 → **giữ**
- ~50 MB = ControlDashboard → **giữ tạm**
- ~25 MB = CLI Proxy → **giữ**

### Conclusion
- **Không nên bỏ chỉ vì nhìn thấy python.exe**
- Cần đánh giá theo vai trò; các process này khá nhẹ và có ích

## 3. Ollama trên home node có nên bỏ không?
### Short answer
- **Có, đây là ứng viên bỏ mạnh nhất**
- miễn là xác minh current callers không còn phụ thuộc local Ollama path

### Why
- home node yếu
- inference nặng nên đẩy sang `vannt-work-op`
- local Ollama trên home đi ngược kiến trúc mới

## 4. Plugin WordPress đang forward sai vai trò / target không phù hợp?
### Short answer
- **Rất có khả năng đúng**
- browser path OK, backend target likely broken/misaligned
- cần chốt target thực tế rồi mới quyết định restore 8015 hay đổi sang 8000/remote path

---

# III. Recommended action classes

## KEEP
### Services
- `TTAiFastAPI8000`
- `TTAiCLIProxy`

### Why
- low footprint
- high platform value
- đúng role trên home node

## KEEP TEMPORARILY
### Services
- `TTAiControlDashboard`
- `TTAiRagService`

### Why
- dashboard: quá nhẹ để phải lo ngay
- RAG: hơi nặng nhưng vẫn có giá trị rõ và không phải thứ lệch vai trò nhất

## STOP CANDIDATE
### Services
- `OllamaServe`

### Why
- load không phù hợp máy
- inference hosting nên dời khỏi home node

## RESTORE LATER / ON-DEMAND
### Services
- `8005`
- `8015`

### Why
- chỉ restore sau khi chốt canonical path
- không biến home node thành execution-heavy node thêm lần nữa

## DO NOT RESTORE
### Services
- `8013`

### Why
- debug runtime, giá trị thấp hơn load risk

---

# IV. Migration preference

## Preferred target roles
### home-zq
- control/account/API backend
- portal/admin
- CLI/cloud bridge
- optional memory temporarily

### work-op
- inference host
- heavy models
- hybrid execution role

### home-pc
- optional support node
- possible future RAG relocation
- backups / side workloads / detached services

---

# V. Decision priority

## Priority 1
- audit and remove local Ollama from home node if safe

## Priority 2
- confirm real WordPress backend target

## Priority 3
- decide if RAG stays or moves later

## Priority 4
- only then redesign hybrid restore path

---

# VI. Operational stance

Do **not** optimize by killing random Python processes.
Optimize by correcting node roles.

The main principle is:
- keep control plane on home
- keep heavy inference off home
- keep memory where it is acceptable until a better host is justified
