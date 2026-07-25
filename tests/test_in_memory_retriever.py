import pytest

from app.domain.models import KnowledgeDocument
from app.retrieval.in_memory_retriever import (
    InMemoryRetriever,
    cosine_similarity,
)

from tests.conftest import FakeEmbedder


def test_cosine_similarity_for_identical_vectors() -> None:
    score = cosine_similarity(
        [1.0, 0.0],
        [1.0, 0.0],
    )

    assert score == pytest.approx(1.0)


def test_cosine_similarity_for_orthogonal_vectors() -> None:
    score = cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    assert score == pytest.approx(0.0)


def test_cosine_similarity_returns_zero_for_zero_vector() -> None:
    score = cosine_similarity(
        [0.0, 0.0],
        [1.0, 0.0],
    )

    assert score == 0.0


def test_cosine_similarity_rejects_different_dimensions() -> None:
    with pytest.raises(
        ValueError,
        match="same dimensions",
    ):
        cosine_similarity(
            [1.0, 0.0],
            [1.0],
        )


@pytest.mark.asyncio
async def test_create_embeds_title_and_content(
    password_document: KnowledgeDocument,
) -> None:
    indexed_text = (
        f"{password_document.title}\n\n"
        f"{password_document.content}"
    )

    embedder = FakeEmbedder(
        embeddings_by_text={
            indexed_text: [1.0, 0.0],
        }
    )

    retriever = await InMemoryRetriever.create(
        documents=[password_document],
        embedder=embedder,
    )

    assert retriever.documents == [password_document]
    assert retriever.vectors == [[1.0, 0.0]]
    assert embedder.calls == [[indexed_text]]


@pytest.mark.asyncio
async def test_retrieve_orders_documents_by_score(
    password_document: KnowledgeDocument,
    storage_document: KnowledgeDocument,
) -> None:
    question = "How do I reset my password?"

    embedder = FakeEmbedder(
        embeddings_by_text={
            question: [1.0, 0.0],
        }
    )

    retriever = InMemoryRetriever(
        documents=[
            password_document,
            storage_document,
        ],
        vectors=[
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        embedder=embedder,
    )

    results = await retriever.retrieve(
        query=question,
        limit=2,
    )

    assert len(results) == 2
    assert results[0].document.id == "snippet-1"
    assert results[0].score == pytest.approx(1.0)

    assert results[1].document.id == "snippet-2"
    assert results[1].score == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_retrieve_respects_limit(
    password_document: KnowledgeDocument,
    storage_document: KnowledgeDocument,
) -> None:
    embedder = FakeEmbedder(
        default_embedding=[1.0, 0.0]
    )

    retriever = InMemoryRetriever(
        documents=[
            password_document,
            storage_document,
        ],
        vectors=[
            [1.0, 0.0],
            [0.8, 0.2],
        ],
        embedder=embedder,
    )

    results = await retriever.retrieve(
        query="question",
        limit=1,
    )

    assert len(results) == 1


@pytest.mark.asyncio
async def test_retrieve_rejects_blank_query(
    password_document: KnowledgeDocument,
) -> None:
    embedder = FakeEmbedder()

    retriever = InMemoryRetriever(
        documents=[password_document],
        vectors=[[1.0, 0.0]],
        embedder=embedder,
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        await retriever.retrieve(
            query="   ",
            limit=1,
        )


@pytest.mark.asyncio
async def test_retrieve_rejects_invalid_limit(
    password_document: KnowledgeDocument,
) -> None:
    embedder = FakeEmbedder()

    retriever = InMemoryRetriever(
        documents=[password_document],
        vectors=[[1.0, 0.0]],
        embedder=embedder,
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        await retriever.retrieve(
            query="password",
            limit=0,
        )


@pytest.mark.asyncio
async def test_create_rejects_empty_documents() -> None:
    embedder = FakeEmbedder()

    with pytest.raises(
        ValueError,
        match="At least one knowledge document",
    ):
        await InMemoryRetriever.create(
            documents=[],
            embedder=embedder,
        )


def test_constructor_rejects_mismatched_documents_and_vectors(
    password_document: KnowledgeDocument,
) -> None:
    embedder = FakeEmbedder()

    with pytest.raises(
        ValueError,
        match="one embedding vector",
    ):
        InMemoryRetriever(
            documents=[password_document],
            vectors=[],
            embedder=embedder,
        )