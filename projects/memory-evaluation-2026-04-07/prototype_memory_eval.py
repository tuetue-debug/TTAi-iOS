from pathlib import Path
from datetime import datetime
import json

WORKSPACE = Path(r"C:\Users\vannt-pc\.openclaw\workspace")
TODAY_FILE = WORKSPACE / "memory" / "2026-04-07.md"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
OUTPUT_FILE = WORKSPACE / "projects" / "memory-evaluation-2026-04-07" / "prototype_last_run.json"

TARGETS = [
    {
        "query": "What decision was made about port 8000?",
        "criticality": "high",
        "patterns": ["port 8000", "không động vào port 8000", "khong dong vao port 8000"]
    },
    {
        "query": "What file was deferred in the memory cleanup work and why?",
        "criticality": "medium",
        "patterns": ["2026-03-30.md", "deferred", "severely corrupted", "dedicated recovery"]
    },
    {
        "query": "What role should Gemma 3:4b play in the memory system?",
        "criticality": "medium",
        "patterns": ["Gemma 3:4b", "post-retrieval", "synthesis", "rerank"]
    },
]


def extract_matching_lines(path: Path, patterns):
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    matches = []
    for idx, line in enumerate(text, start=1):
        line_lower = line.lower()
        if any(p.lower() in line_lower for p in patterns):
            start = max(1, idx - 1)
            end = min(len(text), idx + 2)
            snippet = "\n".join(text[start-1:end])
            matches.append({"path": str(path), "line": idx, "snippet": snippet})
    return matches


def assess(matches, criticality):
    count = len(matches)
    retrieval_strength = min(1.0, 0.35 + 0.2 * count) if count else 0.0
    groundedness = 0.9 if count >= 1 else 0.2
    coverage = 0.85 if count >= 2 else (0.65 if count == 1 else 0.2)
    consistency = 0.85 if count >= 2 else 0.7 if count == 1 else 0.2
    disagreement = 0.15 if count >= 1 else 0.8
    criticality_boost = {"low": 0.0, "medium": 0.5, "high": 1.0}.get(criticality, 0.5)
    risk_score = round(
        0.30 * (1 - groundedness)
        + 0.20 * (1 - coverage)
        + 0.15 * (1 - consistency)
        + 0.15 * disagreement
        + 0.10 * (1 - retrieval_strength)
        + 0.10 * criticality_boost,
        4,
    )
    if count == 0:
        decision = "fallback"
    elif risk_score < 0.30:
        decision = "accept"
    elif risk_score <= 0.55:
        decision = "review"
    else:
        decision = "fallback"
    return {
        "retrieval_strength": retrieval_strength,
        "groundedness": groundedness,
        "coverage": coverage,
        "consistency": consistency,
        "disagreement": disagreement,
        "risk_score": risk_score,
        "decision": decision,
    }


def main():
    results = []
    for target in TARGETS:
        matches = []
        matches.extend(extract_matching_lines(TODAY_FILE, target["patterns"]))
        matches.extend(extract_matching_lines(MEMORY_FILE, target["patterns"]))
        assessment = assess(matches, target["criticality"])
        results.append({
            "query": target["query"],
            "criticality": target["criticality"],
            "matches": matches[:6],
            "assessment": assessment,
        })
    payload = {
        "timestamp": datetime.now().isoformat(),
        "mode": "safe-local-prototype",
        "results": results,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
