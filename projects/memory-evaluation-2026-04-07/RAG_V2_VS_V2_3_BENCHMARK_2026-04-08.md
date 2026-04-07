# RAG-V2 vs RAG-V2.3 Benchmark - 2026-04-08

## Purpose
Run a quick benchmark immediately after bootstrapping RAG-V2.3 to assess whether the new structured layers are already improving answerability.

## Result summary
### Query 1 - Port 8000 decision
- **RAG-V2:** accept / high confidence / 3 evidence matches
- **RAG-V2.3:** fallback / low confidence / 0 candidate matches
- **Interpretation:** V2.3 has not yet captured enough structured memory to compete here.

### Query 2 - Gemma role in memory system
- **RAG-V2:** accept / high confidence / 5 evidence matches
- **RAG-V2.3:** fallback / low confidence / 0 candidate matches
- **Interpretation:** same result; V2.3 bootstrap store is still too sparse.

### Query 3 - What was upgraded into RAG-V2.3?
- **RAG-V2:** accept / high confidence / 2 evidence matches
- **RAG-V2.3:** review / medium confidence / 1 candidate match
- **Interpretation:** V2.3 can answer about its own bootstrap event, but not yet broadly.

## Honest conclusion
RAG-V2.3 is **not yet outperforming RAG-V2**.
That is expected and acceptable at this stage because:
- V2.3 has only just been bootstrapped
- structured extraction has not yet accumulated enough promoted memory
- the consumption path is still minimal

## Important positive result
The benchmark confirms that the current evaluation harness is honest.
It does not falsely claim improvement before the data supports it.

## What this means
### RAG-V2
remains the stronger practical memory path right now.

### RAG-V2.3
is a promising upgrade path, but it still needs:
1. more extraction coverage
2. better promotion volume/quality
3. retrieval consumption of structured candidates

## Final judgment tonight
- **RAG-V2.3 bootstrap:** successful
- **RAG-V2.3 benchmark superiority:** not yet demonstrated
- **Strategic value:** still high, because the upgrade path is now real and measurable
