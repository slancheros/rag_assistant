from pydantic import BaseModel, Field, field_validator


class AnswerRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=10,
    )
    relevance_threshold: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )

    @field_validator("question")
    @classmethod
    def normalize_question(
        cls,
        value: str,
    ) -> str:
        normalized = " ".join(value.split())

        if not normalized:
            raise ValueError(
                "Question cannot be blank."
            )

        return normalized


class SourceResponse(BaseModel):
    id: str
    title: str
    source: str
    score: float


class RagParametersResponse(BaseModel):
    top_k: int
    relevance_threshold: float


class AnswerResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[SourceResponse]
    request_id: str
    parameters: RagParametersResponse


class RagConfigResponse(BaseModel):
    provider: str
    llm_model: str
    embedding_model: str
    document_count: int
    defaults: RagParametersResponse


class HealthResponse(BaseModel):
    status: str
