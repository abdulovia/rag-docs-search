"""Unit тесты для chunker"""

import pytest

from src.domain.entities.document import Document, DocumentMetadata
from src.domain.value_objects import ChunkConfig
from src.infrastructure.chunkers.parent_child_chunker import ParentChildChunker


@pytest.fixture
def chunker():
    return ParentChildChunker()


@pytest.fixture
def config():
    return ChunkConfig(
        child_chunk_size=50,
        parent_chunk_size=150,
        chunk_overlap=10,
    )


@pytest.fixture
def test_documents():
    return [
        Document(
            page_content="This is a test document with some content. " * 10,
            metadata=DocumentMetadata(source="test.pdf", page=1),
        ),
    ]


@pytest.mark.asyncio
async def test_chunking_creates_child_chunks(chunker, config, test_documents):
    child_chunks, parent_map = await chunker.chunk(test_documents, config)
    assert len(child_chunks) > 0


@pytest.mark.asyncio
async def test_chunking_creates_parent_map(chunker, config, test_documents):
    child_chunks, parent_map = await chunker.chunk(test_documents, config)
    assert len(parent_map) > 0


@pytest.mark.asyncio
async def test_child_chunks_have_parent_id(chunker, config, test_documents):
    child_chunks, parent_map = await chunker.chunk(test_documents, config)
    for chunk in child_chunks:
        assert chunk.parent_id is not None
        assert chunk.parent_id in parent_map


@pytest.mark.asyncio
async def test_empty_document(chunker, config):
    docs = [Document(page_content="", metadata=DocumentMetadata(source="test.pdf"))]
    child_chunks, parent_map = await chunker.chunk(docs, config)
    assert len(child_chunks) == 0
    assert len(parent_map) == 0
