# Long-term Memory

## Credentials & Access
- **GitHub Account:** `tuetue-debug`
- **GitHub Email:** `tuetue@minhtue.vn`
- **GitHub Repository:** `TTAi-iOS` (https://github.com/tuetue-debug/TTAi-iOS)
- **Authentication:** Personal Access Token required for CLI operations
- **Note:** Token scope needs `repo` permissions

## Preferences & Working Style
- **Communication:** Direct, concise, no filler words
- **Development:** Prefers rapid implementation (15-20 min/step)
- **Infrastructure:** Willing to pivot when blocked (Oracle Cloud → local deployment)
- **Project Management:** Values clear milestones and progress tracking

## Active Projects & Decisions
### TTAi Project (Active)
- **Status:** Phase 1 COMPLETE - Full stack operational on Dell Zx0Q

#### Canonical Architecture Statement
- **Architecture Direction (2026-04-05, updated 2026-04-09):** Confirmed 4-surface product split for TTAi platform:
  - `console.tuetue.vn` = canonical developer portal / API console / portal root / developer platform surface for signup, login, API keys, usage, billing, limits, docs, and future social auth
  - `api.tuetue.vn` = machine-facing FastAPI runtime / backend core / API runtime / core backend surface for chat, metering, quota, billing, admin APIs, and future auth/tenant/api-key logic
  - `control.tuetue.vn` = internal operator/admin control dashboard for system/core/model/Ollama/provider management
  - `chat.tuetue.vn` = end-user/product UI for chat experience, later login/packages/subscriptions/user usage
- **Priority Clarification (2026-04-05):** `control.tuetue.vn` and `api.tuetue.vn` are the main surfaces that matter most right now. WordPress admin/plugin integration is secondary/supporting only and should not drive core architecture decisions.
- **System Design Rule:** `control.tuetue.vn` should be primarily admin UI/control console, while `api.tuetue.vn` remains the control-plane/business-logic backend. Avoid mixing control UI with backend state logic.
- **Execution Order Decision:** Near-term execution should proceed in this order: (1) stabilize/deploy API backend and admin foundations, (2) build `control.tuetue.vn` MVP admin console on top of backend APIs as the main control surface, (3) build canonical developer portal at `console.tuetue.vn`, (4) build `chat.tuetue.vn` user/product surface with login, plans, subscriptions, and usage views. WordPress admin can support this work but is not the main destination.

#### Canonical Boundary Statement
- **Core Identity:** `TTAi Super Model Hybrid` is the main backend/core intelligence layer of the system and is intended to evolve into Tuệ Tuệ's own model/core brain over time.
- **Boundary Decision:** Do not put quota/billing/core backend logic directly inside WordPress.
- **Reason:** WordPress should remain public-site/content/docs/marketing, while control and product surfaces call into FastAPI backend APIs.
- **Alias Reminder:** Do not collapse backend logic into WordPress/CMS. Keep business logic in FastAPI/backend core.

#### Canonical Domain Milestone
- **Milestone (2026-04-09):** `console.tuetue.vn` is now live as the portal root and canonical developer console.
- **After this update:** portal auth works end-to-end (signup/login/dashboard), docs expose customer connection info, and `api.tuetue.vn` remains the runtime/API domain while `/portal` is intended to redirect to console.
- **Chronology Marker:** The domain architecture update on 2026-04-09 was followed by console root go-live, working signup/login/dashboard, docs sync, and customer connection info publication.

#### Canonical Project State
- **Current Focus:** Resolve SSH authentication issue with vannt-work-op (PRIMARY BLOCKER), deploy TTAi to remote machine, implement load balancing, resolve cloud API timeout issues in hybrid system
- **Primary Blocker:** SSH connection hanging / SSH authentication issue with vannt-work-op
- **Current Issues:** SSH connection hanging to vannt-work-op (PRIMARY BLOCKER), cloud API timeouts in hybrid routing, iMac repair pending (blocks iOS testing)
- **Timeline:** DAY 5-6 of aggressive timeline; ~85% of Week 1 goals achieved; Major infrastructure complete (Hybrid System, Tailscale, local deployment); Pending remote deployment and load balancing
- **Timeline Status:** On track for Week 1 completion; SSH issue must be resolved today to stay on schedule for Week 2 Phase 2 launch

#### Decisions & Milestones
- **Decision:** Abandoned Oracle Cloud due to account/capacity issues
- **Decision:** Pivoted to local Docker-based stack (FastAPI + PostgreSQL + Redis + WordPress)
- **Decision:** WordPress MySQL pivot after PostgreSQL PHP extension failures
- **Decision:** CI bypass strategy with minimal workflow (ci-minimal.yml)
- **Decision:** Infrastructure expansion to vannt-work-op via Tailscale
- **Milestone:** GitHub setup completed (2026-03-23)
- **Milestone:** Local MVP + Production Migration COMPLETE (2026-03-24)
- **Milestone:** Remote deployment to vannt-work-op operational (2026-03-28)

#### Systems & Infrastructure
- **Stack:** FastAPI ✅, PostgreSQL ✅, Redis ✅, MySQL ✅, WordPress ⚠️ (install pending)
- **Infrastructure:** Tailscale ✅, SSH access ✅, Docker remote ✅
- **CI/CD:** Minimal workflow green (CI Minimal #4), iOS builds successful
- **Active Systems:** TTAi Hybrid v2.0 (port 8005), TTAi Debug (port 8013), TTAi Simple Proxy (port 8015), FastAPI Original (port 8000)
- **Last Check:** 2026-04-01 03:40 - Health check shows multiple services down:
  - Load balancer (8015) ❌ DOWN
  - Remote server (100.89.201.7:8000) ❌ DOWN  
  - Local service (8000) ❌ DOWN
  - Services on 8013/8005 ⚠️ WARNING
  - Immediate attention required

#### Chronology Markers
- **What happened first?** The memory system audit was written on 2026-04-07 before the 4-layer memory benchmark completed on 2026-04-09.
- **What happened after the 2026-04-09 domain update?** `console.tuetue.vn` went live at root, signup/login/dashboard worked end-to-end, docs were synced, and customer connection info was published.

### iOS App Development
#### Canonical Ownership Statement
- **GitHub Account:** `tuetue-debug`
- **Repository:** `tuetue-debug/TTAi-iOS` (Xcode project)
- **Ownership Answer Form:** The GitHub account currently used for TTAi-iOS is `tuetue-debug`, and the repository currently used is `tuetue-debug/TTAi-iOS`.
- **Authentication:** Personal Access Token required for CLI operations

#### Current Delivery State
- **CI/CD:** GitHub Actions configured and successful (multiple runs)
- **Testing:** Pending iMac repair for real device testing
- **Plan:** Automated builds → TestFlight → App Store
- **Status:** Build pipeline functional and consistently passing; TestFlight deployment ready when iMac hardware repaired
- **Last Check:** 2026-03-29 04:56 - CI/CD operational, awaiting hardware for real device testing

## Lessons Learned
1. **Oracle Cloud Free Tier:** Unreliable for immediate deployment; have paid alternatives ready
2. **GitHub Authentication:** Personal Access Tokens required for CLI; SSH keys recommended for long-term
3. **YAML Syntax:** GitHub Actions workflows are strict about indentation; use online validators
4. **Rapid Pivoting:** When blocked, quickly switch to alternative path (local deployment vs cloud)
5. **Documentation:** Keep memory logs updated for continuity between sessions
6. **Remote API Testing:** SSH/PowerShell escaping can corrupt JSON payloads; validate endpoint functionality through logs and alternative testing methods rather than relying solely on curl through complex shell pipelines
7. **Infrastructure Planning:** Tailscale provides reliable zero-config networking for multi-machine deployments
8. **Docker Health Checks:** Application responding doesn't guarantee Docker health check passes; configure appropriate health check endpoints
9. **Timeline Management:** Aggressive timelines require flexibility; celebrate infrastructure wins even if feature development shifts
10. **Remote Deployment:** Copy deployment files before starting containers; verify each service independently before integration testing
11. **Hybrid AI Systems:** Implement smart query routing based on complexity and response time requirements; local Ollama for simple queries (20-30s), cloud APIs for complex queries (1-3s) provides optimal cost-performance balance
12. **API Integration:** Maintain multiple AI provider integrations (DeepSeek, Gemini, Ollama) for redundancy and optimal query routing based on task type
13. **Vietnamese Text Processing:** Handle encoding issues carefully when processing Vietnamese text for query classification; use proper Unicode handling and consider language-specific patterns
14. **Fallback Mechanisms:** Implement robust fallback logic when primary providers fail (e.g., cloud API timeout → local Ollama, local Ollama timeout → simpler model)
15. **Aggressive Timeline Management:** Regular progress checks against timeline; Identify blockers early; Adjust timeline based on actual progress vs planned milestones
16. **SSH/Remote Access:** Test SSH connections early in deployment process; Have alternative deployment methods ready (manual copy, different authentication methods)
17. **FastAPI + CLI Proxy Integration:** For local TTAi FastAPI 8000, prefer local CLI proxy at `https://127.0.0.1:8317` with internal TLS verify disabled in code, ensure NSSM service `TTAiFastAPI8000` has `CLI_PROXY_API_KEY=cliproxy-dev-token`, and use `TTAi_FASTAPI_CLIPROXY_FIX_NOTES_2026-04-05.md` as the detailed runbook for future incidents.
18. **Architecture Separation:** For TTAi, keep product UI (`chat.*`), admin/control UI (`control.*`), and backend core (`api.*`) as separate surfaces with clear boundaries. Let UIs call backend APIs; do not collapse backend logic into WordPress/CMS.
19. **Control Plane Design:** `control.tuetue.vn` should be an admin console backed by APIs, not the place where core business logic lives. Keep system/model/provider control actions in FastAPI endpoints and let the dashboard consume them.
20. **Roadmap Discipline:** Build TTAi in layered order: backend core first, then admin/control console, then customer/product surface. This reduces churn and keeps quota/billing/auth foundations reusable.
21. **Backend Switching Observability:** For switchable runtimes like the RAG service on port `8075`, never trust service config alone. Always verify real port ownership, build marker, active backend, raw env values, and runtime proof endpoints before declaring a cutover successful.
22. **Orphan Process Risk:** Service restarts can appear successful while a stale/orphan process still owns the live port. Verify parent-child relationships and real listener PID (`Get-NetTCPConnection`) before assuming the managed service controls the runtime.
23. **RAG 8075 Cutover Milestone (2026-04-10):** Port `8075` was successfully promoted onto the compatibility-surface design with `backend = rag_v2`, `backend_active = RAGV2ShadowBackend`, and build marker `rag-service-build-d68cd55-marker-1` after identifying and removing orphan Python PID `7696` that had been silently holding the live port.
