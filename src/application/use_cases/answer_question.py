"""Use case для ответа на вопросы через RAG pipeline"""

import time
from typing import List, Optional

from loguru import logger

from ...domain.entities.document import Document
from ...domain.entities.query import Query
from ...domain.entities.response import (
    Citation,
    ConfidenceLevel,
    GenerationResult,
    Message,
)
from ...domain.ports import Evaluator, LLMClient, Reranker, Retriever, WebSearch
from ..services.prompt_registry import PromptRegistry


class AnswerQuestionUseCase:
    """RAG pipeline для ответа на вопросы"""

    def __init__(
        self,
        retriever: Retriever,
        reranker: Optional[Reranker],
        llm: LLMClient,
        prompt_registry: PromptRegistry,
        evaluator: Optional[Evaluator] = None,
        web_search: Optional[WebSearch] = None,
        max_retries: int = 2,
        enable_self_correction: bool = True,
        enable_reranking: bool = True,
        min_score: float = 0.0,
    ):
        self._retriever = retriever
        self._reranker = reranker
        self._llm = llm
        self._prompts = prompt_registry
        self._evaluator = evaluator
        self._web_search = web_search
        self._max_retries = max_retries
        self._enable_self_correction = enable_self_correction
        self._enable_reranking = enable_reranking
        self._min_score = min_score

    async def execute(
        self,
        question: str,
        top_k: int = 5,
        conversation_history: Optional[List[Message]] = None,
        enable_citations: bool = True,
        enable_web_search: bool = False,
    ) -> GenerationResult:
        """Выполнить Rаг pipeline"""
        start_time = time.time()
        
        logger.info(f"RAG Pipeline started: question='{question[:50]}...', web_search={enable_web_search}")

        query = Query(text=question)

        # Phase 1: Retrieval из документов
        logger.debug(f"Phase 1: Retrieval from documents (top_k={top_k})")
        documents_with_scores = await self._retriever.retrieve(query, top_k=top_k)
        documents = [doc for doc, _ in documents_with_scores]
        logger.debug(f"Retrieved {len(documents)} documents, scores: {[f'{s:.3f}' for _, s in documents_with_scores[:3]]}")

        # Фильтруем документы по минимальному score
        good_docs = [doc for doc, score in documents_with_scores if score >= self._min_score]
        logger.debug(f"After filtering (min_score={self._min_score}): {len(good_docs)} good documents")

        # Проверяем максимальный score
        max_score = max([score for _, score in documents_with_scores], default=0.0)
        relevance_threshold = 0.2
        
        # Приоритет документам: если score >= 0.2, используем их без LLM проверки
        if max_score >= relevance_threshold and good_docs:
            logger.info(f"Documents found (max_score={max_score:.3f} >= {relevance_threshold}), using them")
            # good_docs уже установлены
        elif good_docs:
            # score < 0.2, но документы есть - проверяем через LLM только если нет веб-поиска
            if not enable_web_search:
                logger.info(f"Low score ({max_score:.3f} < {relevance_threshold}), checking with LLM")
                is_relevant = await self._check_documents_relevance(question, good_docs[:2])
                if not is_relevant:
                    logger.info("LLM: documents not relevant, using direct LLM")
                    good_docs = []
            else:
                # Веб-поиск включен - пропускаем документы с низким score
                logger.info(f"Low score ({max_score:.3f}), web search enabled, skipping documents")
                good_docs = []
        else:
            good_docs = []

        # Phase 1.5: Web Search если включён
        web_search_used = False
        if enable_web_search and self._web_search:
            logger.debug("Phase 1.5: Web search enabled, searching...")
            web_results = await self._web_search.search(question, max_results=3)
            logger.debug(f"Web search returned {len(web_results)} results")
            if web_results:
                documents = web_results
                web_search_used = True
                logger.info(f"Using web search results: {len(web_results)} web results")
        elif not good_docs:
            # Нет релевантных документов
            documents = []
            logger.info("No relevant documents found")
        else:
            # Есть релевантные документы
            documents = good_docs

        # Phase 2: Если ничего не найдено — direct LLM
        if not documents:
            logger.info("Phase 2: No context found, using direct LLM")
            answer = await self._generate_direct(
                question=question,
                conversation_history=conversation_history,
            )
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Direct LLM completed in {elapsed:.0f}ms")
            return GenerationResult(
                answer=f"[Сгенерировано] {answer}",
                confidence=ConfidenceLevel.MEDIUM,
                is_valid=True,
                citations=[],
                metadata={
                    "processing_time_ms": elapsed,
                    "source": "direct_llm",
                    "source_label": "Сгенерировано",
                },
            )

        # Phase 3: Reranking (optional)
        if self._enable_reranking and self._reranker and not web_search_used:
            logger.debug("Phase 3: Reranking documents")
            reranked = await self._reranker.rerank(question, documents, top_k=5)
            documents = [doc for doc, _ in reranked]
            documents_with_scores = reranked
            logger.debug(f"After reranking: {len(documents)} documents")

        # Phase 4: Generation с self-check
        logger.debug(f"Phase 4: Generation with {len(documents)} context documents")
        result = None
        for attempt in range(self._max_retries + 1):
            logger.debug(f"Generation attempt {attempt + 1}/{self._max_retries + 1}")
            result = await self._generate(
                question=question,
                documents=documents,
                conversation_history=conversation_history,
                enable_citations=enable_citations,
                attempt=attempt,
            )

            if result.is_valid:
                logger.debug(f"Generation successful on attempt {attempt + 1}")
                break
            else:
                logger.warning(f"Generation attempt {attempt + 1} invalid (faithfulness={result.faithfulness_score}, relevance={result.relevance_score})")

        # Phase 5: Post-processing
        if result is None:
            logger.error("All generation attempts failed")
            result = GenerationResult(
                answer="Не удалось сгенерировать ответ.",
                confidence=ConfidenceLevel.LOW,
            )

        elapsed = (time.time() - start_time) * 1000
        result.metadata["processing_time_ms"] = elapsed
        
        if web_search_used:
            result.metadata["source"] = "web_search"
            result.metadata["source_label"] = "Из интернета"
        else:
            # Проверяем ответил ли LLM или написал что нет информации
            context_text = "\n".join([doc.page_content[:200] for doc in documents[:3]])
            actually_answered = await self._check_if_answered(
                question=question,
                context=context_text,
                answer=result.answer,
            )
            if not actually_answered:
                logger.info("LLM did not answer → switching to direct LLM")
                direct_answer = await self._generate_direct(
                    question=question,
                    conversation_history=conversation_history,
                )
                result.answer = direct_answer
                result.metadata["source"] = "generated"
                result.metadata["source_label"] = "Сгенерировано"
                result.citations = []
            else:
                result.metadata["source"] = "documents"
                result.metadata["source_label"] = "Из документов"
        
        # Добавляем приписку к ответу
        source_label = result.metadata.get("source_label", "")
        if source_label and not result.answer.startswith(f"[{source_label}]"):
            result.answer = f"[{source_label}] {result.answer}"
        
        logger.info(f"RAG Pipeline completed in {elapsed:.0f}ms: source={result.metadata.get('source', 'documents')}, citations={len(result.citations)}")
        return result
        
        # Добавляем приписку к ответу
        source_label = result.metadata.get("source_label", "")
        if source_label and not result.answer.startswith(f"[{source_label}]"):
            result.answer = f"[{source_label}] {result.answer}"
        
        logger.info(f"RAG Pipeline completed in {elapsed:.0f}ms: source={result.metadata.get('source', 'documents')}, citations={len(result.citations)}")
        return result

    async def _generate(
        self,
        question: str,
        documents: List[Document],
        conversation_history: Optional[List[Message]],
        enable_citations: bool,
        attempt: int,
    ) -> GenerationResult:
        """Генерация ответа с опциональной проверкой"""

        # Формируем контекст с явным маппингом [N] -> источник
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.source if hasattr(doc, "metadata") else "unknown"
            page = doc.metadata.page if hasattr(doc, "metadata") and doc.metadata.page else ""
            page_info = f", стр. {page}" if page else ""
            context_parts.append(f"[{i}] Источник: {source}{page_info}\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        # Всегда используем answer_with_citations когда есть документы
        prompt = self._prompts.render(
            "rag/answer_with_citations",
            context=context,
            question=question,
            conversation_history=conversation_history,
        )

        # Генерация
        answer = await self._llm.generate(prompt, temperature=0.0, max_tokens=1024)

        # Self-check (optional)
        is_valid = True
        faithfulness_score = None
        relevance_score = None

        if self._enable_self_correction and self._evaluator:
            faithfulness_score = await self._evaluator.check_faithfulness(context, answer)
            relevance_score = await self._evaluator.check_relevance(question, answer)

            if faithfulness_score < 0.7 or relevance_score < 0.6:
                is_valid = False

        # Извлекаем citations из ответа
        citations = []
        if enable_citations:
            citations = self._extract_citations(answer, documents)

        # Определяем confidence
        confidence = ConfidenceLevel.MEDIUM
        if faithfulness_score and relevance_score:
            avg_score = (faithfulness_score + relevance_score) / 2
            if avg_score >= 0.8:
                confidence = ConfidenceLevel.HIGH
            elif avg_score < 0.5:
                confidence = ConfidenceLevel.LOW

        return GenerationResult(
            answer=answer,
            citations=citations,
            confidence=confidence,
            faithfulness_score=faithfulness_score,
            relevance_score=relevance_score,
            is_valid=is_valid,
            attempt=attempt + 1,
        )

    def _extract_citations(
        self, answer: str, documents: List[Document]
    ) -> List[Citation]:
        """Извлечение citations из ответа с валидацией"""
        import re

        citations = []
        # Ищем паттерн [N] где N - число от 1 до количества документов
        pattern = r"\[(\d+)\]"
        matches = re.findall(pattern, answer)

        seen = set()
        max_doc_index = len(documents)

        for match in matches:
            idx = int(match) - 1
            
            # Валидация: индекс должен быть в диапазоне документов
            if idx < 0 or idx >= max_doc_index:
                logger.debug(f"Citation [{match}] out of range (max: {max_doc_index}), skipping")
                continue
            
            if idx in seen:
                continue
            
            seen.add(idx)
            doc = documents[idx]
            source = doc.metadata.source if hasattr(doc, "metadata") else "unknown"
            page = doc.metadata.page if hasattr(doc, "metadata") else None

            logger.debug(f"Citation [{match}] validated: source={source}, page={page}")
            citations.append(
                Citation(
                    index=idx + 1,
                    source=source,
                    page=page,
                    snippet=doc.page_content[:200],
                    relevance_score=1.0,
                )
            )

        logger.debug(f"Extracted {len(citations)} valid citations from {len(matches)} matches")
        return citations

    async def _check_documents_relevance(
        self,
        question: str,
        documents: List[Document],
    ) -> bool:
        """Проверка релевантности документов через LLM"""
        logger.debug(f"Checking relevance of {len(documents)} documents for question")
        
        prompt = self._prompts.render(
            "grading/documents_relevance_check",
            question=question,
            documents=documents,
        )
        
        response = await self._llm.generate(prompt, temperature=0.0, max_tokens=10)
        response_lower = response.strip().lower()
        
        is_relevant = response_lower.startswith("да") or response_lower.startswith("yes")
        logger.debug(f"LLM relevance check result: '{response[:20]}...' -> relevant={is_relevant}")
        
        return is_relevant

    async def _check_faithfulness(
        self,
        context: str,
        answer: str,
    ) -> bool:
        """Проверка опирается ли ответ на контекст"""
        logger.debug("Checking faithfulness of answer")
        
        prompt = self._prompts.render(
            "grading/faithfulness_check",
            context=context[:1000],
            answer=answer[:500],
        )
        
        response = await self._llm.generate(prompt, temperature=0.0, max_tokens=10)
        response_lower = response.strip().lower()
        
        is_faithful = response_lower.startswith("да") or response_lower.startswith("yes")
        logger.debug(f"Faithfulness check: '{response[:20]}...' -> faithful={is_faithful}")
        
        return is_faithful

    async def _check_if_answered(
        self,
        question: str,
        context: str,
        answer: str,
    ) -> bool:
        """Проверка дал ли LLM полезный ответ или написал что нет информации"""
        logger.debug("Checking if LLM actually answered the question")
        
        prompt = self._prompts.render(
            "grading/no_info_check",
            question=question,
            context=context[:500],
            answer=answer[:500],
        )
        
        response = await self._llm.generate(prompt, temperature=0.0, max_tokens=10)
        response_lower = response.strip().lower()
        
        # "Да" = LLM ответил, "Нет" = LLM не нашёл информацию
        answered = response_lower.startswith("да") or response_lower.startswith("yes")
        logger.debug(f"Answered check: '{response[:20]}...' -> answered={answered}")
        
        return answered

    async def _generate_direct(
        self,
        question: str,
        conversation_history: Optional[List[Message]] = None,
    ) -> str:
        """Генерация ответа напрямую без контекста документов"""
        logger.debug(f"Direct LLM generation for: '{question[:50]}...'")
        prompt = self._prompts.render(
            "rag/direct_llm",
            question=question,
            conversation_history=conversation_history,
        )
        logger.debug(f"Direct prompt length: {len(prompt)} chars")
        answer = await self._llm.generate(prompt, temperature=0.0, max_tokens=1024)
        logger.debug(f"Direct LLM answer length: {len(answer)} chars")
        return answer
