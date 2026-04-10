# Hybrid Memory Trial Plan — 2026-04-10

## Objective
Safely evolve the memory system without losing the trust advantages of the current live path.

## Official operating posture
- `memory_search` = **live primary recall path**
- `RAG-V2 8075` = **main shadow challenger**
- `legacy RAG archive` = **backup/archive/regression-only retriever**
- `RAG-V2.3 research` = **structured-memory research lane only**

Markdown memory files remain authoritative.

---

## Why this plan exists
After three real-query benchmark batches:
- `memory_search` remained the safest live baseline, especially for governance/policy/boundary questions.
- `RAG-V2 8075` repeatedly outperformed the other systems on next-step, project-state, timeline/date, ownership, blocker, chronology, and continuity recall.
- `legacy RAG archive` drifted too often to remain a serious candidate for live primary recall.
- `RAG-V2.3 research` remained too sparse for practical recall.

The goal is therefore **not** to replace `memory_search` immediately.
The goal is to define a controlled hybrid trial where `RAG-V2 8075` can challenge or augment `memory_search` only where it has earned that role.

---

## Query-family routing rules

### Family A — Governance / policy / boundary / why
Examples:
- WordPress vs backend business logic
- why a file was deferred
- architecture boundary decisions
- audit/governance questions

**Routing:**
- `memory_search` leads
- `RAG-V2 8075` runs only as challenger/support
- if disagreement exists, verify markdown authority directly

### Family B — Next-step / project-state / blocker / continuity
Examples:
- current blocker
- current focus
- next planned action
- what happened after X

**Routing:**
- run `memory_search` + `RAG-V2 8075`
- allow `RAG-V2 8075` to lead when evidence is clearly stronger
- include provenance in the answer

### Family C — Timeline / date / chronology
Examples:
- what happened first
- when X was completed
- what came after Y

**Routing:**
- run both
- allow `RAG-V2 8075` to lead only when chronology evidence is explicit and stable
- if weak chronology evidence, fall back to markdown verification

### Family D — Ownership / entity / repo / account / role
Examples:
- GitHub repo/account ownership
- canonical domain roles
- current system ownership facts

**Routing:**
- prefer curated memory (`MEMORY.md`, `CURRENT_STATE.md`) when available
- allow `RAG-V2 8075` to lead only when it retrieves those curated sources clearly

---

## Lead / challenge / fallback rules

### `memory_search` wins by default when:
- the query belongs to Family A
- `RAG-V2 8075` is only review/medium confidence
- evidence from `RAG-V2 8075` is thin or noisy
- the two systems disagree on the answer

### `RAG-V2 8075` may lead when all are true:
1. query belongs to Family B, C, or D
2. `RAG-V2 8075` returns accept/high confidence
3. evidence is explicit and reasonably authoritative
4. answer does not conflict with `memory_search`

### Disagreement handling
If `memory_search` and `RAG-V2 8075` disagree:
- do not auto-promote `RAG-V2 8075`
- mark the answer as needing verification
- verify directly against markdown authority

---

## Practical answer modes

### Mode 1 — `memory_search`-led
Use for governance/policy/boundary/why questions.

### Mode 2 — `RAG-V2 8075`-led with verification
Use for next-step/project-state/timeline/blocker/continuity/entity questions when it clearly wins.

### Mode 3 — verification mode
Use when systems conflict or chronology is ambiguous.

---

## Hardening work required for `memory_search`
The trial is not only about giving more work to `RAG-V2 8075`.
It also requires improving the current strengths and weaknesses of `memory_search`.

### Hardening priorities
1. Create `CURRENT_STATE.md`
2. Add canonical memory blocks to `MEMORY.md`
3. Add chronology markers to key benchmark/decision docs
4. Add alias wording for important domain/surface concepts
5. Keep major decisions short, explicit, and retrieval-friendly

---

## Success criteria for future promotion decisions
Do not consider broader promotion of `RAG-V2 8075` unless:
- it keeps outperforming across several additional real-query batches
- it does not regress badly on trust-sensitive questions
- chronology/date recall remains stable
- disagreement rate remains manageable
- provenance remains easy to inspect

---

## Near-term execution order
1. Formalize naming and runtime roles
2. Harden `memory_search` with curated state and canonical statements
3. Reassign port 8075 identity to `RAG-V2 8075`
4. Move legacy RAG into archive/backup role
5. Continue focused benchmark work only on `memory_search` vs `RAG-V2 8075`
6. Start selective hybrid trial later if performance remains stable

---

## Bottom line
This plan protects trust first.
It lets `RAG-V2 8075` earn more responsibility only where benchmark evidence says it should, while keeping `memory_search` as the safe live anchor.
