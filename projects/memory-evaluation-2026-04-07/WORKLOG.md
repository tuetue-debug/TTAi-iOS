# WORKLOG - Memory Evaluation Work Package

## 2026-04-07

### Established context
- Paused deeper auth/deploy progression because memory reliability issues were creating workflow discontinuity.
- Confirmed that memory stabilization had become prerequisite infrastructure work.

### Audit and source-of-truth decisions
- Audited current memory architecture across markdown, OpenClaw `memory_search`, and TTAi RAG.
- Confirmed markdown memory as the authoritative source of truth.
- Defined retrieval precedence: `memory_search` -> direct markdown read -> TTAi RAG -> local model synthesis.

### Data hygiene and ingest alignment
- Repaired `memory/2026-03-20.md` after backup due to Vietnamese encoding corruption.
- Deferred `memory/2026-03-30.md` due to severe corruption and structural damage.
- Confirmed `scripts/memory_ingest.py` as canonical parser.
- Added safe exclusion support for ingest/reindex.
- Reindexed memory/RAG while excluding the deferred corrupted file.

### Evaluation design
- Confirmed Gemma 3:4b should be post-retrieval only.
- Defined that confidence should be treated probabilistically rather than as a binary judgment.
- Chosen evaluator dimensions:
  - groundedness
  - coverage
  - consistency
  - disagreement
  - retrieval strength
  - criticality
- Chosen decision states:
  - accept
  - review
  - fallback
- Chosen escalation rule: fallback to ChatGPT only on the same evidence bundle when risk is too high.

### Packaging work
- Created dedicated project folder `projects/memory-evaluation-2026-04-07/`.
- Added project README.
- Added task spec.
- Added this worklog.

### Current state at packaging time
- Design/framework is stabilized enough to stop re-debating fundamentals.
- The remaining work is implementation/tuning, not architecture discovery.
- This package can now sit alongside the auth/backend work without blocking it.

### Private Gemma/Ollama runtime separation
- Confirmed existing public/default Ollama service `OllamaServe` is listening on `11434`.
- Created `automation/start-ollama-memory-instance.ps1` to launch a separate memory-only Ollama process.
- Started and validated a separate local-only instance on `127.0.0.1:11435`.
- Verified both `11434` and `11435` respond to `/api/tags` successfully.
- Decision frozen: keep `11434` for public/default use and reserve `127.0.0.1:11435` for the memory-evaluation path.
