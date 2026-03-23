"""Unit тесты для domain entities"""

from src.domain.entities.document import Chunk, Document, DocumentMetadata
from src.domain.entities.query import Query, QueryType
from src.domain.entities.response import Citation, ConfidenceLevel, GenerationResult


class TestDocument:
    def test_document_creation(self):
        doc = Document(
            page_content="Test content",
            metadata=DocumentMetadata(source="test.pdf", page=1),
        )
        assert doc.page_content == "Test content"
        assert doc.metadata.source == "test.pdf"
        assert doc.metadata.page == 1

    def test_document_length(self):
        doc = Document(
            page_content="Test content",
            metadata=DocumentMetadata(source="test.pdf"),
        )
        assert len(doc) == 12

    def test_document_repr(self):
        doc = Document(
            page_content="Test",
            metadata=DocumentMetadata(source="test.pdf", page=5),
        )
        assert "test.pdf" in repr(doc)
        assert "page=5" in repr(doc)


class TestChunk:
    def test_chunk_creation(self):
        chunk = Chunk(
            page_content="Chunk content",
            metadata={"source": "test.pdf"},
            chunk_id="chunk-1",
            parent_id="parent-1",
        )
        assert chunk.page_content == "Chunk content"
        assert chunk.chunk_id == "chunk-1"
        assert chunk.parent_id == "parent-1"

    def test_chunk_to_dict(self):
        chunk = Chunk(
            page_content="Content",
            metadata={"source": "test.pdf"},
            chunk_id="id-1",
        )
        data = chunk.to_dict()
        assert data["page_content"] == "Content"
        assert data["chunk_id"] == "id-1"

    def test_chunk_from_dict(self):
        data = {
            "page_content": "Content",
            "metadata": {"source": "test.pdf"},
            "chunk_id": "id-1",
        }
        chunk = Chunk.from_dict(data)
        assert chunk.page_content == "Content"
        assert chunk.chunk_id == "id-1"


class TestQuery:
    def test_query_creation(self):
        query = Query(text="Test query")
        assert query.text == "Test query"
        assert query.original == "Test query"

    def test_query_with_type(self):
        query = Query(text="Test", query_type=QueryType.SIMPLE_FACTUAL)
        assert query.query_type == QueryType.SIMPLE_FACTUAL


class TestGenerationResult:
    def test_result_creation(self):
        result = GenerationResult(
            answer="Test answer",
            confidence=ConfidenceLevel.HIGH,
        )
        assert result.answer == "Test answer"
        assert result.confidence == ConfidenceLevel.HIGH
        assert result.is_valid is True

    def test_result_with_citations(self):
        result = GenerationResult(
            answer="Answer",
            citations=[
                Citation(index=1, source="test.pdf", page=1, snippet="Test"),
            ],
        )
        assert len(result.citations) == 1
        assert result.citations[0].source == "test.pdf"

    def test_result_with_warning(self):
        result = GenerationResult(answer="Answer")
        result = result.with_warning("Test warning")
        assert result.metadata["warning"] == "Test warning"
