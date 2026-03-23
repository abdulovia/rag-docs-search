from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class DocumentMetadata:
    """Метаданные документа"""
    source: str
    page: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    doc_type: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Документ с текстом и метаданными"""
    page_content: str
    metadata: DocumentMetadata
    
    def __len__(self) -> int:
        return len(self.page_content)
    
    def __repr__(self) -> str:
        source = self.metadata.source
        page = self.metadata.page
        if page:
            return f"Document(source={source}, page={page}, len={len(self)})"
        return f"Document(source={source}, len={len(self)})"


@dataclass
class Chunk:
    """Чанк документа для индексации"""
    page_content: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    parent_id: Optional[str] = None
    
    def __len__(self) -> int:
        return len(self.page_content)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_content": self.page_content,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id,
            "parent_id": self.parent_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        return cls(
            page_content=data["page_content"],
            metadata=data.get("metadata", {}),
            chunk_id=data.get("chunk_id"),
            parent_id=data.get("parent_id"),
        )
