"""Mock Embedder для тестирования без torch"""

import hashlib
import re
from typing import List


class MockEmbedder:
    """Mock embedder для тестирования без ML зависимостей

    Создаёт векторы на основе простого keyword matching
    для демонстрации работы RAG pipeline.
    """

    def __init__(self, dimensions: int = 384):
        self._dimensions = dimensions

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Создание mock эмбеддингов для документов"""
        return [self._text_to_vector(text) for text in texts]

    async def embed_query(self, query: str) -> List[float]:
        """Создание mock эмбеддинга для запроса"""
        return self._text_to_vector(query)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _text_to_vector(self, text: str) -> List[float]:
        """Создание вектора на основе текста

        Используем комбинацию:
        1. Hash от полного текста (для уникальности)
        2. Hash от ключевых слов (для matching)
        """
        # Нормализуем текст
        text_lower = text.lower()

        # Извлекаем "ключевые" слова (длиной > 3 символов)
        words = re.findall(r'\b\w{4,}\b', text_lower)

        # Создаём вектор на основе слов
        vector = [0.0] * self._dimensions

        # Каждое слово влияет на несколько компонент вектора
        for word in words:
            # Hash слова определяет позиции
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)

            # Влияем на несколько позиций
            for i in range(5):
                pos = (word_hash + i) % self._dimensions
                # Увеличиваем значение (нормализуем потом)
                vector[pos] += 1.0

        # Нормализуем вектор
        max_val = max(vector) if max(vector) > 0 else 1.0
        vector = [v / max_val for v in vector]

        # Добавляем немного noise для уникальности
        text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        for i in range(min(10, self._dimensions)):
            pos = (text_hash + i) % self._dimensions
            vector[pos] = min(1.0, vector[pos] + 0.1)

        return vector
