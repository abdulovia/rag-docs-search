"""Cross-Encoder Reranker"""

from typing import List, Tuple

from ...domain.entities.document import Document


class CrossEncoderReranker:
    """Cross-encoder reranking для улучшения precision

    Модели:
    - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast)
    - cross-encoder/ms-marco-MiniLM-L-12-v2 (better quality)
    - BAAI/bge-reranker-v2-m3 (multilingual)
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
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
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(
                self._model_name,
                device=self._device,
            )
        return self._model

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
    ) -> List[Tuple[Document, float]]:
        """Переранжирование документов по релевантности"""
        if not documents:
            return []

        # Подготавливаем пары (query, document)
        pairs = [(query, doc.page_content) for doc in documents]

        # Получаем scores
        scores = self._get_model.predict(
            pairs,
            batch_size=self._batch_size,
            show_progress_bar=False,
        )

        # Сортируем по убыванию score
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        return doc_scores[:top_k]
