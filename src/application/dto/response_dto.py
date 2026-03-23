from typing import List, Optional

from pydantic import BaseModel, Field


class CitationDTO(BaseModel):
    """Цитата из источника"""
    index: int
    source: str
    page: Optional[int] = None
    snippet: str = ""
    relevance_score: float = 0.0


class AnswerResponse(BaseModel):
    """Ответ на вопрос"""
    answer: str
    citations: List[CitationDTO] = Field(default_factory=list)
    confidence: str = "medium"
    reasoning: Optional[str] = None
    follow_up_questions: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[float] = None
    metadata: Optional[dict] = None


class IndexResponse(BaseModel):
    """Результат индексации"""
    status: str
    chunks_count: int = 0
    document_id: Optional[str] = None


class DocumentInfo(BaseModel):
    """Информация о документе"""
    document_id: str
    source: str
    chunks_count: int
    indexed_at: Optional[str] = None
