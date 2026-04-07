from pathlib import Path
from datetime import datetime
import json

WORKSPACE = Path(r"C:\Users\vannt-pc\.openclaw\workspace")
PROJECT = WORKSPACE / "projects" / "memory-evaluation-2026-04-07"
TODAY_FILE = WORKSPACE / "memory" / "2026-04-07.md"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
SHADOW_LOG = PROJECT / "parallel_memory_shadow_last_run.json"

QUERIES = [
    "What decision was made about port 8000?",
    "What file was deferred in the memory cleanup work and why?",
    "What role should Gemma 3:4b play in the memory system?"
]

PATTERN_MAP = {
    QUERIES[0]: ["port 8000", "không động vào port 8000", "khong dong vao port 8000"],
    QUERIES[1]: ["2026-03-30.md", "deferred", "severely corrupted", "recovery"],
    QUERIES[2]: ["Gemma 3:4b", "post-retrieval", "synthesis", "rerank"],
}


def scan(path: Path, patterns):
    if not path.exists():
        return []
    out = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if any(p.lower() in low for p in patterns):
            out.append({"path": str(path), "line": i, "text": line.strip()})
    return out


def decide(matches, query):
    count = len(matches)
    if count >= 2:
        decision = "accept"
        confidence = "high"
    elif count == 1:
        decision = "review"
        confidence = "medium"
    else:
        decision = "fallback"
        confidence = "low"
    return {
        "query": query,
        "evidence_count": count,
        "decision": decision,
        "confidence": confidence,
        "matches": matches[:8],
    }


def main():
    results = []
    for q in QUERIES:
        patterns = PATTERN_MAP[q]
        matches = scan(TODAY_FILE, patterns) + scan(MEMORY_FILE, patterns)
        results.append(decide(matches, q))
    payload = {
        "timestamp": datetime.now().isoformat(),
        "mode": "shadow-parallel-memory-pipeline",
        "non_intrusive": True,
        "results": results,
    }
    SHADOW_LOG.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
