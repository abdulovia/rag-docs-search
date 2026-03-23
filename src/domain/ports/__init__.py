"""Domain ports — интерфейсы для infrastructure слоя"""

from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
)

from ..entities.document import Chunk, Document
from ..entities.query import Query

T = TypeVar("T")


class DocumentParser(Protocol):
    """Извлечение текста и метаданных из документов"""

    async def parse(self, file_path: Path) -> List[Document]:
        ...

    def supports(self, file_path: Path) -> bool:
        ...


class TextPreprocessor(Protocol):
    """Очистка и нормализация текста"""

    async def preprocess(self, documents: List[Document]) -> List[Document]:
        ...


class Chunker(Protocol):
    """Разбиение документов на чанки"""

    async def chunk(
        self,
        documents: List[Document],
        config: Any,
    ) -> Tuple[List[Chunk], Dict[str, Chunk]]:
        """Returns: (child_chunks, parent_map)"""
        ...


class Embedder(Protocol):
    """Создание векторных представлений текста"""

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...

    async def embed_query(self, query: str) -> List[float]:
        ...

    @property
    def dimensions(self) -> int:
        ...


class VectorStore(Protocol):
    """Хранение и поиск векторов"""

    async def add(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> None:
        ...

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        ...

    async def delete(self, filter: Dict[str, Any]) -> int:
        ...

    async def persist(self) -> None:
        ...

    async def load(self) -> None:
        ...


class Retriever(Protocol):
    """Извлечение релевантных документов"""

    async def retrieve(
        self,
        query: Query,
        top_k: int = 5,
    ) -> List[Tuple[Document, float]]:
        ...


class Reranker(Protocol):
    """Повторное ранжирование результатов retrieval"""

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
    ) -> List[Tuple[Document, float]]:
        ...


class LLMClient(Protocol):
    """Клиент для взаимодействия с LLM"""

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        ...

    async def generate_stream(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        ...

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        **kwargs: Any,
    ) -> T:
        ...


class WebSearch(Protocol):
    """Веб-поиск"""

    async def search(self, query: str, max_results: int = 5) -> List[Document]:
        ...


class Evaluator(Protocol):
    """Оценка качества ответов"""

    async def check_faithfulness(self, context: str, answer: str) -> float:
        ...

    async def check_relevance(self, question: str, answer: str) -> float:
        ...

    async def grade_documents(
        self, query: str, documents: List[Document]
    ) -> List[float]:
        ...
