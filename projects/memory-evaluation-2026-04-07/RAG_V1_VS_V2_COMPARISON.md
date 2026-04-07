# RAG-V1 vs RAG-V2 Comparison

## Executive summary
- **RAG-V1** = retrieval-first memory pipeline
- **RAG-V2** = evidence-first memory RAG pipeline

## Architecture difference
### RAG-V1
`retrieve -> answer`

### RAG-V2
`retrieve -> verify -> bundle -> score -> answer`

## Source-of-truth handling
### RAG-V1
- retrieval-driven
- source verification is implicit or inconsistent

### RAG-V2
- markdown is authoritative
- source verification is explicit for fresh/high-impact queries

## Reliability profile
### RAG-V1
- good for broad memory search
- weaker for fresh operational details

### RAG-V2
- stronger for high-stakes or same-day memory answers
- designed to reduce weakly grounded responses

## Model role
### RAG-V1
- model mainly answers from retrieved context

### RAG-V2
- models synthesize only after evidence assembly
- Gemma = post-retrieval synthesis/rerank
- GPT = fallback/judge when needed

## Operational mode
### RAG-V1
- existing/reference path

### RAG-V2
- current shadow/prototype path for safe evaluation

## Upgrade direction
RAG-V2 should be tested against RAG-V1 on the current OpenClaw environment in shadow mode before any deeper adoption.
