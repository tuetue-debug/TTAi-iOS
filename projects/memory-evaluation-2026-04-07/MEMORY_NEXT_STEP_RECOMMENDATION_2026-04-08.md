# Memory Next-Step Recommendation - 2026-04-08

## Priority recommendation
If we are choosing one practical next memory improvement after RAG-V2 foundation work, choose:

### **Structured Memory Extraction + Promotion Pipeline**

## Why this is the right next move
Because the main pain described is not only poor retrieval.
It is failure to preserve and surface important context from prior work consistently.

A structured extraction/promotion pipeline addresses that directly.

## Suggested shape
### Inputs
- daily markdown logs
- session summaries
- important chat turns

### Outputs
- memory candidates JSONL
- promoted long-term memory candidates
- entity/relation sidecar updates
- benchmark/eval candidate labels

## Why not jump straight to something heavier
A graph DB or external memory platform may help later, but this pipeline gives immediate value with less disruption and much better fit to the current system.

## Recommendation
Implement this before any major memory platform migration.
