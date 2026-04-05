# TTAi SYSTEM MAP AND CHEATSHEET

## 1. Purpose

This file is the short operational map for day-to-day TTAi work.
It is intentionally separate from the full project review.

Use this file when you need quick answers to:
- Which port does what?
- Which service is running where?
- Which path stores what?
- Which container/service should be touched for maintenance?
- Which command/script is the right operational entry point?

---

## 2. Core Hosts / Nodes

## 2.1 `vannt-home-pc`
Role:
- local development + orchestration core
- load balancer
- hybrid API
- RAG service
- control dashboard collector
- local Ollama
- CLI proxy API

## 2.2 `vannt-work-op`
Role:
- remote worker / remote compute node
- remote FastAPI
- remote Ollama node

## 2.3 Dell Zx0Q / `vannt-home-zq`
Role:
- production host
- WordPress production portal
- production DB stack
- FastAPI production host path from project architecture

---

## 3. Ports Cheat Sheet

| Port | System | Meaning | Notes |
|---|---|---|---|
| `8000` | FastAPI | Core/local API path | Listening locally on `vannt-home-pc` |
| `8005` | Hybrid API | TTAi hybrid service | Healthy in latest dashboard snapshot |
| `8013` | Legacy/local backend path | Historical backend path | Has shown high latency in history |
| `8015` | Load Balancer | Aggregation / routing layer | Healthy now, but logs should still be watched |
| `8075` | RAG Service | RAG API | Used for `/search` and `/context` |
| `8090` | Control Dashboard Collector | Monitoring API | Token header may be required |
| `8080` | WordPress Production | Portal/UI | On production host / Docker environment |
| `8317` | CLI Proxy API | Cloud API proxy path | Was confirmed listening after restart |
| `11434` | Ollama Local | Local model runtime | Local host |
| `11434` | Ollama Remote | Remote model runtime | Remote node `100.89.201.7` |
| `3306` | MySQL | WordPress DB | Production stack |
| `5432` | PostgreSQL | Core DB | Production stack |
| `6379` | Redis | Cache / queue support | Production stack |

---

## 4. Endpoint Cheat Sheet

## 4.1 Control Dashboard Collector
Base URL:
- `http://127.0.0.1:8090`

Endpoints:
- `GET /health-summary`
- `GET /providers`
- `GET /workloads`
- `GET /alerts`

Auth:
- optional token via header:
  - `X-Control-Token: <token>`

## 4.2 RAG Service
Base URL:
- `http://127.0.0.1:8075`

Endpoints:
- `POST /search`
- `POST /context`

## 4.3 Portal / Admin / Auth Paths
- `/login`
- `/admin/dashboard-control`
- `/api/v1/admin/control-dashboard`
- `/api/v1/auth/login`

## 4.4 Tailnet / production access examples
Referenced working example from project notes:
- `http://vannt-home-zq.tail45599e.ts.net:8000/login`

---

## 5. Key Runtime Topology

## 5.1 Local core (`vannt-home-pc`)
Current known service roles:
- Load Balancer
- Hybrid API
- RAG Service
- Control Dashboard Collector
- Local Ollama
- CLI Proxy API

Latest healthy backend set reported by collector:
- `http://localhost:8005`
- `http://localhost:8000`
- `http://100.89.201.7:8000`

## 5.2 Remote worker (`vannt-work-op`)
Current known service roles:
- Remote FastAPI
- Remote Ollama

Current remote Ollama models seen by collector:
- `qwen3-vl:8b`
- `gemma3:12b`
- `deepseek-r1:8b`
- `gemma3:4b`

---

## 6. Storage and File Paths

## 6.1 Workspace root
- `C:\Users\vannt-pc\.openclaw\workspace`

## 6.2 Important top-level directories
- `services\`
- `automation\`
- `data\`
- `logs\`
- `memory\`
- `datasets\`
- `frontend\`
- `docs\`

## 6.3 Important code / script paths

### RAG / memory
- `scripts\memory_ingest.py`
- `services\rag_service\rag_engine.py`
- `automation\run-rag-ingest.ps1`
- `data\memory_dump.json`
- `data\memory_ingest_state.json`
- `logs\rag_ingest.log`

### Control Dashboard
- `services\control_dashboard\collector_service.py`
- `services\control_dashboard\config\topology.json`
- `automation\register_control_dashboard.ps1`
- `logs\control_dashboard\`

### Hybrid / routing / provider monitoring
- `logs\load_balancer.jsonl`
- `logs\provider_metrics.jsonl`
- `logs\provider_scores.json`
- `data\learn_queue.jsonl`

### Memory continuity
- `MEMORY.md`
- `memory\YYYY-MM-DD.md`

---

## 7. Persistent Data Stores

## 7.1 RAG knowledge base
Active path:
- `E:\openclaw-knowledge_base`

Backup created during clean rebuild on 2026-04-05:
- `E:\openclaw-knowledge_base-backup-2026-04-05-0606`

## 7.2 WordPress production plugin path (inside container)
Active production plugin file:
- `/var/www/html/wp-content/plugins/ttai-chat-plugin-1.1.1-1/wordpress-chat-plugin.php`

Important fact:
- active plugin slug/path in DB:
  - `ttai-chat-plugin-1.1.1-1/wordpress-chat-plugin.php`
- header version inside file:
  - `1.1.7`

Older inactive copy:
- `/var/www/html/wp-content/plugins/ttai-chat/wordpress-chat-plugin.php`
- older header version:
  - `1.1.4`

---

## 8. Containers and Services

## 8.1 Docker container names seen in production WordPress environment
- `ttai-wordpress`
- `ttai-mysql`
- `ttai-control-collector`
- `ttai-fastapi`
- `ttai-postgres`
- `ttai-redis`

## 8.2 Windows services explicitly confirmed
- `TTAiRagService`
- `TTAiControlDashboard`

---

## 9. Operational Entry Points

## 9.1 Rebuild/re-index RAG
Use:
- `automation\run-rag-ingest.ps1`

Important current rule:
- ingest should now flow through:
  - `scripts\memory_ingest.py --index`

## 9.2 Register dashboard collector as service
Use:
- `automation\register_control_dashboard.ps1`

## 9.3 Control dashboard collector implementation
Use for code changes:
- `services\control_dashboard\collector_service.py`

## 9.4 Production WordPress maintenance
Use Docker container:
- `ttai-wordpress`

Be careful:
- production plugin identity must follow the real active slug/path, not guessed zip names

---

## 10. Common Operational Reminders

## 10.1 For RAG work
- check `data\memory_dump.json` if retrieval seems wrong
- check `logs\rag_ingest.log` after every ingest
- if quality is suspicious, verify whether collection rebuild is needed

## 10.2 For dashboard work
- collector may require `X-Control-Token`
- use `/health-summary` for live topology truth
- use `/workloads` for RAG/load/data state

## 10.3 For WordPress plugin work
- check actual active plugin path in WordPress before packaging anything
- avoid slug sprawl and mismatched zip naming
- treat `ttai-chat-plugin-1.1.1-1` as current production identity unless intentionally migrated

## 10.4 For hybrid system review
- do not trust green health snapshot alone
- compare health snapshot with historical `load_balancer.jsonl`
- especially watch:
  - `8005`
  - `8013`
  - remote fallback behavior

---

## 11. Recommended Future Additions to This Cheat Sheet
- exact load balancer source file(s)
- exact classifier source file(s)
- exact FastAPI service names for 8000 / 8005 / 8015
- exact production host filesystem paths for portal/backend deployment
- exact restart commands for each runtime component

---

## 12. Usage Rule

Use this file as the short operational map.
Use `TTAi_SUPER_MODEL_PROJECT_REVIEW_2026-04-05.md` for the full review and strategic status.
