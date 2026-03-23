"""Конфигурация приложения через Pydantic Settings"""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Конфигурация LLM"""
    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: Literal["ollama"] = "ollama"
    model_name: str = "llama3.2:3b-instruct-fp16"
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=128000)
    ollama_url: str = "http://localhost:11434"
    timeout_seconds: int = Field(120, ge=1, le=300)


class EmbeddingSettings(BaseSettings):
    """Конфигурация embedding модели"""
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    model_name: str = "intfloat/multilingual-e5-large"
    device: Literal["cpu", "cuda"] = "cpu"
    dimensions: int = 1024
    batch_size: int = Field(32, ge=1, le=256)


class RetrievalSettings(BaseSettings):
    """Конфигурация retrieval"""
    model_config = SettingsConfigDict(
        env_prefix="RETRIEVAL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Chunking
    child_chunk_size: int = Field(256, ge=64, le=2048)
    parent_chunk_size: int = Field(1024, ge=256, le=8192)
    chunk_overlap: int = Field(32, ge=0, le=512)

    # Search
    top_k: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0)
    min_score: float = Field(0.0, ge=0.0, le=1.0)

    # Hybrid search
    enable_hybrid_search: bool = False
    vector_weight: float = Field(0.7, ge=0.0, le=1.0)
    bm25_weight: float = Field(0.3, ge=0.0, le=1.0)

    # Reranking
    enable_reranking: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_k: int = Field(5, ge=1, le=20)


class VectorStoreSettings(BaseSettings):
    """Конфигурация векторного хранилища"""
    model_config = SettingsConfigDict(env_prefix="VECTOR_")

    provider: Literal["faiss", "qdrant"] = "faiss"
    db_path: Path = Path("db/db_01")
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    collection_name: str = "documents"


class MonitoringSettings(BaseSettings):
    """Конфигурация мониторинга"""
    model_config = SettingsConfigDict(env_prefix="MONITORING_")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "text"


class Settings(BaseSettings):
    """Основные настройки приложения"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Ports
    api_port: int = 8000
    ui_port: int = 8501
    ollama_port: int = 11434

    # Sub-configurations
    llm: LLMSettings = LLMSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    vector_store: VectorStoreSettings = VectorStoreSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    # Paths (относительно корня проекта)
    project_root: Path = Path(".")
    prompts_dir: Path = Path("src/infrastructure/prompts/templates")
    pdf_dir: Path = Path("data/documents")
    log_dir: Path = Path("logs")

    # Feature flags
    enable_web_search: bool = True
    enable_self_correction: bool = True

    @field_validator("pdf_dir", "log_dir")
    @classmethod
    def create_dirs(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()
