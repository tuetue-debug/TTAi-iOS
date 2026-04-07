# OLLAMA MEMORY SERVICE SETUP

## Goal
Run a dedicated Gemma/Ollama instance for memory-only workloads on a private local port so it does not interfere with the public/default Ollama service.

## Current public state
- Existing Ollama service: `OllamaServe`
- Existing listener: `127/:: :11434`
- This existing service must not be modified for the memory-evaluation package.

## Safe isolation rule
Memory-only Ollama must:
- bind to a different port
- stay local-only (`127.0.0.1`)
- run as a separate process/service
- be treated as auxiliary, not public-facing infrastructure

## Chosen initial port
- `127.0.0.1:11435`

## Why this is safe
- avoids collision with current `11434`
- not exposed publicly when bound to localhost
- easy to target explicitly from future memory tooling
- failure does not require touching the public Ollama service

## Startup script
Use:
- `automation/start-ollama-memory-instance.ps1`

## Startup mode
Phase 1 should be process-based validation first.
Only after that should it become a Windows service.

## Validation checklist
1. confirm public `OllamaServe` remains on `11434`
2. start memory instance on `127.0.0.1:11435`
3. verify listener exists on `11435`
4. verify basic request succeeds
5. verify no public route points to `11435`
6. only then consider service registration

## Validation status on 2026-04-07
- Confirmed existing public/default Ollama service `OllamaServe` remains on port `11434`
- Confirmed separate memory-only instance started on `127.0.0.1:11435`
- Confirmed both `/api/tags` endpoints on `11434` and `11435` respond successfully
- Confirmed memory-only instance is local-only and does not require changing public routing

## Decision frozen
For the memory-evaluation package, the private Gemma/Ollama path is now frozen as:
- public/default Ollama -> `11434`
- memory-only Ollama -> `127.0.0.1:11435`

This separation should remain in place unless a later infrastructure task explicitly revisits it.

## Important rule
Do not repoint existing public clients to the memory-only instance.
It is private support infrastructure for the memory framework only.
