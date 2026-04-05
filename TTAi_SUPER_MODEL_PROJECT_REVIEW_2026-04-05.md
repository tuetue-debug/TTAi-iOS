# TTAi SUPER MODEL PROJECT REVIEW — 2026-04-05

## 1. Executive Summary

TTAi Super Model has moved beyond pure infrastructure setup and is now in the transition from **system assembly** to **core stabilization + productization**.

As of 2026-04-05:
- **Infrastructure and production environment are strong**
- **Memory Brain / RAG has been materially improved today and is now working well in practice**
- **WordPress portal is usable, but plugin release/update workflow is still immature**
- **The main unresolved core area remains hybrid routing, load balancing behavior, and local backend reliability**

### Current overall assessment
- **Project completeness:** ~78–84%
- **Best-performing areas:** infrastructure, monitoring, RAG/memory, production environment access
- **Most important unfinished area:** hybrid routing core (classification, balancing, failover, hardening)

---

## 2. Source Basis for This Review

This review is based on:
- `TTAi_SUPER_MODEL_ARCHITECTURE.md`
- `TTAi_SUPER_MODEL_HYBRID_ARCHITECTURE.md`
- `TTAi_SUPER_MODEL_HYBRID_MASTER_PLAN.md`
- `TTAi_PROGRESS_REPORT_2026-04-04.md`
- project memory logs and validated operational work completed on 2026-04-05

Important note:
Several existing architecture/progress files still reflect **older snapshots** and do not fully capture the successful RAG repair/rebuild and WordPress production/plugin findings completed on 2026-04-05.

---

## 3. Current State by Major System Area

## 3.1 Infrastructure / Production Stack

### What is confirmed
- Production host and Docker-based stack are operational enough for direct maintenance and testing
- WordPress production instance is running inside Docker and is reachable/maintainable
- FastAPI, databases, and supporting services exist as a coherent production environment
- SSH/remote access is workable and has been used successfully for real maintenance
- Monitoring/collector infrastructure is present and usable

### Assessment
Infrastructure is now one of the strongest parts of the project.

### Status
- **Infrastructure / Production Stack:** 85–90%

---

## 3.2 Memory Brain / RAG

### What changed significantly on 2026-04-05
This area improved substantially today.

Completed:
- identified root cause of poor retrieval quality
- discovered ingest pipeline mismatch (`run-rag-ingest.ps1` was using legacy ingest path)
- patched parser + retrieval logic
- switched ingest pipeline to use `scripts/memory_ingest.py --index`
- verified `2026-04-05.md` entries now correctly enter `memory_dump.json`
- rebuilt Chroma knowledge base from scratch after stopping services
- benchmarked retrieval successfully

### Verified outcome
After clean rebuild, benchmark queries for today’s WordPress production/plugin/CSS work returned correct **2026-04-05** entries at the top.

### Assessment
This area has moved from “partially implemented” to “working in a practically useful way.”

### Status
- **Memory Brain / RAG:** 85–90%

### Remaining improvement ideas
- improve metadata cleanliness / encoding hygiene
- shorten overlong titles for better retrieval and readability
- continue tuning lexical/semantic balance if needed

---

## 3.3 WordPress Portal / User-Facing Chat Layer

### What is working
- Portal is usable
- Production chat plugin state has been identified correctly
- Production plugin slug/path confusion has been resolved operationally
- Broken plugin directories were cleaned from the live WordPress container
- Chat frame CSS was tuned directly in production plugin for acceptable current UX

### What is still weak
- Plugin packaging/release process is not yet mature
- Earlier release attempts failed due to slug/package/path mismatches
- Live edits inside container were the fastest successful method, but are not the desired long-term release model
- Portal UX is acceptable for now, but not yet standardized as a product release workflow

### Assessment
Usable in practice, but not yet productized cleanly.

### Status
- **WordPress Portal / Chat UX / Plugin delivery:** 70–78%

---

## 3.4 Control Dashboard / Monitoring / Collector

### Confirmed progress
A meaningful V1 control layer now exists:
- collector API in `services/control_dashboard/`
- endpoints:
  - `/health-summary`
  - `/providers`
  - `/workloads`
  - `/alerts`
- topology config in `config/topology.json`
- frontend service wrappers and admin dashboard component/page scaffolding
- token-protected collector support
- service registration via `automation/register_control_dashboard.ps1`
- admin portal integration path prepared

### Real-world status
- collector and dashboard services are now running as Windows services
- collector has practical operational value for checking topology, provider scores, workloads, alerts, and RAG status
- this is a strong observability asset for the project

### Assessment
The monitoring layer is no longer conceptual; it is a useful operational subsystem.

### Status
- **Control Dashboard / Monitoring:** 80–88%

---

## 3.5 Core Hybrid Inference / Load Balancing / Routing

### Vision in docs
The architecture documents consistently define this as the heart of TTAi Super Model:
- 60/30/10 balancing strategy
- query classification
- provider selection
- warm-up / anti-timeout handling
- fallback logic
- memory-aware routing

### Reality today
This is still the least proven critical area.

Evidence suggests:
- health snapshot can be green at a given moment
- but historical logs show instability in local backends (especially around 8005 / 8013)
- timeouts / HTTP 500 / latency spikes have happened repeatedly
- the strategy is well-described, but practical production-grade implementation and verification are not yet fully demonstrated

### Important distinction
The project has:
- strong provider availability
- multiple working paths
- conceptually clear routing strategy

But it still needs:
- implementation clarity
- validation of actual current routing behavior
- reliability hardening
- confidence that 60/30/10 is not just planned but truly enforced well under real load

### Assessment
This is still the main unfinished core.

### Status
- **Hybrid routing / balancing / classification core:** 55–65%

---

## 3.6 iOS / Delivery Pipeline

### What appears solid
- CI/CD work has historically been successful
- repository and build pipeline foundation exist

### Limiting factor
- real-device testing and downstream distribution remain dependent on hardware readiness (iMac/device path)

### Assessment
Not broken, but externally constrained.

### Status
- **iOS delivery path:** 65–75%

---

## 4. Progress Reconciliation: Docs vs Actual Reality

## Existing docs are directionally strong but partially stale

### Underrated in older docs
The following area is now stronger than several older files indicate:
- **Memory Brain / RAG**

### Still accurately flagged as weak in older docs
The following remains the key unresolved zone:
- **load balancing / routing / classifier / warm-up / reliability hardening**

### Newly clarified in real operations
The following gained important operational clarity today:
- WordPress production plugin identity and state
- Docker-based production maintenance path
- control dashboard serviceization
- RAG ingest and retrieval pipeline correctness

---

## 5. Current True Blockers

## Blocker 1 — Hybrid routing core is not fully closed
Needs direct review of:
- where classifier code actually lives
- what load balancer is currently doing in code and in runtime
- whether the 60/30/10 strategy is implemented or still mostly architectural intent

## Blocker 2 — Local backend stability under load is not yet trustworthy enough
Even if current health is green, historical instability remains a serious concern:
- timeouts
- latency spikes
- HTTP 500s
- dependency on remote backend as rescue path

## Blocker 3 — WordPress plugin release process is not yet standardized
Current operational workaround succeeded, but long-term product maintenance needs:
- one canonical production slug
- repeatable package structure
- predictable deployment/update procedure

## Blocker 4 — Project tracking documents lag behind actual state
Docs need refreshed progress truth so future planning is based on current reality, not older snapshots.

---

## 6. What Has Been Completed Well

## Strongly completed or near-complete
- production environment access and maintainability
- Docker-based operational maintenance workflow
- base observability/control layer
- memory logging and curation workflow
- RAG ingestion and retrieval repair/rebuild
- practical ability to recover and debug live services

## Functional but not yet mature
- WordPress chat delivery
- admin dashboard integration path
- frontend/admin operational polish
- API management/business/control-plane layer

## Still core incomplete
- hybrid intelligence behavior under real routing constraints
- classification + balancing + fallback policy as a tested production system

---

## 7. Updated Progress Scorecard

| Area | Current Assessment | Notes |
|---|---:|---|
| Infrastructure / Production Stack | 85–90% | Strong foundation |
| Memory Brain / RAG | 85–90% | Major improvement completed today |
| WordPress Portal / Chat UX | 70–78% | Usable, not yet cleanly productized |
| Control Dashboard / Monitoring | 80–88% | Useful V1 control/ops layer exists |
| Hybrid Routing / Balancing Core | 55–65% | Main unresolved core |
| iOS Delivery Path | 65–75% | Pipeline okay, hardware dependent |

### Overall project status
- **Total project progress:** ~78–84%

---

## 8. Recommended Priorities (Next)

## Priority 1 — Review and close the hybrid core
Immediate questions to answer:
- What code currently performs routing?
- What logic is actually live today?
- Is 60/30/10 active, partial, or only planned?
- How are 8005 / 8013 / remote paths selected and monitored?
- What hardening exists for timeouts, HTTP 500s, and warm-up?

This is the most important technical review remaining.

## Priority 2 — Standardize WordPress plugin delivery
Need to define:
- single production plugin identity
- canonical package structure
- safe update path
- no more ad-hoc slug proliferation

## Priority 3 — Refresh project tracking discipline
Need one updated review/progress truth source to avoid reconstructing project state repeatedly from logs and memory.

---

## 9. Recommended Immediate Next Action

### Recommended next review task
Perform a code-and-runtime review of:
- load balancer
- query classification
- hybrid API services (especially the 8005 / 8013 paths)

Goal:
- determine whether the core “Super Model” behavior is actually implemented as intended
- identify exact gap between architecture and runtime
- turn the remaining unknowns into a concrete completion plan

---

## 10. Ports, Services, Endpoints, and Storage Paths

A separate operational quick-reference file is maintained at:
- `TTAi_SYSTEM_MAP_AND_CHEATSHEET.md`

Use that file for daily operations and fast lookup.
Use this review document for strategic status and project-level assessment.


## 10.1 Confirmed local listening ports on `vannt-home-pc`

As checked on 2026-04-05, the following ports are actively listening locally:

| Port | Purpose | Notes |
|---|---|---|
| `8000` | FastAPI / core API path | Local API entry is listening |
| `8005` | Hybrid API | Currently healthy in dashboard health snapshot |
| `8015` | Load balancer | Collector reports 3 healthy backends currently |
| `8075` | RAG service API | Used for `/search` and `/context` |
| `8090` | Control Dashboard Collector | Collector service API |
| `8317` | CLI Proxy API | Was verified listening after restart |
| `11434` | Local Ollama | Local model service |

### Related known service ports from project context

| Port | Service | Host / Context |
|---|---|---|
| `8080` | WordPress production portal | Dell Zx0Q / Docker host |
| `3306` | MySQL | Production DB stack |
| `5432` | PostgreSQL | Production DB stack |
| `6379` | Redis | Production DB stack |
| `11434` | Remote Ollama | `100.89.201.7` / `vannt-work-op` |

---

## 10.2 Confirmed important endpoints

### Control Dashboard Collector API
- `GET /health-summary`
- `GET /providers`
- `GET /workloads`
- `GET /alerts`
- Base local URL: `http://127.0.0.1:8090`
- When token protection is enabled, requests require header:
  - `X-Control-Token: <token>`

### RAG service API
- `POST /search`
- `POST /context`
- Base local URL: `http://127.0.0.1:8075`

### Portal/admin-related paths described in project notes
- UI login path: `/login`
- Admin dashboard path: `/admin/dashboard-control`
- Backend proxy path: `/api/v1/admin/control-dashboard`
- Auth login endpoint: `/api/v1/auth/login`

### WordPress / portal production access references
- WordPress production service is described on port `8080`
- Tailnet/admin access examples referenced in project notes include:
  - `http://vannt-home-zq.tail45599e.ts.net:8000/login`

---

## 10.3 Confirmed runtime topology snapshot

### `vannt-home-pc`
- **Load Balancer** → healthy
- **Hybrid API** → healthy
- **RAG Service** → healthy

Current collector snapshot reports the load balancer sees these backends as healthy:
- `http://localhost:8005`
- `http://localhost:8000`
- `http://100.89.201.7:8000`

### `vannt-work-op`
- **Remote FastAPI** → healthy
- **Remote Ollama** → healthy

Remote Ollama models reported by collector currently include:
- `qwen3-vl:8b`
- `gemma3:12b`
- `deepseek-r1:8b`
- `gemma3:4b`

---

## 10.4 Important storage paths and project directories

### Workspace root
- `C:\Users\vannt-pc\.openclaw\workspace`

### Core operational directories in workspace
- `services\` → backend services
- `automation\` → scripts for setup/ops/ingest/service registration
- `data\` → generated state and structured outputs
- `logs\` → operational logs
- `memory\` → daily memory files and continuity notes
- `datasets\` → dataset snapshots / training-related assets
- `frontend\` → portal frontend code
- `docs\` → documentation

### Especially important paths
- `services\control_dashboard\collector_service.py`
- `services\control_dashboard\config\topology.json`
- `services\rag_service\rag_engine.py`
- `scripts\memory_ingest.py`
- `automation\run-rag-ingest.ps1`
- `automation\register_control_dashboard.ps1`
- `data\memory_dump.json`
- `data\memory_ingest_state.json`
- `logs\rag_ingest.log`
- `logs\load_balancer.jsonl`
- `logs\provider_metrics.jsonl`
- `logs\provider_scores.json`

### RAG persistent storage
- Active Chroma / knowledge base directory:
  - `E:\openclaw-knowledge_base`
- Backup created during clean rebuild on 2026-04-05:
  - `E:\openclaw-knowledge_base-backup-2026-04-05-0606`

### WordPress production plugin path discovered in Docker
Inside container `ttai-wordpress`, the active production plugin path is:
- `/var/www/html/wp-content/plugins/ttai-chat-plugin-1.1.1-1/wordpress-chat-plugin.php`

Related production plugin facts:
- active plugin slug/path in WordPress DB:
  - `ttai-chat-plugin-1.1.1-1/wordpress-chat-plugin.php`
- header version inside that plugin file:
  - `1.1.7`
- inactive older copy exists at:
  - `/var/www/html/wp-content/plugins/ttai-chat/wordpress-chat-plugin.php`
  - with older version header `1.1.4`

---

## 10.5 Service names explicitly confirmed

Windows services confirmed in current environment:
- `TTAiRagService`
- `TTAiControlDashboard`

Operational note:
These services had to be stopped and restarted during the clean RAG rebuild on 2026-04-05.

---

## 10.6 Key operational paths to remember for future work

### For RAG maintenance
- run ingest via:
  - `automation\run-rag-ingest.ps1`
- parser/index source of truth now points to:
  - `scripts\memory_ingest.py --index`

### For collector/dashboard maintenance
- collector implementation:
  - `services\control_dashboard\collector_service.py`
- service registration:
  - `automation\register_control_dashboard.ps1`

### For portal/chat maintenance
- production WordPress plugin must be treated carefully by actual active slug/path, not by guessed folder names
- container used for direct production maintenance:
  - `ttai-wordpress`

---

## 11. Final Project Readout

TTAi Super Model is no longer “just an architecture concept with infra setup.”
It is now a **partially operational system with a working production environment, working memory brain, and usable portal path**.

The project’s center of gravity has changed.
The biggest work ahead is no longer “bring systems up.”
It is now:
- **make the core hybrid intelligence reliable and explicit**
- **standardize release/product operations**
- **convert a working stack into a coherent, repeatable product**

That is the real current phase of the project.

---

**Prepared:** 2026-04-05
**Context owner:** Tuệ Văn
**Review synthesized by:** Tuệ Tuệ
