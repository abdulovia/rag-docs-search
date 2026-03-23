"""FastAPI Dependencies — DI через Depends"""

from ...application.services.prompt_registry import PromptRegistry
from ...application.use_cases.answer_question import AnswerQuestionUseCase
from ...application.use_cases.index_documents import IndexDocumentsUseCase
from ...domain.value_objects import ChunkConfig
from ...infrastructure.chunkers.parent_child_chunker import ParentChildChunker
from ...infrastructure.config.settings import Settings, get_settings
from ...infrastructure.evaluation.rag_evaluator import RAGEvaluator
from ...infrastructure.llm.ollama_client import OllamaClient
from ...infrastructure.parsers.composite_parser import CompositeParser
from ...infrastructure.retrievers.vector_retriever import VectorRetriever
from ...infrastructure.vector_stores.faiss_store import FAISSVectorStore

# Module-level singleton instances
_embedder = None
_vector_store = None
_llm_client = None
_prompt_registry = None
_retriever = None
_reranker = None
_evaluator = None
_web_search = None


def _check_sentence_transformers():
    """Проверить доступность sentence_transformers"""
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False


def get_embedder(settings: Settings = None):
    global _embedder
    if _embedder is None:
        if settings is None:
            settings = get_settings()

        if _check_sentence_transformers():
            from ...infrastructure.embeddings.huggingface_embedder import (
                HuggingFaceEmbedder,
            )

            _embedder = HuggingFaceEmbedder(
                model_name=settings.embedding.model_name,
                device=settings.embedding.device,
                batch_size=settings.embedding.batch_size,
            )
        else:
            from ...infrastructure.embeddings.mock_embedder import MockEmbedder

            _embedder = MockEmbedder(dimensions=settings.embedding.dimensions)

    return _embedder


def get_vector_store(settings: Settings = None):
    global _vector_store
    if _vector_store is None:
        if settings is None:
            settings = get_settings()

        _vector_store = FAISSVectorStore(
            path=settings.vector_store.db_path,
            embeddings=get_embedder(settings),
            dimension=settings.embedding.dimensions,
        )

    return _vector_store


def get_llm_client(settings: Settings = None):
    global _llm_client
    if _llm_client is None:
        if settings is None:
            settings = get_settings()

        _llm_client = OllamaClient(
            model=settings.llm.model_name,
            base_url=settings.llm.ollama_url,
            timeout=settings.llm.timeout_seconds,
        )

    return _llm_client


def get_prompt_registry(settings: Settings = None):
    global _prompt_registry
    if _prompt_registry is None:
        if settings is None:
            settings = get_settings()

        _prompt_registry = PromptRegistry(templates_dir=settings.prompts_dir)

    return _prompt_registry


def get_retriever(settings: Settings = None):
    global _retriever
    if _retriever is None:
        if settings is None:
            settings = get_settings()

        _retriever = VectorRetriever(
            vector_store=get_vector_store(settings),
            embedder=get_embedder(settings),
            similarity_threshold=settings.retrieval.similarity_threshold,
        )

    return _retriever


def get_reranker(settings: Settings = None):
    global _reranker
    if _reranker is None:
        if settings is None:
            settings = get_settings()

        if _check_sentence_transformers() and settings.retrieval.enable_reranking:
            from ...infrastructure.rerankers.cross_encoder_reranker import (
                CrossEncoderReranker,
            )

            _reranker = CrossEncoderReranker(
                model_name=settings.retrieval.reranker_model,
                device=settings.embedding.device,
            )
        else:
            _reranker = None

    return _reranker


def get_evaluator(settings: Settings = None):
    global _evaluator
    if _evaluator is None:
        if settings is None:
            settings = get_settings()

        if settings.enable_self_correction:
            _evaluator = RAGEvaluator(
                llm=get_llm_client(settings),
                prompt_registry=get_prompt_registry(settings),
            )
        else:
            _evaluator = None

    return _evaluator


def get_web_search(settings: Settings = None):
    global _web_search
    if _web_search is None:
        if settings is None:
            settings = get_settings()

        if settings.enable_web_search:
            from ...infrastructure.web_search.duckduckgo_search import (
                DuckDuckGoSearch,
            )

            _web_search = DuckDuckGoSearch()
        else:
            _web_search = None

    return _web_search


def get_answer_use_case() -> AnswerQuestionUseCase:
    settings = get_settings()
    return AnswerQuestionUseCase(
        retriever=get_retriever(settings),
        reranker=get_reranker(settings),
        llm=get_llm_client(settings),
        prompt_registry=get_prompt_registry(settings),
        evaluator=get_evaluator(settings),
        web_search=get_web_search(settings),
        enable_self_correction=settings.enable_self_correction,
        enable_reranking=settings.retrieval.enable_reranking,
        min_score=settings.retrieval.min_score,
    )


def get_index_use_case() -> IndexDocumentsUseCase:
    settings = get_settings()
    return IndexDocumentsUseCase(
        parser=CompositeParser(),
        chunker=ParentChildChunker(),
        embedder=get_embedder(settings),
        vector_store=get_vector_store(settings),
        chunk_config=ChunkConfig(
            child_chunk_size=settings.retrieval.child_chunk_size,
            parent_chunk_size=settings.retrieval.parent_chunk_size,
            chunk_overlap=settings.retrieval.chunk_overlap,
        ),
    )
