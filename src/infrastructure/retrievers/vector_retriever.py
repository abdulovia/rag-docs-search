"""Vector Retriever — чистый vector search"""

from typing import List, Tuple

from ...domain.entities.document import Document
from ...domain.entities.query import Query
from ...domain.ports import Embedder, VectorStore


class VectorRetriever:
    """Retriever на основе чистого vector search"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        similarity_threshold: float = 0.5,
    ):
        self._vector_store = vector_store
        self._embedder = embedder
        self._similarity_threshold = similarity_threshold

    async def retrieve(
        self,
        query: Query,
        top_k: int = 5,
    ) -> List[Tuple[Document, float]]:
        """Поиск релевантных документов через vector similarity"""
        # Создаём эмбеддинг запроса
        query_embedding = await self._embedder.embed_query(query.text)

        # Поиск в векторном хранилище
        results = await self._vector_store.search(
            query_embedding,
            top_k=top_k,
            filters=query.filters,
        )

        # Фильтрация по порогу similarity
        filtered_results = [
            (chunk, score)
            for chunk, score in results
            if score >= self._similarity_threshold
        ]

        # Преобразуем Chunk в Document
        documents = []
        for chunk, score in filtered_results:
            from ...domain.entities.document import DocumentMetadata

            metadata = DocumentMetadata(
                source=chunk.metadata.get("source", "unknown"),
                page=chunk.metadata.get("page"),
                title=chunk.metadata.get("title"),
            )

            doc = Document(
                page_content=chunk.page_content,
                metadata=metadata,
            )
            documents.append((doc, score))

        return documents
