from types import SimpleNamespace

import pytest

from app.core.errors import ProviderUnavailableError
from app.domain.models import KnowledgeDocument
from app.generation.openai_generator import (
    OpenAIAnswerGenerator,
)


@pytest.mark.asyncio
async def test_generate_returns_model_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OpenAIAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        return SimpleNamespace(
            output_text="The reset link is valid for 30 minutes."
        )

    monkeypatch.setattr(
        generator.client.responses,
        "create",
        fake_create,
    )

    document = KnowledgeDocument(
        id="snippet-1",
        title="Password Reset",
        content="The reset link is valid for 30 minutes.",
        source="knowledge_base.md",
    )

    result = await generator.generate(
        question="How long is the reset link valid?",
        context=[document],
    )

    assert result == (
        "The reset link is valid for 30 minutes."
    )


@pytest.mark.asyncio
async def test_generate_rejects_blank_question() -> None:
    generator = OpenAIAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    document = KnowledgeDocument(
        id="snippet-1",
        title="Password Reset",
        content="Reset instructions.",
        source="knowledge_base.md",
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty",
    ):
        await generator.generate(
            question="   ",
            context=[document],
        )


@pytest.mark.asyncio
async def test_generate_rejects_empty_context() -> None:
    generator = OpenAIAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    with pytest.raises(
        ValueError,
        match="context document",
    ):
        await generator.generate(
            question="How do I reset my password?",
            context=[],
        )


@pytest.mark.asyncio
async def test_generate_rejects_empty_model_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OpenAIAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        return SimpleNamespace(
            output_text="   "
        )

    monkeypatch.setattr(
        generator.client.responses,
        "create",
        fake_create,
    )

    document = KnowledgeDocument(
        id="snippet-1",
        title="Password Reset",
        content="Reset instructions.",
        source="knowledge_base.md",
    )

    with pytest.raises(
        ValueError,
        match="empty answer",
    ):
        await generator.generate(
            question="How do I reset my password?",
            context=[document],
        )


@pytest.mark.asyncio
async def test_generate_maps_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator = OpenAIAnswerGenerator(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        raise RuntimeError("Provider failed")

    monkeypatch.setattr(
        generator.client.responses,
        "create",
        fake_create,
    )

    document = KnowledgeDocument(
        id="snippet-1",
        title="Password Reset",
        content="Reset instructions.",
        source="knowledge_base.md",
    )

    with pytest.raises(ProviderUnavailableError):
        await generator.generate(
            question="How do I reset my password?",
            context=[document],
        )