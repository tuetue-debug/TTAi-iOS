# TTAi Hybrid Phase 0 Execution Checklist — 2026-04-10

## Mục tiêu
Checklist thực thi cho Phase 0 — Strategic Recovery Baseline.
Mọi bước phải được đánh dấu hoàn thành trước khi chuyển sang Phase 1.

---

# I. Phase 0 Overview

## 1.1. Mục tiêu Phase 0
Không bật lại service mù. Chốt lại sự thật của hệ trước đã.

## 1.2. Deliverables Phase 0
1. ✅ Canonical topology document
2. ✅ Runtime trace for real entry paths
3. ✅ Port/service ownership map
4. ✅ WordPress / chat.tuetue.vn active target map
5. ✅ Current control-dashboard capability gap list

## 1.3. Câu hỏi phải trả lời xong trong Phase 0
- [~] WordPress/chat hiện đang gọi port nào? (đã biết browser → admin-ajax.php; backend target cuối vẫn cần chốt từ settings/payload)
- [ ] `8015` có phải canonical entry cho hybrid không?
- [ ] `8005` có phải canonical execution runtime không?
- [ ] `8000` hiện nên giữ vai trò gì, bỏ vai trò gì?
- [ ] Remote runtime hiện thực thi gì và gọi qua đâu?

---

# II. Checklist thực thi

## 2.1. Kiểm tra service status hiện tại
### [ ] Task 1: Kiểm tra FastAPI 8000
```powershell
Get-Service -Name TTAiFastAPI8000
# Expected: Running
```

### [ ] Task 2: Kiểm tra RAG 8075
```powershell
Get-Service -Name RAGService8075
# Expected: Running
```

### [ ] Task 3: Kiểm tra các Python service khác
```powershell
Get-Process -Name python | Where-Object {$_.CommandLine -match "8005|8013|8015"} | Select-Object Id, CommandLine
# Expected: Có thể không có process nào (vì tắt)
```

### [ ] Task 4: Kiểm tra port listening
```powershell
netstat -ano | findstr ":8000 :8005 :8013 :8015 :8075"
# Expected: 8000 và 8075 đang listen
```

## 2.2. Xác minh WordPress entry path
### [ ] Task 5: Đọc WordPress plugin config
```bash
# Đọc file plugin chính
cat C:\Users\vannt-pc\.openclaw\workspace\wordpress-chat-plugin.php | findstr "localhost\|127.0.0.1\|8000\|8015\|8005"
```

### [ ] Task 6: Kiểm tra WordPress admin settings
1. Đăng nhập WordPress admin
2. Vào Settings → TTAi Chat Plugin
3. Ghi lại API endpoint URL
4. Chụp ảnh màn hình nếu cần

**Status:** Chưa có ảnh settings endpoint; mới có ảnh plugin list + network trace.

### [x] Task 7: Network trace từ browser
1. Mở chat.tuetue.vn trong Chrome/Firefox
2. Mở DevTools → Network tab
3. Gửi một tin nhắn test
4. Xem request đi đến đâu

**Finding:** Browser request đi tới `https://chat.tuetue.vn/wp-admin/admin-ajax.php` (status `200 OK`). Đây là AJAX bridge của WordPress, chưa phải backend hybrid cuối cùng.

### [ ] Task 8: Test direct endpoints
```powershell
# Test 8000
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"test"}'

# Test 8015 (nếu có)
curl -X POST http://localhost:8015/chat -H "Content-Type: application/json" -d '{"message":"test"}'

# Test 8005 (nếu có)
curl -X POST http://localhost:8005/chat -H "Content-Type: application/json" -d '{"message":"test"}'
```

## 2.3. Kiểm tra remote node
### [ ] Task 9: Kiểm tra Tailscale connectivity
```powershell
ping 100.89.201.7
# Expected: Reply from 100.89.201.7
```

### [ ] Task 10: Kiểm tra remote port 8000
```powershell
Test-NetConnection -ComputerName 100.89.201.7 -Port 8000
# Expected: TcpTestSucceeded: True
```

### [ ] Task 11: Test remote endpoint
```powershell
curl -X POST http://100.89.201.7:8000/chat -H "Content-Type: application/json" -d '{"message":"test remote"}'
```

## 2.4. Audit FastAPI 8000 endpoints
### [ ] Task 12: Liệt kê hybrid endpoints trong 8000
```bash
# Đọc main.py tìm các route hybrid
grep -n "@app.*chat\|@app.*complete\|@app.*hybrid" C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\main.py
```

### [ ] Task 13: Phân loại endpoints
Phân loại mỗi endpoint thuộc nhóm nào:
- Business/account endpoints (giữ lại)
- Hybrid execution endpoints (có thể chuyển sang 8005/8015)
- Admin/control endpoints (giữ lại)
- Portal endpoints (giữ lại)

## 2.5. Kiểm tra CLI Proxy integration
### [ ] Task 14: Kiểm tra CLI Proxy service
```powershell
Get-Service | Where-Object {$_.Name -match "cli.*proxy|openclaw"}
```

### [ ] Task 15: Kiểm tra CLI Proxy config trong 8000
```bash
# Tìm CLI_PROXY_API_KEY trong main.py hoặc env
grep -r "CLI_PROXY\|cliproxy" C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\
```

### [ ] Task 16: Test CLI Proxy endpoint
```powershell
curl http://127.0.0.1:8317/v1/health
# Expected: {"status":"ok"} hoặc tương tự
```

## 2.6. Document findings
### [ ] Task 17: Cập nhật canonical topology
Cập nhật `TTAi_HYBRID_CANONICAL_TOPOLOGY_2026-04-10.md` với:
- WordPress entry path thật
- Service status thật
- Remote node status
- Endpoints classification

### [ ] Task 18: Tạo runtime trace map
Vẽ sơ đồ request flow thật từ WordPress đến model execution.

### [ ] Task 19: Tạo gap summary
Tóm tắt gaps tìm thấy:
- WordPress gọi port nào?
- Hybrid endpoints nào đang ở 8000?
- Remote node có hoạt động không?
- CLI Proxy có hoạt động không?

---

# III. Decision points

## 3.1. Sau khi có findings
### Decision 1: WordPress entry path
- Nếu WordPress gọi `8000` → có nên chuyển sang `8015` không?
- Nếu WordPress gọi `8015` → `8015` có cần khôi phục không?
- Nếu WordPress gọi `8005` → `8005` có cần khôi phục không?

### Decision 2: Hybrid endpoints trong 8000
- Giữ lại hay chuyển sang 8005/8015?
- Nếu chuyển, timeline thế nào?

### Decision 3: Remote node
- Còn hoạt động không?
- Nếu không, có cần khôi phục không?
- Nếu có, vai trò trong topology là gì?

### Decision 4: CLI Proxy
- Có hoạt động không?
- Có cần tích hợp vào hybrid flow không?

## 3.2. Exit criteria Phase 0
Phase 0 chỉ kết thúc khi:
- [ ] Đã biết WordPress gọi port nào
- [ ] Đã biết service nào đang chạy/tắt
- [ ] Đã biết remote node status
- [ ] Đã phân loại được endpoints trong 8000
- [ ] Đã cập nhật canonical topology với truth
- [ ] Đã có quyết định rõ cho từng decision point

---

# IV. Risks and mitigation

## 4.1. Risk: WordPress đang gọi 8000 trực tiếp
- **Impact**: Khó chuyển sang 8015 mà không break user experience
- **Mitigation**: 
  1. Thêm proxy layer trong 8000 redirect sang 8015
  2. Hoặc update plugin config (cần WordPress admin access)

## 4.2. Risk: Remote node không hoạt động
- **Impact**: Mất 30% capacity trong 60/30/10 policy
- **Mitigation**:
  1. Khôi phục remote node
  2. Điều chỉnh policy weights tạm thời
  3. Ưu tiên khôi phục local runtime trước

## 4.3. Risk: 8000 có quá nhiều hybrid logic
- **Impact**: Khó tách mà không break hệ thống
- **Mitigation**:
  1. Phân loại endpoints
  2. Chuyển dần từng endpoint
  3. Giữ backward compatibility

## 4.4. Risk: Thiếu documentation cho existing flow
- **Impact**: Khó hiểu hệ đang chạy thế nào
- **Mitigation**:
  1. Trace thật từ WordPress
  2. Document từng bước
  3. Tạo sơ đồ flow

---

# V. Tools và commands reference

## 5.1. PowerShell commands
```powershell
# Service management
Get-Service -Name TTAiFastAPI8000
Start-Service -Name TTAiFastAPI8000
Stop-Service -Name TTAiFastAPI8000
Restart-Service -Name TTAiFastAPI8000

# Process management
Get-Process -Name python
Stop-Process -Id <PID> -Force

# Network
netstat -ano | findstr ":8000"
Test-NetConnection -ComputerName 100.89.201.7 -Port 8000
```

## 5.2. curl commands
```bash
# Test endpoints
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"test"}'
curl http://localhost:8000/health
curl http://localhost:8075/health
```

## 5.3. File locations
```
# FastAPI code
C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\

# WordPress plugin
C:\Users\vannt-pc\.openclaw\workspace\wordpress-chat-plugin.php

# Hybrid runtime
C:\Users\vannt-pc\.openclaw\workspace\ttai_hybrid_v2_fixed.py
C:\Users\vannt-pc\.openclaw\workspace\simple_proxy.py

# Service configs
C:\Windows\System32\config\systemprofile\AppData\Local\nssm\ (NSSM service configs)
```

---

# VI. Next phase readiness

## 6.1. Phase 1 sẽ bắt đầu khi
- [ ] Phase 0 checklist hoàn thành
- [ ] Canonical topology đã được cập nhật với truth
- [ ] Decision points đã có quyết định
- [ ] Có clear plan cho khôi phục 8015/8005

## 6.2. Phase 1 focus
- Khôi phục 8015 với vai trò routing front door
- Khôi phục 8005 với execution role
- Benchmark path thật
- Điều chỉnh WordPress plugin nếu cần

---

# VII. Changelog

## 2026-04-10
- Tạo checklist Phase 0
- Liệt kê tasks cần thực thi
- Xác định decision points
- Liệt kê risks và mitigation

---

**Lưu ý:** Mỗi task phải được đánh dấu hoàn thành với timestamp và người thực hiện.
