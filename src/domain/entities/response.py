from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Message:
    """Сообщение в диалоге"""
    role: str  # "user" или "assistant"
    content: str
    timestamp: Optional[datetime] = None


@dataclass
class Citation:
    """Цитата из источника"""
    index: int
    source: str
    page: Optional[int] = None
    snippet: str = ""
    relevance_score: float = 0.0


@dataclass
class GenerationResult:
    """Результат генерации ответа"""
    answer: str
    citations: List[Citation] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    reasoning: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)
    faithfulness_score: Optional[float] = None
    relevance_score: Optional[float] = None
    is_valid: bool = True
    attempt: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_warning(self, warning: str) -> "GenerationResult":
        self.metadata["warning"] = warning
        return self


@dataclass
class QueryClassification:
    """Классификация запроса для роутинга"""
    query_type: str
    confidence: float
    domains: List[str] = field(default_factory=list)
    requires_web_search: bool = False
    sub_queries: Optional[List[str]] = None
