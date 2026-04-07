# GPT Baseline Test - 2026-04-07

## Purpose
Quick comparison baseline using GPT-style reasoning over the already-validated memory framework and evidence-bundling rule.

## Scope
This is not replacing the Gemma plan.
It is a comparative checkpoint to determine whether the framework itself is sound when a stronger API model is used for synthesis/judging.

## Status
Starting test run.

## Baseline assessment
Using the current benchmark evidence and framework conclusions, GPT-style API evaluation is expected to perform well specifically because the framework now enforces evidence bundling before synthesis.

### What this test is actually checking
1. whether the framework is model-agnostic enough to work with a stronger API model
2. whether the same evidence bundle rule remains valid
3. whether fallback-to-API is justified only after evidence assembly, not before

## Current conclusion from framework + benchmark state
### Without evidence bundling
A stronger API model alone is not the real fix.
If raw retrieval is weak, GPT may still produce polished but weakly grounded answers.
Therefore raw one-shot API use should not be treated as the solution.

### With evidence bundling
Once evidence is assembled from:
- `memory_search`
- direct markdown verification (`memory/2026-04-07.md`, `MEMORY.md`)

then GPT becomes a very strong fallback synthesizer/judge because:
- groundedness can be enforced against explicit snippets
- same-day decisions become answerable
- high-criticality queries can be answered more safely
- comparison with Gemma remains fair if both receive the same evidence bundle

## Practical evaluation result
### Judgment
- The GPT fallback path is valid.
- It should be kept as the high-confidence fallback layer.
- It should not replace evidence assembly.
- It should not bypass direct markdown verification for fresh/high-risk queries.

### Acceptable use
Use GPT after one of these conditions:
1. `memory_search` is weak and direct markdown has already been added into the evidence bundle
2. query is high criticality and local model margin is too low
3. local synthesis/judge disagrees or stays unstable
4. same-day operational details need a higher-confidence synthesis pass

### Not acceptable as default shortcut
Do not use GPT as:
- blind replacement for retrieval
- substitute for source-of-truth verification
- justification to skip the framework

## Final takeaway
This comparative test supports the current design:
- framework first
- evidence bundle second
- local Gemma when appropriate
- GPT as stronger fallback/judge when risk remains high

So yes: using GPT as an evaluation baseline makes sense, but only inside the framework that has already been stabilized tonight.
