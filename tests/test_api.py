from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.domain.models import SupportAnswer
from app.main import create_app


class FakeAssistant:
    async def answer(
        self,
        question: str,
    ) -> SupportAnswer:
        return SupportAnswer(
            answer="Test answer",
            grounded=True,
            sources=[],
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