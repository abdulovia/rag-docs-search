"""Parent-Child чанкинг стратегия"""

import uuid
from typing import Dict, List, Tuple

from ...domain.entities.document import Chunk, Document
from ...domain.value_objects import ChunkConfig


def _split_text(text: str, chunk_size: int, chunk_overlap: int, separators: Tuple[str, ...]) -> List[str]:
    """Простой text splitter без внешних зависимостей"""
    if not text or not text.strip():
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Ищем ближайший разделитель
        best_split = end
        for sep in separators:
            if not sep:
                continue
            last_sep = text.rfind(sep, start, end)
            if last_sep > start:
                best_split = last_sep + len(sep)
                break

        chunks.append(text[start:best_split])
        start = best_split - chunk_overlap if best_split - chunk_overlap > start else best_split

    return [c.strip() for c in chunks if c.strip()]


class ParentChildChunker:
    """Parent-Child чанкинг: малые child chunks для retrieval, большие parent для контекста"""

    def __init__(self):
        pass

    async def chunk(
        self,
        documents: List[Document],
        config: ChunkConfig,
    ) -> Tuple[List[Chunk], Dict[str, Chunk]]:
        """Создание parent-child chunks

        Returns:
            Tuple из (child_chunks, parent_map)
            - child_chunks: для embedding и поиска
            - parent_map: child_id -> parent_chunk для контекста
        """
        parent_map: Dict[str, Chunk] = {}
        child_chunks: List[Chunk] = []

        for doc in documents:
            # Создаём parent chunks
            parent_texts = _split_text(
                doc.page_content,
                config.parent_chunk_size,
                config.chunk_overlap,
                config.separators,
            )

            for parent_text in parent_texts:
                parent_id = str(uuid.uuid4())

                # Метаданные parent chunk
                parent_metadata = {
                    "source": doc.metadata.source,
                    "page": doc.metadata.page,
                    "title": doc.metadata.title,
                    "parent_id": parent_id,
                    "chunk_type": "parent",
                    **doc.metadata.extra,
                }

                parent_chunk = Chunk(
                    page_content=parent_text,
                    metadata=parent_metadata,
                    chunk_id=parent_id,
                    parent_id=None,
                )

                parent_map[parent_id] = parent_chunk

                # Создаём child chunks из parent
                child_texts = _split_text(
                    parent_text,
                    config.child_chunk_size,
                    config.chunk_overlap,
                    config.separators,
                )

                for child_text in child_texts:
                    child_id = str(uuid.uuid4())
                    child_metadata = {
                        **parent_metadata,
                        "chunk_type": "child",
                        "parent_id": parent_id,
                    }

                    child_chunks.append(
                        Chunk(
                            page_content=child_text,
                            metadata=child_metadata,
                            chunk_id=child_id,
                            parent_id=parent_id,
                        )
                    )

        return child_chunks, parent_map
