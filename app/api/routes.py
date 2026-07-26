from fastapi import APIRouter, Depends, Request

from app.api.schemas import (
    AnswerRequest,
    AnswerResponse,
    HealthResponse,
    RagConfigResponse,
    RagParametersResponse,
    SecurityResponse,
    SourceResponse,
)
from app.api.security import require_api_key


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/config",
    response_model=RagConfigResponse,
    dependencies=[Depends(require_api_key)],
)
async def config(request: Request) -> RagConfigResponse:
    assistant = request.app.state.container.assistant

    return RagConfigResponse(
        provider=request.app.state.settings.ai_provider,
        llm_model=assistant.generator.model,
        embedding_model=assistant.retriever.embedder.model,
        document_count=len(assistant.retriever.documents),
        defaults=RagParametersResponse(
            top_k=assistant.top_k,
            relevance_threshold=assistant.relevance_threshold,
        ),
    )


@router.post(
    "/answer",
    response_model=AnswerResponse,
    dependencies=[Depends(require_api_key)],
)
async def answer(
    payload: AnswerRequest,
    request: Request,
) -> AnswerResponse:
    request_id = request.state.request_id

    result = await (
        request.app.state.container.assistant.answer(
            payload.question,
            top_k=payload.top_k,
            relevance_threshold=payload.relevance_threshold,
        )
    )

    assistant = request.app.state.container.assistant

    return AnswerResponse(
        answer=result.answer,
        grounded=result.grounded,
        sources=[
            SourceResponse(
                id=source.id,
                title=source.title,
                source=source.source,
                score=source.score,
            )
            for source in result.sources
        ],
        request_id=request_id,
        parameters=RagParametersResponse(
            top_k=(
                payload.top_k
                if payload.top_k is not None
                else assistant.top_k
            ),
            relevance_threshold=(
                payload.relevance_threshold
                if payload.relevance_threshold is not None
                else assistant.relevance_threshold
            ),
        ),
        security=SecurityResponse(
            prompt_injection_detected=(
                result.security.prompt_injection_detected
            ),
            blocked=result.security.blocked,
            reason=result.security.reason,
        ),
    )
