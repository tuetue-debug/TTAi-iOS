# PARALLEL MEMORY PIPELINE PLAN - 2026-04-07

## Goal
Run the new memory path in parallel with the current system, safely and without affecting live behavior.

## Core clarification
Yes: the original memory idea is still fundamentally RAG.
But the corrected architecture is **not "LLM instead of RAG"**.
It is:
- markdown memory = source of truth
- retrieval layers = RAG / semantic recall / direct verification
- synthesis layers = Gemma or GPT after retrieval

So the new memory path is still a RAG-oriented system, but with stronger evidence discipline.

## Corrected architecture
### Existing/current memory-related pieces
1. OpenClaw `memory_search`
2. markdown files (`MEMORY.md`, `memory/YYYY-MM-DD.md`)
3. TTAi RAG service on `8075`

### New parallel path
A safe shadow pipeline that does:
1. receive query
2. collect evidence from authoritative markdown and/or memory recall
3. score confidence/risk
4. optionally synthesize with Gemma private runtime (`127.0.0.1:11435`) or GPT fallback
5. write evaluation output only
6. do not override current system answers yet

## Why parallel mode matters
- compare old vs new behavior
- avoid regression in live system
- let us learn thresholds before full adoption

## Relationship to RAG
### What remains RAG
- retrieval from indexed/stored memory
- semantic recall over memory corpus
- context assembly before answer generation

### What is new
- direct markdown verification for fresh/high-criticality cases
- explicit evidence bundle construction
- explicit risk scoring
- selective fallback/judge behavior

## Bottom line
The new system is not abandoning RAG.
It is turning the old memory concept into a more reliable **evidence-first RAG pipeline**.

## Safe rollout plan
### Stage 1 - Shadow mode
- current system continues unchanged
- new pipeline runs separately on selected queries
- output logged only

### Stage 2 - Assisted mode
- new pipeline provides recommendation/confidence beside current answer
- no automatic override yet

### Stage 3 - Selective adoption
- only low-risk/high-confidence query classes may use the new pipeline directly
- high-criticality still reviewed or fallback-routed
