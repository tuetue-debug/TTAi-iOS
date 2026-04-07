# Memory System Comparison Matrix - 2026-04-08

## Scope
Compare the current internal memory direction against notable external memory-oriented approaches that are relevant to TTAi / OpenClaw / Tuệ Tuệ.

## Systems compared
- **RAG-V2** (current internal direction)
- **Letta**
- **Zep**
- **Mem0**

## Evaluation criteria
Scored qualitatively for our environment, not in the abstract.

| Criterion | RAG-V2 | Letta | Zep | Mem0 |
|---|---|---|---|---|
| **Fits current OpenClaw/TTAi architecture** | **High** | Medium | Medium | Medium-High |
| **Keeps markdown as source of truth** | **High** | Medium | Medium | Medium |
| **Same-day continuity potential** | Medium-High | High | High | High |
| **Groundedness discipline** | **High** | Medium-High | High | Medium-High |
| **Observability / traceability** | Medium | Medium | High | High |
| **Ease of safe incremental adoption** | **High** | Medium-Low | Medium | Medium-High |
| **Self-host / data control friendliness** | **High** | Medium | Medium | Medium-High |
| **Production maturity as packaged solution** | Low-Medium | Medium-High | High | High |
| **Good for future eval/training dataset generation** | **High** | Medium | High | High |
| **Risk of architectural disruption** | **Low** | Medium-High | Medium | Medium |

## Practical interpretation

### RAG-V2
**Best role:** internal baseline + upgrade path
- strongest fit for current system constraints
- easiest to evolve without breaking current workflows
- weakest point is maturity/observability compared with dedicated memory platforms

### Letta
**Best role:** architecture inspiration for stateful agents
- strong conceptual model for long-lived memory-first agents
- attractive if we later want a dedicated agent runtime with richer state transitions
- heavier architectural shift than we need right now

### Zep
**Best role:** inspiration for context assembly and graph-aware memory
- strongest external reference for "context engineering" direction
- very relevant to our problem of weak/insufficient context assembly
- likely one of the best conceptual upgrades for RAG-V2

### Mem0
**Best role:** memory-layer inspiration for practical adoption
- strongest candidate for incremental memory-layer improvements
- very relevant for compression, observability, and personalization continuity
- easier to borrow ideas from than to replace our whole system

## Overall conclusion
### If the question is "what should we replace RAG-V2 with right now?"
Answer: **nothing**.

### If the question is "what should we learn from to improve RAG-V2 fastest?"
Answer:
1. **Zep** for context assembly / graph-oriented thinking
2. **Mem0** for memory-layer mechanics, observability, compression, and traceability
3. **Letta** for long-lived stateful agent design principles

## Recommendation for us
- keep **RAG-V2** as the working internal memory architecture
- selectively graft in high-value ideas from Zep / Mem0
- defer any full external platform adoption until our topology/control/dashboard work is clearer
