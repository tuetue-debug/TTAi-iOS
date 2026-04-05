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
- **Architecture Direction (2026-04-05):** Confirmed 3-surface product split for TTAi API Model:
  - `chat.tuetue.vn` = end-user/product UI for chat experience, later login/packages/subscriptions/user usage
  - `control.tuetue.vn` = operator/admin control dashboard for system/core/model/Ollama/provider management
  - `api.tuetue.vn` = FastAPI backend core for chat, metering, quota, billing, admin APIs, and future auth/tenant/api-key logic
- **Core Identity:** `TTAi Super Model Hybrid` is the main backend/core intelligence layer of the system and is intended to evolve into Tuệ Tuệ's own model/core brain over time.
- **Boundary Decision:** Do not put quota/billing/core backend logic directly inside WordPress. WordPress should remain public-site/content/docs/marketing, while control and product surfaces call into FastAPI backend APIs.
- **System Design Rule:** `control.tuetue.vn` should be primarily admin UI/control console, while `api.tuetue.vn` remains the control-plane/business-logic backend. Avoid mixing control UI with backend state logic.
- **Execution Order Decision:** Near-term execution should proceed in this order: (1) stabilize/deploy API backend and admin foundations, (2) build `control.tuetue.vn` MVP admin console on top of backend APIs, (3) build `chat.tuetue.vn` user/product surface with login, plans, subscriptions, and usage views.
- **Decision:** Abandoned Oracle Cloud due to account/capacity issues
- **Decision:** Pivoted to local Docker-based stack (FastAPI + PostgreSQL + Redis + WordPress)
- **Decision:** WordPress MySQL pivot after PostgreSQL PHP extension failures
- **Decision:** CI bypass strategy with minimal workflow (ci-minimal.yml)
- **Decision:** Infrastructure expansion to vannt-work-op via Tailscale
- **Milestone:** GitHub setup completed (2026-03-23)
- **Milestone:** Local MVP + Production Migration COMPLETE (2026-03-24)
- **Milestone:** Remote deployment to vannt-work-op operational (2026-03-28)
- **Stack:** FastAPI ✅, PostgreSQL ✅, Redis ✅, MySQL ✅, WordPress ⚠️ (install pending)
- **Infrastructure:** Tailscale ✅, SSH access ✅, Docker remote ✅
- **CI/CD:** Minimal workflow green (CI Minimal #4), iOS builds successful
- **Current Focus:** Resolve SSH authentication issue with vannt-work-op (PRIMARY BLOCKER), deploy TTAi to remote machine, implement load balancing, resolve cloud API timeout issues in hybrid system
- **Timeline:** DAY 5-6 of aggressive timeline; ~85% of Week 1 goals achieved; Major infrastructure complete (Hybrid System, Tailscale, local deployment); Pending remote deployment and load balancing
- **Active Systems:** TTAi Hybrid v2.0 (port 8005), TTAi Debug (port 8013), TTAi Simple Proxy (port 8015), FastAPI Original (port 8000)
- **Issues:** SSH connection hanging to vannt-work-op (PRIMARY BLOCKER), cloud API timeouts in hybrid routing, iMac repair pending (blocks iOS testing)
- **Timeline Status:** On track for Week 1 completion; SSH issue must be resolved today to stay on schedule for Week 2 Phase 2 launch
- **Last Check:** 2026-04-01 03:40 - Health check shows multiple services down:
  - Load balancer (8015) ❌ DOWN
  - Remote server (100.89.201.7:8000) ❌ DOWN  
  - Local service (8000) ❌ DOWN
  - Services on 8013/8005 ⚠️ WARNING
  - Immediate attention required

### iOS App Development
- **Repository:** `tuetue-debug/TTAi-iOS` (Xcode project)
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
