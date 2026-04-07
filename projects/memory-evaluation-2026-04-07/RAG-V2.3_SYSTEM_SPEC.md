# RAG-V2.3 SYSTEM SPEC

## Name
**RAG-V2.3 — Evidence-First Memory RAG with Structured Extraction, Promotion, and Provenance**

## Definition
RAG-V2.3 extends RAG-V2 by adding three explicit memory quality layers:
1. **Structured Extraction**
2. **Promotion**
3. **Provenance**

The goal is to reduce memory continuity loss, improve trust in recall, and create better-quality evaluation/training assets without destabilizing the current system.

## Why V2.3 exists
RAG-V2 improved retrieval discipline and evidence-based answering, but the current pain remains:
- important facts can still remain buried in raw logs
- not enough memory is intentionally promoted
- answer traces are not explicit enough for debugging/training

RAG-V2.3 addresses those directly.

## Core flow
1. capture important interaction / summary / memory event
2. extract structured memory candidates
3. score and promote selected items
4. store provenance with evidence route and decision context
5. feed promoted/structured memory into future RAG-V2 retrieval and evaluation paths

## The three new layers

### 1. Structured Extraction
Convert important raw interaction material into typed memory candidates:
- decision
- preference
- blocker
- next_step
- project_state
- relationship_fact

### 2. Promotion
Decide where each candidate belongs:
- daily log only
- long-term curated memory
- structured sidecar memory store
- benchmark/evaluation candidate set
- training candidate set

### 3. Provenance
Record how a memory or answer was formed:
- source files/snippets
- retrieval path
- verification status
- scoring/decision
- timestamp/version metadata

## Relationship to prior versions
### RAG-V1
retrieval-first memory pipeline

### RAG-V2
retrieve -> verify -> bundle -> score -> answer

### RAG-V2.3
retrieve -> verify -> bundle -> score -> answer
plus
extract -> promote -> trace

## Operating mode
Initial deployment mode should be:
- shadow / parallel / non-intrusive
- no live-path replacement until evaluated

## Strategic value
- better memory continuity for the human
- easier debugging when memory answers are wrong
- structured material for evaluation and future training
- stronger path toward graph-aware/context-aware memory later
