# RAG Evaluation Workflow

## Goal
Create a repeatable way to compare RAG-V1 and RAG-V2 on real OpenClaw memory queries.

## Workflow
1. capture a real query from current usage
2. classify the query type
3. run/observe RAG-V1 behavior
4. run/observe RAG-V2 shadow behavior
5. fill `RAG_EVAL_RECORD_TEMPLATE.md`
6. append summary result to `RAG_EVAL_LOG_2026-04.md`
7. mark whether the case belongs in:
   - benchmark set
   - training candidate set

## Labeling priorities
Prioritize keeping examples where:
- V1 and V2 disagree
- V1 misses same-day context
- V2 improves groundedness
- fallback/review behavior is triggered
- high-criticality answers are involved

## Safety rule
Evaluation should remain non-intrusive unless a later step explicitly promotes V2 into a live assisted path.
