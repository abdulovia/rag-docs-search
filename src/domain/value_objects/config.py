from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkConfig:
    """Конфигурация чанкинга"""
    child_chunk_size: int = 256
    parent_chunk_size: int = 1024
    chunk_overlap: int = 32
    separators: tuple = ("\n\n", "\n", ". ", " ", "")


@dataclass(frozen=True)
class RetrievalConfig:
    """Конфигурация retrieval"""
    top_k: int = 5
    similarity_threshold: float = 0.5
    vector_weight: float = 0.7
    bm25_weight: float = 0.3
    rerank_top_k: int = 5
