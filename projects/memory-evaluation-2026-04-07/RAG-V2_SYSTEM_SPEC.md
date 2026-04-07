# RAG-V2 SYSTEM SPEC

## Name
**RAG-V2 — Evidence-First Memory RAG Pipeline**

## Definition
RAG-V2 is the upgraded memory architecture that keeps retrieval at the center, but adds source verification, evidence bundling, explicit confidence/risk judgment, and selective synthesis/fallback.

## Purpose
- improve grounding and decision reliability
- make same-day/high-criticality memory answers safer
- preserve RAG while reducing weakly grounded outputs

## Core flow
1. retrieve candidate memory evidence
2. verify source-of-truth markdown directly when query is fresh/high-criticality or retrieval is weak
3. assemble compact evidence bundle
4. score groundedness/coverage/consistency/disagreement/retrieval strength/criticality
5. choose `accept` / `review` / `fallback`
6. synthesize with Gemma or GPT only after evidence assembly

## Typical properties
- evidence-first
- source-of-truth aware
- explicit risk scoring
- controlled fallback behavior
- safe shadow-mode rollout possible

## Strengths
- better for same-day and operational questions
- more resistant to weak one-shot retrieval
- provides an auditable reasoning structure
- safer path for future automation and training-data generation

## Weaknesses / current gaps
- more complex than RAG-V1
- requires disciplined evidence assembly
- production orchestration is not fully built yet
- threshold tuning still needed on broader query sets

## Components in the current environment
- markdown memory as source of truth
- OpenClaw `memory_search` as primary recall layer
- TTAi RAG (`8075`) as supplemental retrieval layer
- private Gemma runtime on `127.0.0.1:11435` for post-retrieval tasks
- GPT fallback/judge path for high-confidence escalation when needed
- shadow parallel prototype path for safe evaluation

## Best use cases
- high-criticality memory questions
- same-day operational recall
- decision support where groundedness matters
- comparative evaluation against older memory behavior

## Current status
RAG-V2 is running in safe shadow/prototype mode, not full production replacement.

## Strategic role going forward
- main candidate for next-generation memory path
- evaluation harness for shadow testing on current OpenClaw usage
- better foundation for building future training/evaluation corpora
