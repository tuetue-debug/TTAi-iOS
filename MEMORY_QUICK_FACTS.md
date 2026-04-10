# MEMORY_QUICK_FACTS.md

## TTAi quick facts
- **Primary blocker:** SSH authentication / hanging connection issue with `vannt-work-op`
- **GitHub account for TTAi-iOS:** `tuetue-debug`
- **GitHub repository for TTAi-iOS:** `tuetue-debug/TTAi-iOS`
- **Canonical developer portal:** `console.tuetue.vn`
- **Canonical developer portal aliases:** developer portal, API console, portal root, developer platform surface
- **API runtime/backend core:** `api.tuetue.vn`
- **API runtime aliases:** machine-facing runtime, backend core, API runtime, core backend surface

## Canonical chronology
- **Memory system audit written on:** `2026-04-07`
- **4-layer memory benchmark completed on:** `2026-04-09`
- **What happened first?** The memory system audit happened before the 4-layer memory benchmark.
- **What happened after the 2026-04-09 domain architecture update?** `console.tuetue.vn` went live at root, signup/login/dashboard worked end-to-end, docs were synced, and customer connection info was published.

## Canonical boundary decision
- **Decision:** Do not put quota, billing, or core backend business logic inside WordPress.
- **Reason:** WordPress remains public-site/content/docs/marketing while FastAPI backend APIs remain the business-logic core.

## Memory runtime roles
- **Live primary recall:** `memory_search`
- **Main shadow challenger:** `RAG-V2 8075`
- **Archive retriever:** `legacy RAG archive`
- **Research lane:** `RAG-V2.3 research`
