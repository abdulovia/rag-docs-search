"""Chat Router — endpoints для вопросов"""


from fastapi import APIRouter, Depends

from ....application.dto.request_dto import QuestionRequest
from ....application.dto.response_dto import AnswerResponse, CitationDTO
from ....application.use_cases.answer_question import AnswerQuestionUseCase
from ..dependencies import get_answer_use_case

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    use_case: AnswerQuestionUseCase = Depends(get_answer_use_case),
):
    """Задать вопрос и получить ответ с источниками"""
    result = await use_case.execute(
        question=request.question,
        top_k=request.top_k,
        enable_citations=request.enable_citations,
        enable_web_search=request.enable_web_search,
    )

    return AnswerResponse(
        answer=result.answer,
        citations=[
            CitationDTO(
                index=c.index,
                source=c.source,
                page=c.page,
                snippet=c.snippet,
                relevance_score=c.relevance_score,
            )
            for c in result.citations
        ],
        confidence=result.confidence.value,
        reasoning=result.reasoning,
        follow_up_questions=result.follow_up_questions,
        processing_time_ms=result.metadata.get("processing_time_ms"),
        metadata=result.metadata,
    )
