"""Domain exceptions"""


class DomainError(Exception):
    """Базовое исключение домена"""
    pass


class DocumentParseError(DomainError):
    """Ошибка парсинга документа"""
    pass


class EmbeddingError(DomainError):
    """Ошибка создания эмбеддинга"""
    pass


class VectorStoreError(DomainError):
    """Ошибка векторного хранилища"""
    pass


class RetrievalError(DomainError):
    """Ошибка retrieval"""
    pass


class GenerationError(DomainError):
    """Ошибка генерации"""
    pass


class ConfigurationError(DomainError):
    """Ошибка конфигурации"""
    pass
