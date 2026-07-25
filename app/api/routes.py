from uuid import uuid4

from fastapi import APIRouter, Request

from app.api.schemas import (
    AnswerRequest,
    AnswerResponse,
    HealthResponse,
)


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/answer",
    response_model=AnswerResponse,
)
async def answer(
    payload: AnswerRequest,
    request: Request,
) -> AnswerResponse:
    request_id = str(uuid4())

    request.state.request_id = request_id

    result = await (
        request.app.state.container.assistant.answer(
            payload.question
        )
    )

    return AnswerResponse(
        answer=result.answer,
        grounded=result.grounded,
        sources=result.sources,
        request_id=request_id,
    )