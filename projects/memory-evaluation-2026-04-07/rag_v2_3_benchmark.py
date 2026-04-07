from pathlib import Path
from datetime import datetime
import json

WORKSPACE = Path(r"C:\Users\vannt-pc\.openclaw\workspace")
PROJECT = WORKSPACE / "projects" / "memory-evaluation-2026-04-07"
TODAY = WORKSPACE / "memory" / "2026-04-08.md"
YESTERDAY = WORKSPACE / "memory" / "2026-04-07.md"
V23_CANDIDATES = PROJECT / "rag_v2_3_candidates.jsonl"
OUT = PROJECT / "RAG_V2_VS_V2_3_BENCHMARK_2026-04-08.json"

QUERIES = [
    {
        "query": "What decision was made about port 8000?",
        "patterns": ["port 8000", "không động vào port 8000", "khong dong vao port 8000"]
    },
    {
        "query": "What role should Gemma play in the memory system?",
        "patterns": ["Gemma 3:4b", "post-retrieval", "synthesis", "rerank"]
    },
    {
        "query": "What was upgraded into RAG-V2.3?",
        "patterns": ["RAG-V2.3", "Structured Extraction", "Promotion", "Provenance"]
    }
]


def read_lines(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def v2_matches(patterns):
    matches = []
    for path in [TODAY, YESTERDAY]:
        for idx, line in enumerate(read_lines(path), start=1):
            low = line.lower()
            if any(p.lower() in low for p in patterns):
                matches.append({"path": str(path), "line": idx, "text": line.strip()})
    return matches


def v23_matches(patterns):
    matches = []
    if V23_CANDIDATES.exists():
        for line in V23_CANDIDATES.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            blob = json.dumps(item, ensure_ascii=False).lower()
            if any(p.lower() in blob for p in patterns):
                matches.append(item)
    return matches


def decision(count):
    if count >= 2:
        return "accept", "high"
    if count == 1:
        return "review", "medium"
    return "fallback", "low"


def main():
    results = []
    for q in QUERIES:
        v2 = v2_matches(q["patterns"])
        v23 = v23_matches(q["patterns"])
        v2_decision, v2_conf = decision(len(v2))
        v23_decision, v23_conf = decision(len(v23))
        results.append({
            "query": q["query"],
            "v2": {"evidence_count": len(v2), "decision": v2_decision, "confidence": v2_conf},
            "v2_3": {"evidence_count": len(v23), "decision": v23_decision, "confidence": v23_conf},
            "delta": "improved" if len(v23) > len(v2) else "same_or_lower"
        })
    payload = {"timestamp": datetime.now().isoformat(), "results": results}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
