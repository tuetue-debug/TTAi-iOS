# RAG Evaluation Record Template

## Query metadata
- Query ID:
- Timestamp:
- Source session/context:
- Query text:
- Query class: (historical / same-day / operational / high-criticality / preference / todo / decision)

## Ground truth / authority
- Primary authoritative sources:
- Secondary sources:
- Freshness requirement: (low / medium / high)

## RAG-V1 run
- Retrieval summary:
- Answer draft:
- Confidence impression:
- Observed weaknesses:

## RAG-V2 run
- Retrieval summary:
- Verification performed:
- Evidence bundle summary:
- Scoring summary:
- Decision: (accept / review / fallback)
- Answer draft:
- Observed weaknesses:

## Comparison
- Better answer: (V1 / V2 / mixed / neither)
- Why:
- Hallucination risk comparison:
- Freshness handling comparison:
- Groundedness comparison:

## Training / eval labeling
- Preferred output:
- Failure tags:
- Keep for benchmark set: (yes / no)
- Keep for training candidate set: (yes / no)
- Notes:
