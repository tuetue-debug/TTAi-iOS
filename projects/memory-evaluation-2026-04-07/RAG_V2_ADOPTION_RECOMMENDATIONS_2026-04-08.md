# RAG-V2 Adoption Recommendations - 2026-04-08

## Goal
Identify the easiest, highest-impact improvements that can be added to RAG-V2 without destabilizing the current system.

## Principle
Prioritize **adjacent layers** that improve recall quality and continuity without replacing the source-of-truth or current runtime.

## Highest-value adopt-now additions

### 1. Structured memory extraction layer
**What it is:**
After important sessions/interactions, automatically extract a small set of structured memory candidates:
- decision
- preference
- project state
- blocker
- next step
- relationship/fact

**Why it helps:**
This directly attacks the "I told you this before, why don't you remember?" problem.
It converts raw chat into durable memory units instead of relying only on future retrieval from noisy logs.

**Why it fits us:**
- easy to run beside markdown logs
- can write into a structured JSONL or sidecar file
- does not replace markdown authority
- ideal companion to RAG-V2

**Impact:** Very High
**Difficulty:** Medium
**Adoption risk:** Low

---

### 2. Memory importance scoring + promotion layer
**What it is:**
Assign each memory candidate scores such as:
- importance
- freshness
- stability
- user-specificity
- operational criticality

Then decide whether it stays in daily log only, gets promoted to long-term memory, or becomes benchmark/eval material.

**Why it helps:**
RAG systems often fail because everything is stored similarly and not enough is promoted intentionally.

**Why it fits us:**
This works perfectly with current markdown + MEMORY.md hierarchy.

**Impact:** Very High
**Difficulty:** Medium
**Adoption risk:** Low

---

### 3. Memory trace / provenance layer
**What it is:**
For each answer or retrieved memory bundle, keep trace fields like:
- source files used
- exact snippets used
- retrieval method used
- confidence/risk decision
- whether direct verification happened

**Why it helps:**
This improves trust, debugging, dataset creation, and future training/eval quality.

**Why it fits us:**
This is a natural extension of RAG-V2 and one of the easiest upgrades.

**Impact:** High
**Difficulty:** Low
**Adoption risk:** Very Low

---

### 4. Memory bundle compression layer
**What it is:**
Create compact normalized memory bundles from larger evidence sets before passing to synthesizer/judge.

**Why it helps:**
- lower token cost
- lower latency
- less prompt clutter
- more consistent synthesis quality

**Why it fits us:**
Can be done with Gemma private runtime or rule-based summarization first.

**Impact:** High
**Difficulty:** Medium
**Adoption risk:** Low

---

### 5. Entity / relationship sidecar graph
**What it is:**
Maintain a lightweight structured sidecar for entities and relationships:
- person -> preference
- project -> status
- system -> port -> service -> host
- decision -> date -> rationale

**Why it helps:**
This is the most important conceptual upgrade borrowed from graph/context-engineering systems.
It helps answer system-wide questions much better than flat retrieval alone.

**Why it fits us:**
Can begin as a simple JSON or JSONL sidecar without building a full graph database.

**Impact:** Very High
**Difficulty:** Medium-High
**Adoption risk:** Medium-Low

---

### 6. Shadow evaluation harness (already started)
**What it is:**
Run V2 beside current behavior and log differences.

**Why it helps:**
Creates objective evidence for upgrades and later training sets.

**Why it fits us:**
Already aligned with current work.

**Impact:** High
**Difficulty:** Low
**Adoption risk:** Very Low

## Best immediate package for us
If we want the maximum quality gain with minimum disruption, the best sequence is:

### Package A - near-term high ROI
1. memory trace / provenance layer
2. structured memory extraction layer
3. memory importance scoring / promotion layer

### Package B - next upgrade
4. memory bundle compression layer
5. lightweight entity/relationship sidecar graph

## What not to do yet
- do not replace markdown authority
- do not move to a heavy external platform immediately
- do not require a full graph database before proving value
- do not tie success to full production automation first

## Final recommendation
The **single most valuable improvement** for our real pain point is:
### structured memory extraction + promotion
because it directly reduces the number of times the human has to reconstruct context manually.

The **best technical complement** after that is:
### provenance + lightweight relationship sidecar
because it improves trust and system-wide recall quality without a dangerous rewrite.
