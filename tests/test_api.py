from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.domain.models import Source, SupportAnswer
from app.main import create_app


class FakeAssistant:
    top_k = 2
    relevance_threshold = 0.35

    async def answer(
        self,
        question: str,
        top_k: int | None = None,
        relevance_threshold: float | None = None,
    ) -> SupportAnswer:
        return SupportAnswer(
            answer="Test answer",
            grounded=True,
            sources=[
                Source(
                    id="snippet-1",
                    title="Password Reset",
                    source="knowledge_base.md",
                    score=0.92,
                )
            ],
        )


@dataclass
class FakeContainer:
    assistant: FakeAssistant


@pytest.fixture
def client() -> TestClient:
    async def build_fake_container():
        return FakeContainer(
            assistant=FakeAssistant()
        )

    test_app = create_app(
        container_builder=build_fake_container
    )

    with TestClient(test_app) as test_client:
        yield test_client


def test_answer_serializes_domain_sources(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/answer",
        json={"question": "How do I reset my password?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Test answer"
    assert body["grounded"] is True
    assert body["sources"] == [
        {
            "id": "snippet-1",
            "title": "Password Reset",
            "source": "knowledge_base.md",
            "score": 0.92,
        }
    ]
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == (
        body["request_id"]
    )
    assert body["parameters"] == {
        "top_k": 2,
        "relevance_threshold": 0.35,
    }
