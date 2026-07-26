from collections.abc import Sequence

import pytest
from fastapi.testclient import TestClient

from app.domain.models import (
    KnowledgeDocument,
    RetrievedDocument,
)
from app.main import app


class FakeEmbedder:
    def __init__(
        self,
        embeddings_by_text: dict[str, list[float]] | None = None,
        default_embedding: list[float] | None = None,
    ) -> None:
        self.embeddings_by_text = embeddings_by_text or {}
        self.default_embedding = default_embedding or [1.0, 0.0]
        self.calls: list[list[str]] = []

    async def embed(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        text_list = list(texts)
        self.calls.append(text_list)

        return [
            self.embeddings_by_text.get(
                text,
                self.default_embedding,
            )
            for text in text_list
        ]


class FakeRetriever:
    def __init__(
        self,
        results: list[RetrievedDocument] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.results = results or []
        self.error = error
        self.calls: list[tuple[str, int]] = []

    async def retrieve(
        self,
        query: str,
        limit: int,
    ) -> list[RetrievedDocument]:
        self.calls.append((query, limit))

        if self.error:
            raise self.error

        return self.results[:limit]


class FakeGenerator:
    def __init__(
        self,
        answer: str = "Generated answer",
        error: Exception | None = None,
    ) -> None:
        self.answer = answer
        self.error = error
        self.calls: list[
            tuple[str, Sequence[KnowledgeDocument]]
        ] = []

    async def generate(
        self,
        question: str,
        context: Sequence[KnowledgeDocument],
    ) -> str:
        self.calls.append((question, context))

        if self.error:
            raise self.error

        return self.answer


class FakeGroundingEvaluator:
    def __init__(
        self,
        grounded: bool = True,
        error: Exception | None = None,
    ) -> None:
        self.grounded = grounded
        self.error = error
        self.calls: list[
            tuple[str, Sequence[KnowledgeDocument]]
        ] = []

    async def is_grounded(
        self,
        answer: str,
        context: Sequence[KnowledgeDocument],
    ) -> bool:
        self.calls.append((answer, context))

        if self.error:
            raise self.error

        return self.grounded


@pytest.fixture
def password_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        id="snippet-1",
        title="Password Reset",
        content=(
            "To reset your password, select Forgot password. "
            "The reset link is valid for 30 minutes."
        ),
        source="knowledge_base.md",
    )


@pytest.fixture
def storage_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        id="snippet-2",
        title="Storage Limits",
        content=(
            "Free accounts include 5GB. "
            "Pro accounts include 500GB."
        ),
        source="knowledge_base.md",
    )


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)
