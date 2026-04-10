from typing import Any, Dict, List


class CompatibilityAdapter:
    """Map retrieval backends into the stable 8075 public contract."""

    def map_search_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = []
        for item in results or []:
            metadata = item.get("metadata") or {}
            normalized.append(
                {
                    "content": item.get("content", ""),
                    "metadata": {
                        "source": metadata.get("source", "unknown"),
                        "timestamp": metadata.get("timestamp", ""),
                        "type": metadata.get("type", "memory"),
                        "topic": metadata.get("topic", ""),
                        "length": metadata.get("length", 0),
                        "keywords": metadata.get("keywords", ""),
                    },
                    "distance": item.get("distance", 0.0),
                    "semantic_score": item.get("semantic_score", 0.0),
                    "lexical_score": item.get("lexical_score", 0.0),
                    "recency_score": item.get("recency_score", 0.0),
                    "relevance_score": item.get("relevance_score", 0.0),
                }
            )
        return {"results": normalized}

    def map_context_result(self, context_text: str) -> Dict[str, str]:
        return {"context": context_text or ""}

    def map_health(self, stats: Dict[str, Any], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = {
            "status": "ok" if stats.get("document_count") else "empty",
            "stats": stats,
        }
        if extra:
            payload["compatibility"] = extra
        return payload
