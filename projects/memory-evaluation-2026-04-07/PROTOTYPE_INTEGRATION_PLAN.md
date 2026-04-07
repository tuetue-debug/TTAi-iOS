# PROTOTYPE INTEGRATION PLAN - Memory Evaluation Work Package

## Goal
Apply the memory evaluation framework in a minimal real workflow without touching the current production/public system.

## Safe integration strategy
Do not modify the current assistant runtime, public routes, or core services.
Instead, create a separate prototype utility that:
1. accepts a query,
2. gathers authoritative evidence,
3. applies the framework,
4. produces a recommended decision and answer draft.

## Why this is the right next step
- it proves applicability without risking the live system
- it turns tonight's design into an executable path
- it gives a concrete artifact for further tuning

## Prototype boundaries
### Allowed
- read memory files
- use memory_search results manually or via API-compatible helper later
- use local/private Gemma port or GPT fallback in a controlled manner
- write logs/results into project files

### Not allowed
- changing public Ollama port 11434
- changing production assistant routing
- modifying port 8000 or public TTAi services
- auto-replying into existing user-facing flows

## Prototype deliverable
A local-only utility should produce:
- evidence bundle
- framework assessment
- answer draft
- decision: accept/review/fallback
- notes for tuning

## Evaluation objective
After the prototype works for a few target questions, analyze:
- whether it improves same-day recall
- whether it reduces weak one-shot recall failures
- where thresholds need adjustment
- whether GPT fallback is worth the latency/cost for selected query classes
