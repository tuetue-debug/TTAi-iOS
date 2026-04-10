# Memory Runtime Roles — 2026-04-10

## Official names from this point onward
- `memory_search`
- `RAG-V2 8075`
- `legacy RAG archive`
- `RAG-V2.3 research`

## Role definitions

### `memory_search`
- Role: live primary recall path
- Strengths: governance, policy, boundary decisions, defer/why rationale, trusted markdown grounding
- Operational status: keep live

### `RAG-V2 8075`
- Role: main shadow challenger
- Strengths: next-step recall, project-state recall, timeline/date recall, ownership recall, blocker recall, continuity recall
- Operational status: keep shadow, likely hybrid candidate later

### `legacy RAG archive`
- Role: backup/archive/regression-only retriever
- Strengths: limited old runtime/service incident lookup
- Weakness: too much drift for practical recent-work recall
- Operational status: do not treat as primary candidate

### `RAG-V2.3 research`
- Role: structured-memory research lane
- Strength: future architecture exploration only
- Weakness: current structured/promoted candidates too sparse for practical recall
- Operational status: do not promote to live

## Port identity rule
- Port `8075` should now be treated conceptually as the service identity for **`RAG-V2 8075`**.
- Any references to the old retriever on this port should be labeled **`legacy RAG archive`** once migration/transition is complete.

## Operational decision summary
- Keep `memory_search` live.
- Keep `RAG-V2 8075` shadow.
- Demote legacy RAG to archive/backup.
- Keep RAG-V2.3 in research.
