from types import SimpleNamespace

import pytest

from app.core.errors import ProviderUnavailableError
from app.retrieval.openai_embedder import OpenAIEmbedder


@pytest.mark.asyncio
async def test_embed_returns_vectors_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedder = OpenAIEmbedder(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    embedding=[1.0, 0.0]
                ),
                SimpleNamespace(
                    embedding=[0.0, 1.0]
                ),
            ]
        )

    monkeypatch.setattr(
        embedder.client.embeddings,
        "create",
        fake_create,
    )

    result = await embedder.embed(
        ["password", "storage"]
    )

    assert result == [
        [1.0, 0.0],
        [0.0, 1.0],
    ]


@pytest.mark.asyncio
async def test_embed_rejects_empty_input() -> None:
    embedder = OpenAIEmbedder(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    with pytest.raises(
        ValueError,
        match="At least one non-empty text",
    ):
        await embedder.embed([])


@pytest.mark.asyncio
async def test_embed_rejects_blank_input() -> None:
    embedder = OpenAIEmbedder(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    with pytest.raises(
        ValueError,
        match="At least one non-empty text",
    ):
        await embedder.embed(
            ["   ", ""]
        )


@pytest.mark.asyncio
async def test_embed_maps_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedder = OpenAIEmbedder(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        raise RuntimeError("Embedding provider failed")

    monkeypatch.setattr(
        embedder.client.embeddings,
        "create",
        fake_create,
    )

    with pytest.raises(ProviderUnavailableError):
        await embedder.embed(
            ["password reset"]
        )


@pytest.mark.asyncio
async def test_embed_rejects_wrong_number_of_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedder = OpenAIEmbedder(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
    )

    async def fake_create(**kwargs):
        return SimpleNamespace(
            data=[
                SimpleNamespace(
                    embedding=[1.0, 0.0]
                )
            ]
        )

    monkeypatch.setattr(
        embedder.client.embeddings,
        "create",
        fake_create,
    )

    with pytest.raises(
        ValueError,
        match="unexpected number of vectors",
    ):
        await embedder.embed(
            ["password", "storage"]
        )