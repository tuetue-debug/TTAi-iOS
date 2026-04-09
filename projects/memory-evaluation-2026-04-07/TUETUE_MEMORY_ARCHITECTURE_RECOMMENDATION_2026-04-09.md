# Tuệ Tuệ Memory Architecture Recommendation — 2026-04-09

## Executive recommendation
Use a **3-layer practical memory architecture**:

1. **Markdown memory authority**
2. **OpenClaw `memory_search` as primary live recall**
3. **RAG-V2 as shadow + escalation path**

Keep RAG 8075 as supplemental only.
Keep RAG-V2.3 as the long-term structured-memory upgrade path, not the immediate live replacement.

---

## Recommended architecture

### Layer 0 — Source of truth
Authoritative memory remains:
- `memory/YYYY-MM-DD.md`
- `MEMORY.md`

Why:
- human-readable
- editable
- reviewable
- safest for continuity
- easiest to repair when encoding/index issues happen

### Layer 1 — Primary live recall
Use **OpenClaw `memory_search`** as the default live retrieval path.

Why:
- best current benchmark performance
- strongest recall for decisions/preferences/project facts
- already integrated into assistant workflow
- fits current safety/SOP model

### Layer 2 — Evidence escalation / shadow
Use **RAG-V2** for:
- shadow recall comparisons
- hard memory questions
- governance/decision checks
- evidence bundling for benchmark and evaluation
- future guarded escalation path

Why:
- best-performing RAG-family candidate right now
- better than live RAG 8075 on decision-style recall
- already demonstrates evidence-first behavior

### Layer 3 — Supplemental semantic retrieval
Keep **RAG 8075** as a supplemental semantic memory service only.

Use cases:
- broad topical recall
- related-context expansion
- semantic side-search when `memory_search` is thin

Do not use as primary answering path for high-stakes recall yet.

### Layer 4 — Long-term structured upgrade
Develop **RAG-V2.3** as the next strategic evolution.

Its role is to add:
- structured extraction
- promotion
- provenance
- better traceability
- better future training/eval assets

Do not promote it to live recall until promoted memory density is much stronger.

---

## Operational policy

### Default answer path
1. `memory_search`
2. direct markdown verification if needed
3. optional RAG 8075 semantic supplement
4. optional RAG-V2 shadow/evidence check on difficult cases
5. synthesis/rerank with local model only after retrieval

### High-stakes questions
For decisions, dates, blockers, preferences, and architecture:
- require markdown-backed evidence
- prefer `memory_search` + direct markdown read
- use RAG-V2 only as evidence reinforcement, not sole source

### Fresh/same-day memory
Always prefer:
- today/yesterday markdown
- direct file reads
- then recall tooling

---

## What not to do
- Do not replace markdown memory with vector DB.
- Do not switch live recall to RAG 8075 right now.
- Do not switch live recall to RAG-V2.3 before structured promotion coverage improves.
- Do not let model synthesis answer memory questions without retrieval evidence.

---

## Immediate roadmap

### Now
- keep `memory_search` as primary
- keep RAG 8075 supplemental
- keep RAG-V2 in shadow benchmark mode
- continue documenting benchmark results

### Next
- broaden RAG-V2 benchmark set using real Tuệ Tuệ memory questions
- add explicit scoring/reporting per query class
- define guarded escalation rules from `memory_search` to V2

### Later
- improve V2.3 structured extraction/promotions
- build promoted-memory density
- re-benchmark V2.3 after sidecar memory becomes meaningful

---

## Final recommendation
If the goal is **best practical memory performance now**, choose:
- **Markdown authority + OpenClaw memory_search primary + RAG-V2 shadow**

If the goal is **best long-term architecture**, build toward:
- **Markdown authority + memory_search primary + RAG-V2.3 structured sidecar once mature**

That gives Tuệ Tuệ a memory stack that is:
- safe now
- measurable now
- improvable later
- traceable over time
