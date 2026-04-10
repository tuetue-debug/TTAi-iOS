# TTAi WordPress to Hybrid Runtime Recovery Plan — 2026-04-10

## Mục tiêu
Khôi phục chat path từ WordPress theo hướng tối ưu, không làm `vannt-home-zq` nặng thêm, và phù hợp với kiến trúc tương lai.

---

# I. Current understanding

## Browser-facing path
`chat.tuetue.vn` → `wp-admin/admin-ajax.php`

## Plugin internal forwarding
WordPress plugin `TTAi Chat Interface v1.1.7` forwards request to:
1. `ttai_chat_api_endpoint` option
2. env `TTAI_CHAT_API`
3. default `http://host.docker.internal:8015/api/chat`

## Problem
- `8015` currently OFF
- plugin likely forwarding to an unavailable or wrong-role backend
- WordPress AJAX still returns `200 OK`, but plugin surfaces generic error to user

---

# II. Recovery principles

1. Do not restore old hybrid services blindly on home node.
2. Do not increase persistent inference load on `vannt-home-zq`.
3. First restore user-facing chat reliability.
4. Then align runtime path to canonical topology.

---

# III. Recovery options

## Option A — Temporary stabilization via FastAPI 8000
### Path
WordPress plugin → `http://host.docker.internal:8000/api/chat`

### Pros
- fastest way to restore chat
- no need to restore 8015 immediately
- reuses already-running backend

### Cons
- keeps chat path going through 8000 hybrid endpoints temporarily
- not final canonical architecture

### Best use
- short-term stabilization

---

## Option B — Controlled restore of 8015
### Path
WordPress plugin → `http://host.docker.internal:8015/api/chat`

### Pros
- closer to target topology
- keeps routing/front-door role separate

### Cons
- adds another always-on service to home node
- risky if 8015 still contains old heavy assumptions
- may reintroduce machine pressure

### Best use
- only after 8015 is refactored / validated as lightweight routing front door

---

## Option C — Remote-first path
### Path
WordPress plugin → remote runtime or 8000 proxying remote path

### Pros
- offloads inference from weak home node
- closer to intended resource-aware architecture

### Cons
- more moving parts
- may require bridge/proxy updates
- more work than temporary stabilization

### Best use
- medium-term correct architecture

---

# IV. Recommended staged recovery

## Stage 1 — Stabilize user chat
### Recommendation
Temporarily point WordPress plugin to:
- `http://host.docker.internal:8000/api/chat`

### Why
- 8000 is already running
- lowest-risk way to bring chat back
- avoids restoring 8015 immediately

## Stage 2 — Remove local inference pressure from home node
### Recommendation
- evaluate and stop local Ollama on home node if no critical dependency
- ensure 8000 hybrid path can prefer remote / CLI proxy fallback

## Stage 3 — Rebuild canonical routing path
### Recommendation
- redesign/restore 8015 as lightweight routing front door
- ensure it routes to remote inference host where appropriate
- only then move WordPress back to 8015 if still needed

---

# V. Concrete next actions

## Immediate
1. Confirm current WordPress endpoint setting
2. If broken, change plugin endpoint to `http://host.docker.internal:8000/api/chat`
3. Test end-to-end WordPress chat

## Near-term
4. Audit 8000 `/api/chat` dependency on local Ollama
5. Prefer remote path / CLI proxy where possible
6. Decide whether local Ollama can be removed

## Medium-term
7. Refactor 8015 into lightweight routing front door
8. Move WordPress to canonical routed path if beneficial

---

# VI. Decision recommendation

## Strong recommendation
For recovery:
- **Do not restore 8015 first**
- **Use 8000 as temporary stabilization target**
- **Then redesign routing path cleanly**

This is the safest path that restores chat without making home node heavier.
