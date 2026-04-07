# RAG Evaluation and Training Plan

## Objective
Evaluate RAG-V1 and RAG-V2 on the current OpenClaw environment and use the results to build a higher-quality future training/evaluation asset.

## Important safety rule
Testing should occur on the current OpenClaw system in **shadow / evaluation mode**, not by replacing the live memory path immediately.

## Why this is a good idea
Yes, this is a strong direction if done carefully.
Because:
- real OpenClaw usage provides authentic memory questions
- V1 vs V2 comparison produces grounded evaluation data
- disagreements/errors can become future training examples
- the system can improve without risking current live behavior

## Recommended testing method
### Phase 1 - Observation
- collect representative memory queries from current OpenClaw usage
- run RAG-V1 and RAG-V2 side by side
- log evidence, answers, confidence, and discrepancies

### Phase 2 - Evaluation
- score quality dimensions:
  - groundedness
  - coverage
  - consistency
  - freshness handling
  - hallucination risk
  - usefulness

### Phase 3 - Training/Eval dataset preparation
- convert comparisons into structured examples:
  - query
  - evidence bundle
  - V1 output
  - V2 output
  - judge result
  - preferred answer
  - failure tags

### Phase 4 - Future model/training use
- use dataset for prompt tuning, evaluation benchmarks, or supervised preference datasets
- do not use raw logs blindly; curate first

## What must remain true
- markdown remains source of truth
- evaluation should be reproducible
- shadow mode first
- no regression to current live path without evidence

## Conclusion
This direction is sound.
The right move is not “replace now”, but “evaluate systematically on the current OpenClaw system, then promote the better behavior with evidence.”
