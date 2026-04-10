# TTAi Simple Proxy Backend Pool Redesign — 2026-04-10

## Mục tiêu
Thiết kế lại backend pool cho `TTAiSimpleProxy` để phù hợp với kiến trúc phase mới, giảm assumptions cũ, và đặt proxy dưới quyền điều khiển của dashboard control.

---

# I. Current pool problem

## Current hard-coded pool
```python
BACKENDS = [
    "http://localhost:8005",
    "http://localhost:8000",
    "http://100.89.201.7:8000"
]
```

## Problems
1. assumes `8005` should always exist
2. treats `8000` as just another execution backend
3. lacks backend classes/roles
4. not controlled by dashboard
5. not aware of node capability differences

---

# II. Redesign principles

## 1. Pool must be role-aware
Không chỉ là danh sách URL. Mỗi backend phải có:
- role
- node class
- enabled flag
- health state
- routing priority
- allowed modes

## 2. Pool must be dashboard-controlled
Dashboard control phải có quyền:
- add/remove backend from active pool
- enable/disable backend
- set preferred backend
- mark backend maintenance/degraded

## 3. Pool must support phased architecture
Pool phải hỗ trợ:
- temporary stabilization
- remote-first production
- optional local execution
- future modular expansion

---

# III. Proposed backend classes

## Class A — `stabilization`
### Example
- `http://localhost:8000`

### Use
- short-term recovery path
- fallback safe backend
- minimal additional infra

### Notes
- không phải final ideal execution path
- nhưng hữu ích để khôi phục nhanh user-facing chat

## Class B — `primary-inference`
### Example
- `http://100.89.201.7:8000`

### Use
- main remote inference path
- heavier model execution
- preferred production inference host

### Notes
- phù hợp hơn với resource-aware architecture

## Class C — `optional-local-executor`
### Example
- `http://localhost:8005`

### Use
- only if local execution role is still justified
- on-demand or diagnostic mode

### Notes
- không nên default active trên home node yếu

## Class D — `future-modules`
### Example
- additional execution nodes
- specialized inference endpoints

---

# IV. Proposed active pool by phase

## Phase 0 / stabilization
### Active pool
- `localhost:8000`
- `100.89.201.7:8000`

### Inactive
- `localhost:8005`

### Why
- restore minimal functionality
- no extra local load
- avoid reviving old assumptions

## Phase 1 / controlled recovery
### Active pool
- `100.89.201.7:8000` as primary
- `localhost:8000` as fallback/stabilization

### Conditional
- `localhost:8005` only if specifically enabled in dashboard

## Phase 2 / modular routing
### Active pool
- dashboard-controlled dynamic pool
- explicit backend roles
- optional local execution class if justified

---

# V. Proposed backend object model

```json
[
  {
    "id": "local-fastapi-8000",
    "url": "http://localhost:8000",
    "role": "stabilization",
    "node": "vannt-home-zq",
    "enabled": true,
    "preferred": false,
    "modes": ["stabilize", "balanced", "maintenance"],
    "weight": 20
  },
  {
    "id": "remote-workop-8000",
    "url": "http://100.89.201.7:8000",
    "role": "primary-inference",
    "node": "vannt-work-op",
    "enabled": true,
    "preferred": true,
    "modes": ["balanced", "remote-first", "stabilize"],
    "weight": 80
  },
  {
    "id": "local-hybrid-8005",
    "url": "http://localhost:8005",
    "role": "optional-local-executor",
    "node": "vannt-home-zq",
    "enabled": false,
    "preferred": false,
    "modes": ["diagnostic"],
    "weight": 0
  }
]
```

---

# VI. Dashboard controls required

## Backend pool controls
- list backends
- enable/disable backend
- set preferred backend
- edit mode eligibility
- set backend weight
- maintenance toggle

## Visualization
- backend cards with role + state
- latency + error rate
- last successful route
- active mode compatibility

## Auditability
- when backend enabled/disabled
- by whom
- previous and new values

---

# VII. Hedge redesign

## Current issue
Hedge hiện chỉ dựa trên local vs remote pools.
Điều này quá cứng.

## Proposed redesign
Dashboard should control:
- hedge enabled/disabled
- hedge allowed modes
- hedge candidate classes
- hedge delay ms

## Suggested defaults
### Stabilize mode
- hedge off

### Balanced mode
- hedge optional, conservative

### Remote-first mode
- hedge remote primary → local stabilization only if needed

### Diagnostic mode
- hedge off unless explicitly testing

---

# VIII. Final recommendation

## Immediate pool recommendation
### Active now (conceptually)
- `localhost:8000`
- `100.89.201.7:8000`

### Inactive now
- `localhost:8005`

## Why
This supports:
- chat recovery
- reduced local load
- cleaner phase transition
- dashboard-controlled evolution later

---

# IX. Final statement

`TTAiSimpleProxy` should no longer own a hard-coded list of old backends.
It should operate on a **dashboard-managed backend pool** with role-aware backend objects and explicit mode-based routing.
