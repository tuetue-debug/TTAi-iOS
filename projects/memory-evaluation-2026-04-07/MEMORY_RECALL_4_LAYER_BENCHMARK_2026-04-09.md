# MEMORY RECALL 4-LAYER BENCHMARK — 2026-04-09

## Scope
Official comparison across four current memory recall layers:
1. OpenClaw `memory_search`
2. TTAi RAG live service on `8075`
3. RAG-V2 shadow path
4. RAG-V2.3 structured/prototype benchmark path

## Test queries
1. What decision was made about port 8000?
2. What file was deferred in the memory cleanup work and why?
3. What role should Gemma 3:4b play in the memory system?
4. What was upgraded into RAG-V2.3?

## Environment notes
- `memory_search` = live OpenClaw primary recall path
- `RAG 8075` = live supplemental semantic retrieval service
- `RAG-V2` = shadow/evidence-first prototype via `parallel_memory_shadow.py`
- `RAG-V2.3` = structured extraction/promotion/provenance benchmark via `rag_v2_3_benchmark.py`
- Benchmark date/time: 2026-04-09 23:10–23:15 ICT

## Official comparison table

| Query | memory_search | RAG 8075 | RAG-V2 | RAG-V2.3 | Winner |
|---|---|---|---|---|---|
| Port 8000 decision | Strong: returns governance/decision memory and correct direction | Weak: drifts into port incident/service logs | Strong: accept/high, evidence_count=3 | Weak: fallback/low, evidence_count=0 | memory_search / RAG-V2 |
| Deferred cleanup file | Strong: returns `memory/2026-03-30.md` + why deferred | Weak: drifts into memory-rag-wordpress / ingest results | Strong: accept/high, evidence_count=7 in shadow run | Not covered in current v2.3 benchmark set | memory_search / RAG-V2 |
| Gemma 3:4b role | Strong: returns post-retrieval synthesis/rerank role | Weak: drifts into model runtime/performance logs | Strong: accept/high, evidence_count=5 | Weak: fallback/low, evidence_count=0 | memory_search / RAG-V2 |
| What changed in RAG-V2.3 | Good if query hits docs/memory records, but less specialized than benchmark path | Weak-to-medium, depends on keyword coincidence | Strong: accept/high, evidence_count=2 | Medium: review/medium, evidence_count=1 | RAG-V2 |

## Layer-by-layer assessment

### 1. OpenClaw `memory_search`
**Strengths**
- Best overall real-world recall for decisions, dates, preferences, and project memory.
- Closest to markdown source-of-truth workflow.
- Strongest current live path for answering memory questions safely.

**Weaknesses**
- Depends on current embedding/index freshness.
- Still benefits from direct markdown read for fresh/high-stakes answers.

**Current rank:** #1

### 2. TTAi RAG live (`8075`)
**Strengths**
- Live running service.
- Useful as supplemental semantic retrieval.
- Can retrieve broad related memory around topics.

**Weaknesses**
- Drifts toward operational logs and keyword collisions.
- Weaker than `memory_search` for decision-style questions.
- Previously noted as healthy but stale around last ingest state 2026-04-05.

**Current rank:** #3

### 3. RAG-V2
**Strengths**
- Strong evidence-first behavior in shadow mode.
- Much better than RAG 8075 for decision memory and architectural intent.
- Consistently returned accept/high on tested governance-style queries.

**Weaknesses**
- Still prototype/shadow, not live production path.
- Needs broader benchmark coverage before promotion.

**Current rank:** #2

### 4. RAG-V2.3
**Strengths**
- Best long-term design direction.
- Adds structured extraction, promotion, and provenance.
- Better future path for debugging, traceability, and training assets.

**Weaknesses**
- Current promoted/structured candidate set is too sparse.
- Underperforms V2 on current benchmark queries.
- Not mature enough for live recall use yet.

**Current rank:** #4

## Benchmark conclusion

### Ranked order right now
1. `memory_search`
2. `RAG-V2`
3. `RAG 8075`
4. `RAG-V2.3`

### Main takeaway
- `memory_search` remains the best live recall path.
- `RAG-V2` is the best RAG-family candidate for near-term advancement.
- `RAG 8075` is useful but should stay supplemental.
- `RAG-V2.3` is strategically promising but data-thin today.

## Recommendation
- Keep `memory_search` as primary/live recall.
- Continue `RAG-V2` in shadow + broader benchmark mode.
- Keep `RAG 8075` as supplemental semantic retrieval only.
- Invest in extraction/promotion/provenance density before evaluating V2.3 for live adoption.
