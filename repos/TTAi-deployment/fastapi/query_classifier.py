"""
Query Classifier Module for TTAi Super Model Hybrid
Classifies queries into Simple/Medium/Complex categories
"""

import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from load_balancer import QueryComplexity

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of query classification"""
    complexity: QueryComplexity
    confidence: float
    language: str
    needs_context: bool
    estimated_tokens: int
    features: Dict[str, float]
    needs_realtime: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "complexity": self.complexity.value,
            "confidence": self.confidence,
            "language": self.language,
            "needs_context": self.needs_context,
            "estimated_tokens": self.estimated_tokens,
            "features": self.features,
            "needs_realtime": self.needs_realtime,
        }


_REALTIME_VI = [
    "hôm nay", "hôm qua", "ngày mai", "tuần này", "tháng này", "năm nay",
    "mới nhất", "gần đây", "hiện tại", "vừa mới", "đang xảy ra",
    "tin tức", "thời sự", "cập nhật", "mới ra", "vừa có",
    "giá hiện tại", "giá hôm nay", "kết quả hôm nay", "sự kiện",
    # weather
    "thời tiết", "dự báo thời tiết", "nhiệt độ", "mưa", "nắng", "bão", "lũ",
    # commodity & financial prices — always realtime by nature
    "giá xăng", "giá dầu", "giá điện", "giá vàng", "giá bạc",
    "giá đô", "tỷ giá", "giá usd", "giá btc", "giá bitcoin",
    "chứng khoán", "vnindex", "thị trường chứng khoán",
    "lãi suất", "lạm phát", "cpi", "gdp",
    "giá thịt", "giá gạo", "giá gas",
]
_REALTIME_EN = [
    "today", "yesterday", "this week", "this month", "this year",
    "latest", "recent", "currently", "right now", "breaking",
    "news", "just released", "just announced", "new update",
    "what happened", "who won", "current price", "score today",
]
_YEAR_RE = re.compile(r"\b202[4-9]\b|\b203\d\b")


class QueryClassifier:
    """Intelligent Query Classifier for TTAi Hybrid System"""

    def __init__(self):
        # Vietnamese complex keywords
        self.vietnamese_complex_keywords = [
            "giải thích", "phân tích", "so sánh", "tại sao", "làm thế nào",
            "nguyên nhân", "kết quả", "ảnh hưởng", "tác động", "quan hệ",
            "quá trình", "cơ chế", "phương pháp", "chiến lược", "giải pháp",
            "tóm tắt", "đánh giá", "tối ưu", "khi nào", "ưu nhược điểm",
            "lợi ích", "hạn chế", "khác nhau", "nên dùng", "trường hợp"
        ]
        
        # English complex keywords
        self.english_complex_keywords = [
            "explain", "analyze", "compare", "why", "how",
            "cause", "effect", "impact", "relationship", "process",
            "mechanism", "method", "strategy", "solution", "evaluate",
            "summarize", "summary", "optimize", "when should", "pros and cons",
            "benefits", "tradeoff", "use case"
        ]
        
        # Code/technical keywords
        self.code_keywords = [
            "code", "lập trình", "programming", "function", "hàm",
            "api", "endpoint", "database", "cơ sở dữ liệu", "algorithm",
            "thuật toán", "python", "javascript", "java", "c++", "react",
            "vue", "docker", "kubernetes", "deploy", "triển khai"
        ]
        
        # Simple query patterns (greetings, basic questions)
        self.simple_patterns = [
            r"^(xin chào|hello|hi|chào)",
            r"^(bạn khoẻ không|how are you)",
            r"^(cảm ơn|thank you)",
            r"^(tạm biệt|goodbye)",
            r"^(\?|\.|\!){0,3}$",  # Very short queries
        ]
        
        # Language detection patterns
        self.vietnamese_patterns = [
            r"[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]",
            r"\b(của|và|là|có|được|trong|cho|với|từ|này|đó|kia)\b",
        ]
        
        logger.info("Query classifier initialized")
    
    def detect_language(self, query: str) -> str:
        """Detect language of query (vi/en)"""
        query_lower = query.lower()
        
        # Check for Vietnamese characters
        vietnamese_chars = re.compile(
            r"[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]"
        )
        
        if vietnamese_chars.search(query_lower):
            return "vi"
        
        # Check for common Vietnamese words
        vietnamese_words = re.compile(
            r"\b(của|và|là|có|được|trong|cho|với|từ|này|đó|kia|nào|ấy)\b"
        )
        
        if vietnamese_words.search(query_lower):
            return "vi"
        
        # Default to English
        return "en"
    
    def calculate_length_score(self, query: str) -> float:
        """Calculate score based on query length"""
        words = query.split()
        word_count = len(words)
        
        # Normalize score (0-1)
        if word_count <= 3:
            return 0.1  # Very short
        elif word_count <= 6:
            return 0.3  # Short
        elif word_count <= 10:
            return 0.5  # Medium
        elif word_count <= 15:
            return 0.7  # Long
        else:
            return 0.9  # Very long
    
    def calculate_complexity_score(self, query: str, language: str) -> float:
        """Calculate score based on complex keywords"""
        query_lower = query.lower()
        score = 0.0
        
        # Select appropriate keyword list
        if language == "vi":
            keywords = self.vietnamese_complex_keywords
        else:
            keywords = self.english_complex_keywords
        
        # Check for complex keywords
        for keyword in keywords:
            if keyword in query_lower:
                score += 0.25  # Each complex keyword adds 0.25
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def calculate_code_score(self, query: str) -> float:
        """Calculate score based on code/technical keywords"""
        query_lower = query.lower()
        score = 0.0
        
        for keyword in self.code_keywords:
            if keyword in query_lower:
                score += 0.15  # Each code keyword adds 0.15
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def check_simple_pattern(self, query: str) -> bool:
        """Check if query matches simple patterns"""
        query_lower = query.lower().strip()
        
        for pattern in self.simple_patterns:
            if re.match(pattern, query_lower, re.IGNORECASE):
                return True
        
        return False
    
    def estimate_tokens(self, query: str) -> int:
        """Estimate token count for the query"""
        # Rough estimation: 1 token ≈ 4 characters for English
        # For Vietnamese: 1 token ≈ 3 characters
        language = self.detect_language(query)
        
        if language == "vi":
            return len(query) // 3
        else:
            return len(query) // 4
    
    def needs_context(self, query: str, complexity_score: float) -> bool:
        """Determine if query needs context/memory retrieval"""
        query_lower = query.lower()
        
        # Always need context for certain patterns
        if any(pattern in query_lower for pattern in ["trước đây", "trước kia", "hôm qua", "tuần trước"]):
            return True
        
        # Need context for complex queries
        if complexity_score > 0.5:
            return True
        
        # Check for personal/contextual references
        personal_patterns = [
            r"\b(tôi|mình|tao|tớ)\b",
            r"\b(bạn|anh|chị|em|ông|bà)\b",
            r"\b(của tôi|cho tôi|với tôi)\b"
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _is_realtime(self, query: str) -> bool:
        q = query.lower()
        if any(kw in q for kw in _REALTIME_VI):
            return True
        if any(kw in q for kw in _REALTIME_EN):
            return True
        if _YEAR_RE.search(query):
            return True
        return False

    def classify(self, query: str) -> ClassificationResult:
        """
        Classify query into Simple/Medium/Complex
        
        Scoring weights:
        - Length: 30%
        - Complexity keywords: 40%
        - Code keywords: 30%
        """
        
        # Step 1: Check for simple patterns (fast path)
        if self.check_simple_pattern(query):
            return ClassificationResult(
                complexity=QueryComplexity.SIMPLE,
                confidence=0.95,
                language=self.detect_language(query),
                needs_context=False,
                estimated_tokens=self.estimate_tokens(query),
                needs_realtime=self._is_realtime(query),
                features={
                    "length_score": 0.1,
                    "complexity_score": 0.0,
                    "code_score": 0.0,
                    "total_score": 0.1,
                    "simple_pattern": True
                }
            )
        
        # Step 2: Detect language
        language = self.detect_language(query)
        
        # Step 3: Calculate feature scores
        length_score = self.calculate_length_score(query)
        complexity_score = self.calculate_complexity_score(query, language)
        code_score = self.calculate_code_score(query)
        
        # Step 4: Calculate weighted total score
        total_score = (
            length_score * 0.3 +
            complexity_score * 0.4 +
            code_score * 0.3
        )
        
        # Step 5: Determine complexity level
        query_lower = query.lower()
        if language == "vi" and any(phrase in query_lower for phrase in ["phân tích", "giải thích", "so sánh", "tóm tắt", "đánh giá", "khi nào", "nên dùng", "lợi ích"]):
            total_score = max(total_score, 0.35)
        if language == "en" and any(phrase in query_lower for phrase in ["analyze", "explain", "compare", "summarize", "evaluate", "when should", "benefits"]):
            total_score = max(total_score, 0.35)

        if total_score < 0.2:
            complexity = QueryComplexity.SIMPLE
            confidence = 0.92 - (total_score * 2)
        elif total_score < 0.5:
            complexity = QueryComplexity.MEDIUM
            confidence = 0.72
        else:
            complexity = QueryComplexity.COMPLEX
            confidence = 0.82 + (total_score - 0.5) * 0.4
        
        # Step 6: Check if context is needed
        needs_context = self.needs_context(query, complexity_score)
        
        # Step 7: Create result
        result = ClassificationResult(
            complexity=complexity,
            confidence=min(confidence, 1.0),
            language=language,
            needs_context=needs_context,
            estimated_tokens=self.estimate_tokens(query),
            needs_realtime=self._is_realtime(query),
            features={
                "length_score": length_score,
                "complexity_score": complexity_score,
                "code_score": code_score,
                "total_score": total_score,
                "word_count": len(query.split()),
                "char_count": len(query)
            }
        )
        
        logger.info(
            f"Query classified: '{query[:50]}...' -> {complexity.value} "
            f"(score: {total_score:.2f}, confidence: {confidence:.2f})"
        )
        
        return result
    
    def batch_classify(self, queries: List[str]) -> List[ClassificationResult]:
        """Classify multiple queries at once"""
        return [self.classify(query) for query in queries]
    
    def get_classification_stats(self, queries: List[str]) -> Dict:
        """Get statistics for a batch of queries"""
        results = self.batch_classify(queries)
        
        stats = {
            "total_queries": len(queries),
            "complexity_distribution": {
                "simple": 0,
                "medium": 0,
                "complex": 0
            },
            "language_distribution": {
                "vi": 0,
                "en": 0
            },
            "average_confidence": 0.0,
            "needs_context_percentage": 0.0
        }
        
        total_confidence = 0.0
        needs_context_count = 0
        
        for result in results:
            stats["complexity_distribution"][result.complexity.value] += 1
            stats["language_distribution"][result.language] += 1
            total_confidence += result.confidence
            
            if result.needs_context:
                needs_context_count += 1
        
        if results:
            stats["average_confidence"] = total_confidence / len(results)
            stats["needs_context_percentage"] = (needs_context_count / len(results)) * 100
        
        return stats


# Singleton instance
query_classifier = QueryClassifier()


# Test function
def test_classifier():
    """Test the classifier with sample queries"""
    test_queries = [
        "Xin chào",
        "Thời tiết hôm nay thế nào?",
        "Giải thích về machine learning",
        "Viết function Python để xử lý JSON và kết nối database MySQL",
        "How are you today?",
        "Explain the theory of relativity",
        "Create a React component with TypeScript and Tailwind CSS",
        "So sánh Python và JavaScript",
        "Cách tạo API RESTful với FastAPI",
        "Phân tích ảnh hưởng của AI đến ngành công nghiệp"
    ]
    
    classifier = QueryClassifier()
    
    print("Query Classification Test Results:")
    print("=" * 80)
    
    for query in test_queries:
        result = classifier.classify(query)
        print(f"Query: {query[:50]}...")
        print(f"  Language: {result.language}")
        print(f"  Complexity: {result.complexity.value} (confidence: {result.confidence:.2f})")
        print(f"  Needs Context: {result.needs_context}")
        print(f"  Estimated Tokens: {result.estimated_tokens}")
        print(f"  Features: {result.features}")
        print("-" * 80)


if __name__ == "__main__":
    test_classifier()