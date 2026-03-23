from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class QueryType(str, Enum):
    """Тип запроса для маршрутизации"""
    SIMPLE_FACTUAL = "simple_factual"
    COMPLEX_MULTI_HOP = "complex_multi_hop"
    COMPARISON = "comparison"
    CURRENT_EVENTS = "current_events"
    GREETING = "greeting"


@dataclass
class Query:
    """Запрос пользователя"""
    text: str
    original: Optional[str] = None
    query_type: Optional[QueryType] = None
    filters: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.original is None:
            self.original = self.text


@dataclass
class SubQuery:
    """Подзапрос для multi-hop вопросов"""
    text: str
    parent_query_id: str
    index: int
    
    def to_query(self) -> Query:
        return Query(text=self.text, original=self.text)
