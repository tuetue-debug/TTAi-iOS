# RAG-V2.3 Minimum Upgrade Plan

## Goal
Push RAG-V2.3 from bootstrap state toward a more meaningfully usable state without destabilizing the live system.

## Three smallest high-value upgrades

### 1. Attach extraction to session-summary / daily memory workflow
Why:
- makes extraction recurring instead of one-off
- turns RAG-V2.3 into an actual capture loop

### 2. Use structured/promoted candidates in shadow retrieval
Why:
- makes V2.3 matter during answering, not only during storage
- directly improves same-day recall potential

### 3. Run mini benchmark: V2 vs V2.3
Why:
- creates objective evidence tonight
- validates whether structured capture is already helping

## Success condition tonight
- extraction path exists and runs
- V2.3 can read its own candidate store in shadow mode
- at least a small benchmark exists showing where V2.3 helps or does not help yet
