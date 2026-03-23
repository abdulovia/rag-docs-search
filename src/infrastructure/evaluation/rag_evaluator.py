"""RAG Evaluator — оценка качества ответов через LLM"""

from typing import List

from ...application.services.prompt_registry import PromptRegistry
from ...domain.entities.document import Document
from ...domain.ports import LLMClient


class RAGEvaluator:
    """Оценка качества RAG через LLM"""

    def __init__(
        self,
        llm: LLMClient,
        prompt_registry: PromptRegistry,
    ):
        self._llm = llm
        self._prompts = prompt_registry

    async def check_faithfulness(self, context: str, answer: str) -> float:
        """Проверка, опирается ли ответ на контекст"""
        prompt = self._prompts.render(
            "grading/hallucination_check",
            context=context,
            answer=answer,
        )

        try:
            response = await self._llm.generate(prompt, temperature=0.0, max_tokens=10)
            score = float(response.strip())
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.5

    async def check_relevance(self, question: str, answer: str) -> float:
        """Проверка релевантности ответа вопросу"""
        prompt = self._prompts.render(
            "grading/answer_quality",
            question=question,
            answer=answer,
        )

        try:
            response = await self._llm.generate(prompt, temperature=0.0, max_tokens=10)
            score = float(response.strip())
            return max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            return 0.5

    async def grade_documents(
        self, query: str, documents: List[Document]
    ) -> List[float]:
        """Оценка релевантности документов"""
        scores = []
        for doc in documents:
            prompt = self._prompts.render(
                "grading/document_relevance",
                question=query,
                document=doc.page_content[:500],
            )

            try:
                response = await self._llm.generate(prompt, temperature=0.0, max_tokens=10)
                score = float(response.strip())
                scores.append(max(0.0, min(1.0, score)))
            except (ValueError, TypeError):
                scores.append(0.5)

        return scores
