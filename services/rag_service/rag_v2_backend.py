from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import re


@dataclass
class EvidenceMatch:
    path: str
    line: int
    text: str


class RAGV2ShadowBackend:
    """Lightweight evidence-first backend wired behind the 8075 compatibility surface.

    This is intentionally conservative: it uses markdown files as the trust anchor,
    produces structured evidence-like search rows, and builds context text from
    compact direct matches. It is suitable as a first internal backend behind the
    public compatibility surface before any live cutover.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.candidate_files = [
            workspace_root / "MEMORY.md",
            workspace_root / "MEMORY_QUICK_FACTS.md",
            workspace_root / "CURRENT_STATE.md",
            workspace_root / "HYBRID_MEMORY_TRIAL_PLAN_2026-04-10.md",
            workspace_root / "RAG_V2_8075_CONTRACT_AND_CUTOVER_PLAN_2026-04-10.md",
            workspace_root / "projects" / "memory-evaluation-2026-04-07" / "RAG-V2_SYSTEM_SPEC.md",
        ]

    def _tokenize(self, query: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9._:-]+", query.lower())
        return [t for t in tokens if len(t) >= 3]

    def _scan_file(self, path: Path, tokens: List[str]) -> List[EvidenceMatch]:
        if not path.exists():
            return []
        out: List[EvidenceMatch] = []
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, start=1):
            low = line.lower()
            score = sum(1 for t in tokens if t in low)
            if score > 0:
                out.append(EvidenceMatch(path=str(path), line=i, text=line.strip()))
        return out

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        tokens = self._tokenize(query)
        matches: List[EvidenceMatch] = []
        for path in self.candidate_files:
            matches.extend(self._scan_file(path, tokens))

        ranked = []
        for match in matches:
            low = match.text.lower()
            lexical = sum(1 for t in tokens if t in low) / max(len(tokens), 1)
            ranked.append(
                {
                    "content": match.text,
                    "metadata": {
                        "source": Path(match.path).name,
                        "timestamp": f"L{match.line}",
                        "type": "evidence_match",
                        "topic": "rag_v2_shadow_backend",
                        "length": len(match.text),
                        "keywords": "|".join(tokens[:12]),
                    },
                    "distance": round(max(0.0, 1.0 - lexical), 6),
                    "semantic_score": round(lexical, 6),
                    "lexical_score": round(lexical, 6),
                    "recency_score": 0.5,
                    "relevance_score": round((lexical * 0.85) + 0.075, 6),
                }
            )

        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked[:top_k]

    def context(self, query: str, max_tokens: int = 600) -> str:
        results = self.search(query, top_k=3)
        if not results:
            return ""
        parts: List[str] = []
        approx_tokens = 0
        for item in results:
            text = item.get("content", "")
            source = item.get("metadata", {}).get("source", "unknown")
            block = f"[Source: {source}]\n{text}"
            tok = max(1, len(block) // 4)
            if approx_tokens + tok > max_tokens:
                break
            parts.append(block)
            approx_tokens += tok
        return "\n\n".join(parts)

    def stats(self) -> Dict[str, Any]:
        file_count = sum(1 for p in self.candidate_files if p.exists())
        return {
            "document_count": file_count,
            "persist_directory": "shadow-markdown-evidence",
            "collection_name": "rag_v2_shadow_evidence",
            "status": "shadow-ready",
        }
