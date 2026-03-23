"""Use case для индексации документов"""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...domain.ports import Chunker, DocumentParser, Embedder, VectorStore
from ...domain.value_objects import ChunkConfig


class IndexDocumentsUseCase:
    """Индексация документов в векторное хранилище"""

    def __init__(
        self,
        parser: DocumentParser,
        chunker: Chunker,
        embedder: Embedder,
        vector_store: VectorStore,
        chunk_config: Optional[ChunkConfig] = None,
    ):
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store
        self._chunk_config = chunk_config or ChunkConfig()

    async def execute(self, file_path: Path) -> Dict[str, Any]:
        """Индексировать документ"""
        # Phase 1: Parse
        if not self._parser.supports(file_path):
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        documents = await self._parser.parse(file_path)

        if not documents:
            return {"status": "empty", "chunks_count": 0}

        # Phase 2: Chunk
        child_chunks, parent_map = await self._chunker.chunk(
            documents, self._chunk_config
        )

        # Phase 3: Create embeddings
        texts = [chunk.page_content for chunk in child_chunks]
        embeddings = await self._embedder.embed_documents(texts)

        # Phase 4: Store
        await self._vector_store.add(child_chunks, embeddings)
        await self._vector_store.persist()

        return {
            "status": "indexed",
            "chunks_count": len(child_chunks),
            "document_id": str(uuid.uuid4()),
            "source": file_path.name,
        }

    async def index_from_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Индексировать все документы из директории"""
        results = []
        supported_extensions = {".pdf", ".md", ".markdown"}

        for file_path in directory.iterdir():
            if file_path.suffix.lower() in supported_extensions:
                try:
                    result = await self.execute(file_path)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "status": "error",
                        "source": file_path.name,
                        "error": str(e),
                    })

        return results
