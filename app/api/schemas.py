from pydantic import BaseModel, Field, field_validator


class AnswerRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
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


class AnswerResponse(BaseModel):
    answer: str
    grounded: bool
    sources: list[SourceResponse]
    request_id: str


class HealthResponse(BaseModel):
    status: str