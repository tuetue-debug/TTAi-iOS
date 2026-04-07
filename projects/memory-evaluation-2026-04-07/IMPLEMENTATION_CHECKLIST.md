# IMPLEMENTATION CHECKLIST - Memory Evaluation Work Package

## Phase 1 - Project organization
- [x] Create dedicated project folder
- [x] Add README
- [x] Add TASK_SPEC
- [x] Add WORKLOG
- [x] Add reference snapshots

## Phase 2 - Design freeze
- [x] Freeze source-of-truth rule
- [x] Freeze retrieval precedence
- [x] Freeze Gemma role as post-retrieval only
- [x] Freeze fallback-on-same-evidence rule
- [x] Freeze risk-score based decision model

## Phase 3 - Prompting and benchmark assets
- [x] Add judge prompt templates
- [x] Add benchmark plan
- [x] Add memory-only Ollama runtime plan
- [ ] Add sample evaluation log template
- [ ] Add threshold tuning notes from real runs

## Phase 4 - Manual validation
- [x] Run benchmark query set with current retrieval stack
- [x] Build evidence bundles for representative weak queries
- [ ] Generate Gemma provisional answers
- [ ] Run judge scoring
- [ ] Trigger ChatGPT fallback only when framework says so
- [ ] Compare outcomes and record false accept / false fallback cases

## Phase 5 - Runtime preparation
- [x] Define launch method for memory-only Ollama instance
- [ ] Define timeout and retry policy
- [ ] Define failure handling path
- [ ] Define logging format for evaluation outcomes

## Phase 6 - Assisted integration
- [ ] Add semi-automatic judge/fallback flow
- [x] Keep direct markdown verification for fresh/high-criticality queries
- [ ] Tune thresholds on real query history
- [ ] Review whether automatic fallback is justified

## Phase 7 - Safe prototype application
- [x] Create a local-only prototype executable path
- [x] Run prototype on representative high-value queries
- [x] Confirm prototype does not affect public/current system
- [ ] Extend prototype to Gemma/GPT orchestration loop

## Exit criteria
- [ ] Framework works on benchmark queries
- [ ] Same-day critical recall is more reliable
- [ ] Fallback is selective, not excessive
- [ ] Package is stable enough that auth/backend work can continue without reopening this design
