from types import SimpleNamespace

import pytest

from app.core.errors import ProviderUnavailableError
from app.domain.models import KnowledgeDocument
from app.generation.openai_grounding_evaluator import (
    OpenAIGroundingEvaluator,
)


@pytest.fixture
def document() -> KnowledgeDocument:
    return KnowledgeDocument(
        id="snippet-1",
        title="Password Reset",
        content="The reset link is valid for 30 minutes.",
        source="knowledge_base.md",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("verdict", "expected"),
    [
        ("GROUNDED", True),
        ("UNGROUNDED", False),
    ],
)
async def test_evaluator_returns_provider_verdict(
    monkeypatch: pytest.MonkeyPatch,
    document: KnowledgeDocument,
    verdict: str,
    expected: bool,
) -> None:
    evaluator = OpenAIGroundingEvaluator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        assert document.content in kwargs["input"]
        assert "30 minutes" in kwargs["input"]
        return SimpleNamespace(output_text=verdict)

    monkeypatch.setattr(
        evaluator.client.responses,
        "create",
        fake_create,
    )

    result = await evaluator.is_grounded(
        answer="The reset link is valid for 30 minutes.",
        context=[document],
    )

    assert result is expected


@pytest.mark.asyncio
async def test_evaluator_rejects_invalid_verdict(
    monkeypatch: pytest.MonkeyPatch,
    document: KnowledgeDocument,
) -> None:
    evaluator = OpenAIGroundingEvaluator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        return SimpleNamespace(output_text="MAYBE")

    monkeypatch.setattr(
        evaluator.client.responses,
        "create",
        fake_create,
    )

    with pytest.raises(ValueError, match="invalid verdict"):
        await evaluator.is_grounded(
            answer="An answer",
            context=[document],
        )


@pytest.mark.asyncio
async def test_evaluator_maps_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
    document: KnowledgeDocument,
) -> None:
    evaluator = OpenAIGroundingEvaluator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        raise RuntimeError("Provider failed")

    monkeypatch.setattr(
        evaluator.client.responses,
        "create",
        fake_create,
    )

    with pytest.raises(ProviderUnavailableError):
        await evaluator.is_grounded(
            answer="An answer",
            context=[document],
        )
