# RAG-V1 SYSTEM SPEC

## Name
**RAG-V1 — Retrieval-First Memory Pipeline**

## Definition
RAG-V1 is the earlier memory architecture centered on retrieval from indexed memory and direct answer generation from the retrieved context.

## Purpose
- retrieve historical memory
- supply context for answering
- support memory-aware assistant behavior

## Core flow
1. ingest memory into searchable/indexed form
2. retrieve relevant entries
3. pass retrieved context into answer generation
4. return answer

## Typical properties
- retrieval-first
- lightweight context assembly
- limited explicit verification
- limited confidence/risk control

## Strengths
- simple and fast to reason about
- easy to integrate
- good for broad historical retrieval when indexing quality is acceptable

## Weaknesses
- same-day or fresh operational facts can be missed
- weak retrieval can still lead to polished but under-grounded answers
- verification discipline is not explicit enough for high-criticality decisions
- fallback logic is not formally structured

## Components in the current environment
- TTAi RAG service (`8075`)
- indexed memory export flow
- semantic retrieval over memory corpus
- baseline memory-aware answer path

## Best use cases
- low-to-medium criticality recall
- broad semantic search over older memory
- lightweight context augmentation

## Failure modes observed
- retrieval phrasing mismatch
- stale index effects
- same-day operational context not surfaced reliably
- insufficient distinction between source-of-truth and synthesized answer

## Status
RAG-V1 should be preserved as a reference/baseline system for comparison and regression evaluation.

## Strategic role going forward
- baseline for A/B comparison
- reference for measuring improvements in recall quality
- candidate data source for training/evaluation sets
