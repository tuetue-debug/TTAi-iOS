# 8075 Compatibility Surface Notes — 2026-04-10

## Purpose
This folder now has the foundation for treating port `8075` as a stable public compatibility surface.

## Added pieces
- `rag_service_config.py` = explicit runtime/config metadata for the public 8075 surface
- `compatibility_adapter.py` = maps backend retrieval outputs into the legacy 8075 response contract

## Intent
These files do not force a live cutover on their own.
They prepare the codebase so `rag_service.py` becomes a stable wrapper while retrieval internals evolve behind it.

A new internal backend path now exists for shadow wiring:
- `rag_v2_backend.py` = lightweight evidence-first backend that can sit behind the compatibility surface without changing the public API.

## Stable public contract to preserve
- `GET /health`
- `GET /stats`
- `POST /search`
- `POST /context`

## Why this matters
This design lets callers keep using 8075 while the internal retrieval engine can later move from legacy RAG toward `RAG-V2 8075`.
