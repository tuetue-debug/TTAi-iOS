# RAG-V2.3 Flow

## Fast summary
RAG-V2.3 keeps RAG-V2 answering logic, but adds a disciplined memory-capture loop.

## Flow A - Answering path
1. retrieve candidate evidence
2. verify markdown when needed
3. bundle evidence
4. score decision risk
5. answer / review / fallback
6. attach provenance trace

## Flow B - Memory capture path
1. observe important interaction or summary
2. extract structured memory candidates
3. score importance / freshness / stability / operational criticality
4. promote to the right destination
5. store provenance
6. make candidates available to future retrieval/eval flows

## Initial rollout
- capture path runs in shadow mode
- promoted outputs are reviewed through logs/files first
- no destructive overwrite of existing memory

## Design rule
Markdown remains the human-readable source of truth.
Structured candidates and provenance are support layers that improve continuity and retrieval quality.
