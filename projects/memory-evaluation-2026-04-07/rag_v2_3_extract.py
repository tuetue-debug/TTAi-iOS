from pathlib import Path
from datetime import datetime
import json
import re

WORKSPACE = Path(r"C:\Users\vannt-pc\.openclaw\workspace")
MEMORY_TODAY = WORKSPACE / "memory" / "2026-04-08.md"
PROJECT = WORKSPACE / "projects" / "memory-evaluation-2026-04-07"
OUT_CANDIDATES = PROJECT / "rag_v2_3_candidates.jsonl"
OUT_PROMOTIONS = PROJECT / "rag_v2_3_promotions.jsonl"
OUT_PROVENANCE = PROJECT / "rag_v2_3_provenance.jsonl"

RULES = [
    ("decision", ["decision:", "quyết định", "quyet dinh", "đã chốt", "freeze"]),
    ("blocker", ["blocker", "blocked", "vướng", "vuong"]),
    ("next_step", ["next step", "bước tiếp", "buoc tiep", "sẽ", "se "]),
    ("project_state", ["status:", "trạng thái", "trang thai", "completed", "in progress"]),
    ("preference", ["prefers", "thích", "thich", "ưu tiên", "uu tien"]),
]


def classify(text):
    low = text.lower()
    for ctype, pats in RULES:
        if any(p in low for p in pats):
            return ctype
    return None


def promote(candidate_type, importance, operational_criticality):
    if candidate_type in {"decision", "blocker"} and operational_criticality == "high":
        return "promote_long_term"
    if importance in {"high", "critical"}:
        return "structured_store"
    return "daily_only"


def main():
    if not MEMORY_TODAY.exists():
        print(json.dumps({"status": "no_today_file", "path": str(MEMORY_TODAY)}))
        return

    lines = MEMORY_TODAY.read_text(encoding="utf-8", errors="replace").splitlines()
    created = 0
    now = datetime.now().isoformat()
    for idx, line in enumerate(lines, start=1):
        text = line.strip()
        if len(text) < 24:
            continue
        candidate_type = classify(text)
        if not candidate_type:
            continue
        importance = "high" if candidate_type in {"decision", "blocker", "project_state"} else "medium"
        operational_criticality = "high" if candidate_type in {"decision", "blocker"} else "medium"
        candidate = {
            "id": f"v23-{idx}",
            "timestamp": now,
            "source_context": "memory/2026-04-08.md",
            "candidate_type": candidate_type,
            "subject": text[:80],
            "summary": text[:180],
            "detail": text,
            "importance": importance,
            "freshness": "high",
            "stability": "tentative",
            "user_specificity": "medium",
            "operational_criticality": operational_criticality,
            "sources": [{"path": str(MEMORY_TODAY), "line": idx, "snippet": text}],
        }
        promotion_decision = promote(candidate_type, importance, operational_criticality)
        promotion = {
            "candidate_id": candidate["id"],
            "timestamp": now,
            "decision": promotion_decision,
            "reason": f"type={candidate_type}; importance={importance}; operational_criticality={operational_criticality}"
        }
        provenance = {
            "candidate_id": candidate["id"],
            "timestamp": now,
            "extraction_method": "rule-based",
            "verification_status": "verified_markdown",
            "retrieval_path": ["daily_markdown"],
            "risk_score": 0.2,
            "version": "RAG-V2.3"
        }
        with OUT_CANDIDATES.open("a", encoding="utf-8") as f:
            f.write(json.dumps(candidate, ensure_ascii=False) + "\n")
        with OUT_PROMOTIONS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(promotion, ensure_ascii=False) + "\n")
        with OUT_PROVENANCE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(provenance, ensure_ascii=False) + "\n")
        created += 1

    print(json.dumps({
        "status": "ok",
        "version": "RAG-V2.3",
        "created_candidates": created,
        "files": {
            "candidates": str(OUT_CANDIDATES),
            "promotions": str(OUT_PROMOTIONS),
            "provenance": str(OUT_PROVENANCE)
        }
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
