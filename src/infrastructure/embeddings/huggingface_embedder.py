"""HuggingFace Embeddings через sentence-transformers"""

from typing import List


class HuggingFaceEmbedder:
    """Embeddings через HuggingFace sentence-transformers"""

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        device: str = "cpu",
        batch_size: int = 32,
    ):
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model = None

    @property
    def _get_model(self):
        """Lazy loading модели"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )
        return self._model

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для списка документов"""
        # Добавляем prefix для E5 моделей
        prefixed_texts = [f"passage: {text}" for text in texts]

        embeddings = self._get_model.encode(
            prefixed_texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    async def embed_query(self, query: str) -> List[float]:
        """Создание эмбеддинга для запроса"""
        # Добавляем prefix для E5 моделей
        prefixed_query = f"query: {query}"

        embedding = self._get_model.encode(
            prefixed_query,
            convert_to_numpy=True,
        )

        return embedding.tolist()

    @property
    def dimensions(self) -> int:
        return 1024  # intfloat/multilingual-e5-large
