from typing import Optional

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Запрос на получение ответа"""
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(5, ge=1, le=20)
    conversation_id: Optional[str] = None
    enable_citations: bool = True
    enable_web_search: bool = False


class IndexRequest(BaseModel):
    """Запрос на индексацию документа"""
    file_path: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None
