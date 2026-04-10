# TTAi Hybrid Control Plane Gap Analysis — 2026-04-10

## Mục tiêu
Phân tích gap giữa Control Dashboard hiện tại và một control plane thật sự có thể điều hành được hệ hybrid.

---

# I. Control Dashboard hiện tại

## 1.1. Tính năng đã có
Từ audit `control_dashboard/static/dashboard.js` và `main.py`:

### Monitoring
- Health status (service up/down)
- Usage summary (events, estimated spend)
- Billing summary
- Quota status
- API key list

### Auth
- Admin login
- Session management
- Token-based auth

### Basic control
- API key creation/revocation
- (Có thể có) một số admin actions

## 1.2. Architecture hiện tại
```
Dashboard UI (browser)
        ↓
    [8000] FastAPI control endpoints
        ↓
    Data: usage_truth, billing_store, api_key_store
```

**Nhận xét:** Dashboard hiện chủ yếu là **monitoring veneer**, không phải control plane thật.

---

# II. Yêu cầu của một control plane thật

## 2.1. Control plane phải điều hành được
### Runtime control
- Bật/tắt node (local, remote)
- Bật/tắt model (gemma3:4b, deepseek-r1:8b, ...)
- Bật/tắt provider (DeepSeek CLI Proxy, GPT CLI Proxy)
- Force safe modes (local-only, remote-only, cloud-only, balanced)

### Policy control
- Traffic weights (60/30/10)
- Failover policy
- Route preference
- Cost/latency trade-off settings

### Operational control
- Maintenance mode
- Drain traffic
- Force health check
- Clear caches / warm models

## 2.2. Visibility thật
### Real-time state
- Node health (up/down, latency, errors)
- Model warm status
- Active backend per request type
- Current traffic distribution
- Queue depth / concurrency

### Historical
- Route choice history
- Fallback events
- Cost per provider
- SLA-ish metrics

## 2.3. Proofability
- Runtime identity (build hash, version)
- Active config snapshot
- Control state audit log
- Who changed what, when

---

# III. Gap analysis

## 3.1. Gap lớn nhất: Không có authority thật
| Requirement | Hiện có | Gap |
|-------------|---------|-----|
| Node on/off | ❌ Không | Cao |
| Model on/off | ❌ Không | Cao |
| Provider on/off | ❌ Không | Cao |
| Traffic weights | ❌ Không | Cao |
| Safe modes | ❌ Không | Cao |
| Maintenance mode | ❌ Không | Cao |

## 3.2. Gap visibility
| Requirement | Hiện có | Gap |
|-------------|---------|-----|
| Real-time node health | ⚠️ Một phần | Trung |
| Model warm status | ❌ Không | Cao |
| Active backend visibility | ❌ Không | Cao |
| Traffic distribution | ❌ Không | Cao |
| Route choice history | ❌ Không | Cao |

## 3.3. Gap proofability
| Requirement | Hiện có | Gap |
|-------------|---------|-----|
| Runtime identity | ❌ Không | Cao |
| Config snapshot | ❌ Không | Cao |
| Control audit log | ❌ Không | Cao |

---

# IV. Root cause analysis

## 4.1. Kiến trúc
Control Dashboard hiện được xây trên **business/account backend** (`8000`), không phải trên **runtime control backend**.

## 4.2. Thiếu control APIs
`8000` có:
- `POST /control-api/api-keys`
- `GET /control-api/overview`
- `GET /control-api/usage`
- `GET /control-api/billing`
- `GET /control-api/quota`

Nhưng không có:
- `POST /control-api/nodes/{node}/enable`
- `POST /control-api/models/{model}/disable`
- `POST /control-api/policy/weights`
- `GET /control-api/runtime/state`

## 4.3. Thiếu runtime state propagation
Hybrid runtime (`8005`, `8015`) không expose:
- control state
- health detail
- warm status
- active config

## 4.4. Thiếu central control state store
Không có nơi lưu:
- node enable/disable state
- model enable/disable state
- traffic policy
- maintenance flags

---

# V. Đề xuất giải pháp

## 5.1. Thêm Control APIs vào `8000`
### Node control
```
POST /control-api/nodes/{node}/enable
POST /control-api/nodes/{node}/disable
GET  /control-api/nodes
```

### Model control
```
POST /control-api/models/{model}/enable
POST /control-api/models/{model}/disable
GET  /control-api/models
```

### Provider control
```
POST /control-api/providers/{provider}/enable
POST /control-api/providers/{provider}/disable
GET  /control-api/providers
```

### Policy control
```
PUT  /control-api/policy/weights
GET  /control-api/policy
POST /control-api/policy/safe-mode/{mode}
```

### Runtime control
```
GET  /control-api/runtime/state
POST /control-api/runtime/maintenance
POST /control-api/runtime/drain
```

## 5.2. Thêm control state store
### Redis keys
```
control:nodes:{node}:enabled = true/false
control:models:{model}:enabled = true/false
control:providers:{provider}:enabled = true/false
control:policy:weights = {"local":60,"remote":30,"cloud":10}
control:policy:safe_mode = "balanced"/"local_only"/"remote_only"/"cloud_only"
control:runtime:maintenance = true/false
```

## 5.3. Runtime phải tôn trọng control state
### `8005` (execution engine)
- Kiểm tra `control:models:{model}:enabled` trước khi gọi model
- Kiểm tra `control:providers:{provider}:enabled` trước khi fallback
- Tôn trọng `control:policy:safe_mode`

### `8015` (routing front door)
- Kiểm tra `control:nodes:{node}:enabled` trước khi route
- Áp dụng `control:policy:weights`
- Tôn trọng `control:runtime:maintenance`

## 5.4. Dashboard UI cần update
### New sections
- **Runtime Control** (node/model/provider on/off)
- **Policy Editor** (weights, safe modes)
- **Operational Controls** (maintenance, drain)
- **Real-time State** (active backend, traffic, health)

### Interactive controls
- Toggle switches
- Sliders for weights
- Mode selectors
- One-click actions

---

# VI. Implementation roadmap

## Phase 1 — Control State Foundation
### Deliverables
1. Redis control state schema
2. Control APIs cơ bản (node/model/provider enable/disable)
3. Dashboard UI section cho runtime control

### Timeline: 1-2 ngày

## Phase 2 — Policy Control
### Deliverables
1. Traffic weights API + UI
2. Safe modes API + UI
3. Runtime phải tôn trọng policy

### Timeline: 1-2 ngày

## Phase 3 — Operational Control
### Deliverables
1. Maintenance mode
2. Drain traffic
3. Force health check
4. Control audit log

### Timeline: 1-2 ngày

## Phase 4 — Advanced Visibility
### Deliverables
1. Real-time state endpoints
2. Route choice history
3. Cost/latency dashboard
4. SLA-ish metrics

### Timeline: 2-3 ngày

---

# VII. Technical details

## 7.1. Control state persistence
```python
# fastapi/control_state.py
import redis

class ControlState:
    def __init__(self):
        self.redis = redis.Redis(...)
    
    def is_node_enabled(self, node: str) -> bool:
        return self.redis.get(f"control:nodes:{node}:enabled") == "true"
    
    def set_node_enabled(self, node: str, enabled: bool):
        self.redis.set(f"control:nodes:{node}:enabled", "true" if enabled else "false")
    
    # ... tương tự cho model, provider, policy
```

## 7.2. Runtime integration
```python
# ttai_hybrid_v2_fixed.py (hoặc execution engine)
def execute_with_control_check(query, model):
    if not control_state.is_model_enabled(model):
        raise ModelDisabledError(f"Model {model} is disabled via control plane")
    
    if control_state.get_safe_mode() == "local_only":
        # chỉ dùng local
        pass
    
    # ... execution logic
```

## 7.3. Dashboard UI updates
```javascript
// control-dashboard/static/dashboard.js
async function toggleNode(nodeId, enabled) {
    const endpoint = enabled ? `/control-api/nodes/${nodeId}/enable` 
                            : `/control-api/nodes/${nodeId}/disable`;
    await fetch(endpoint, { method: 'POST' });
    refreshRuntimeState();
}

async function updateTrafficWeights(weights) {
    await fetch('/control-api/policy/weights', {
        method: 'PUT',
        body: JSON.stringify(weights)
    });
}
```

---

# VIII. Success criteria

## 8.1. Minimal viable control plane
- [ ] Node on/off hoạt động
- [ ] Model on/off hoạt động
- [ ] Provider on/off hoạt động
- [ ] Traffic weights có hiệu lực
- [ ] Safe modes có hiệu lực
- [ ] Dashboard UI hiển thị control state

## 8.2. Advanced control plane
- [ ] Maintenance mode
- [ ] Drain traffic
- [ ] Real-time state visibility
- [ ] Control audit log
- [ ] Historical route analysis

## 8.3. Platform readiness
- [ ] Control state survives restart
- [ ] APIs secure (admin auth)
- [ ] UI intuitive for ops
- [ ] Documentation for control surface

---

# IX. Next steps

## 9.1. Immediate
1. Review Redis availability
2. Design control state schema
3. Sketch dashboard UI changes

## 9.2. Short-term
1. Implement control_state.py
2. Add control APIs to main.py
3. Update dashboard.js với runtime control section
4. Test node/model enable/disable

## 9.3. Medium-term
1. Integrate with 8005/8015
2. Add policy control
3. Add operational controls
4. Enhance visibility

---

# X. References

- `control_dashboard/static/dashboard.js`
- `fastapi/main.py` (control-api endpoints)
- `fastapi/usage_truth.py`
- Redis configuration
- `TTAi_HYBRID_CANONICAL_TOPOLOGY_2026-04-10.md`
