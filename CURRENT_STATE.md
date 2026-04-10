# CURRENT_STATE.md

## TTAi Current State
- **Primary blocker:** Resolve SSH authentication / hanging connection issue with `vannt-work-op` (current recorded primary blocker in curated memory)
- **Current focus:** Stabilize and document memory system direction; maintain TTAi domain architecture clarity; keep `memory_search` as live primary while promoting `RAG-V2 8075` as shadow challenger
- **Canonical domains:**
  - `console.tuetue.vn` = canonical developer portal / API console
  - `api.tuetue.vn` = machine-facing runtime / backend core
  - `control.tuetue.vn` = internal admin/operator surface
  - `chat.tuetue.vn` = end-user product surface
- **Last major milestone:** Real-query memory benchmark now completed through Batch 3, with official result docs and synthesis notes written on 2026-04-10
- **Next planned action:** Formalize hybrid memory trial rules, harden `memory_search`, and treat `RAG-V2 8075` as the main shadow challenger

## Memory System Current State
- **Live primary recall:** `memory_search`
- **Main shadow challenger / now live compatibility-surface backend on port 8075:** `RAG-V2 8075`
- **Legacy backup/archive retriever:** `legacy RAG archive`
- **Research lane:** `RAG-V2.3 research`
- **Current evaluation status:**
  - Batch 1 winner: `memory_search`
  - Batch 2 winner: `RAG-V2 8075`
  - Batch 3 winner: `RAG-V2 8075`
- **Current strategic posture:** keep `memory_search` live as primary memory path; run port `8075` on compatibility surface with backend `rag_v2`; keep legacy RAG demoted to archive-only; keep RAG-V2.3 in research
- **Cutover milestone (2026-04-10):** port `8075` now proves `backend = rag_v2`, `backend_active = RAGV2ShadowBackend`, and `build_marker = rag-service-build-d68cd55-marker-1`
- **Key operational lesson:** the main blocker was an orphan Python process (`PID 7696`) holding port `8075`, not the managed service itself
- **Next memory work:** Improve `memory_search` with canonical current-state memory, chronology markers, and alias wording; continue focused evaluation only on `memory_search` vs `RAG-V2 8075`

## Canonical Memory Statements
- **Decision:** `memory_search` remains the live primary recall path.
- **Decision:** `RAG-V2 8075` becomes the main shadow challenger and likely future hybrid candidate.
- **Decision:** legacy RAG is no longer a primary-candidate system and should be treated as archive/backup only.
- **Decision:** `RAG-V2.3 research` remains a future-looking experiment and is not a live candidate now.
- **Reason:** Across three practical batches, `memory_search` remained the safest trust anchor, while `RAG-V2 8075` repeatedly won several practical query families.
