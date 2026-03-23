"""FAISS Vector Store реализация"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

from ...domain.entities.document import Chunk


class FAISSVectorStore:
    """FAISS векторное хранилище с персистентностью"""

    def __init__(
        self,
        path: Path,
        embeddings: Any,  # Embedder для создания эмбеддингов при поиске
        dimension: int = 1024,
    ):
        self._path = Path(path)
        self._embeddings = embeddings
        self._dimension = dimension
        self._index = None
        self._chunks: List[Chunk] = []
        self._chunk_map: Dict[str, Chunk] = {}

    async def _ensure_index(self):
        """Ленивая инициализация индекса"""
        if self._index is None:
            self._index = faiss.IndexFlatIP(self._dimension)  # Inner Product (cosine)
            await self.load()

    async def add(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> None:
        """Добавление чанков с эмбеддингами"""
        await self._ensure_index()

        if not chunks:
            return

        # Нормализуем эмбеддинги для cosine similarity
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)

        # Добавляем в индекс
        self._index.add(embeddings_array)

        # Сохраняем чанки
        for chunk in chunks:
            self._chunks.append(chunk)
            if chunk.chunk_id:
                self._chunk_map[chunk.chunk_id] = chunk

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """Поиск ближайших векторов"""
        await self._ensure_index()

        if self._index.ntotal == 0:
            return []

        # Нормализуем query embedding
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)

        # Поиск
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_array, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue

            chunk = self._chunks[idx]

            # Фильтрация по метаданным
            if filters:
                if not self._match_filters(chunk.metadata, filters):
                    continue

            results.append((chunk, float(score)))

        return results

    async def delete(self, filter: Dict[str, Any]) -> int:
        """Удаление чанков по фильтру (перестройка индекса)"""
        await self._ensure_index()

        original_count = len(self._chunks)
        self._chunks = [
            chunk for chunk in self._chunks
            if not self._match_filters(chunk.metadata, filter)
        ]

        # Перестраиваем индекс
        if len(self._chunks) != original_count:
            await self._rebuild_index()

        return original_count - len(self._chunks)

    async def persist(self) -> None:
        """Сохранение индекса на диск"""
        if self._index is None:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем FAISS индекс
        faiss.write_index(self._index, str(self._path.with_suffix(".faiss")))

        # Сохраняем чанки
        with open(self._path.with_suffix(".pkl"), "wb") as f:
            pickle.dump({
                "chunks": self._chunks,
                "chunk_map": self._chunk_map,
            }, f)

    async def load(self) -> None:
        """Загрузка индекса с диска"""
        faiss_path = self._path.with_suffix(".faiss")
        pkl_path = self._path.with_suffix(".pkl")

        if faiss_path.exists() and pkl_path.exists():
            self._index = faiss.read_index(str(faiss_path))

            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
                self._chunks = data["chunks"]
                self._chunk_map = data["chunk_map"]

    async def _rebuild_index(self):
        """Перестройка индекса из существующих чанков"""
        if not self._chunks:
            self._index = faiss.IndexFlatIP(self._dimension)
            return

        # Создаём эмбеддинги для существующих чанков
        texts = [chunk.page_content for chunk in self._chunks]
        embeddings = await self._embeddings.embed_documents(texts)

        # Пересоздаём индекс
        self._index = faiss.IndexFlatIP(self._dimension)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)
        self._index.add(embeddings_array)

    def _match_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Проверка метаданных на соответствие фильтрам"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
