import pytest

from app.core.errors import ProviderUnavailableError
from app.domain.models import (
    KnowledgeDocument,
    RetrievedDocument,
)
from app.services.support_assistant import (
    FALLBACK_ANSWER,
    SupportAssistant,
)

from tests.conftest import FakeGenerator, FakeRetriever


@pytest.mark.asyncio
async def test_returns_grounded_answer_for_relevant_context(
    password_document: KnowledgeDocument,
) -> None:
    retriever = FakeRetriever(
        results=[
            RetrievedDocument(
                document=password_document,
                score=0.92,
            )
        ]
    )

    generator = FakeGenerator(
        answer="The reset link is valid for 30 minutes."
    )

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    result = await assistant.answer(
        "How long is the reset link valid?"
    )

    assert result.grounded is True
    assert result.answer == (
        "The reset link is valid for 30 minutes."
    )

    assert len(result.sources) == 1
    assert result.sources[0].id == "snippet-1"
    assert result.sources[0].title == "Password Reset"
    assert result.sources[0].score == 0.92

    assert retriever.calls == [
        ("How long is the reset link valid?", 2)
    ]

    assert len(generator.calls) == 1
    assert generator.calls[0][0] == (
        "How long is the reset link valid?"
    )


@pytest.mark.asyncio
async def test_returns_fallback_when_no_results_exist() -> None:
    retriever = FakeRetriever(results=[])
    generator = FakeGenerator()

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    result = await assistant.answer(
        "Does NimbusCloud support SSO?"
    )

    assert result.grounded is False
    assert result.answer == FALLBACK_ANSWER
    assert result.sources == []
    assert generator.calls == []


@pytest.mark.asyncio
async def test_returns_fallback_when_score_is_below_threshold(
    password_document: KnowledgeDocument,
) -> None:
    retriever = FakeRetriever(
        results=[
            RetrievedDocument(
                document=password_document,
                score=0.3,
            )
        ]
    )

    generator = FakeGenerator()

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    result = await assistant.answer(
        "Does NimbusCloud support SSO?"
    )

    assert result.grounded is False
    assert result.sources == []
    assert generator.calls == []


@pytest.mark.asyncio
async def test_only_relevant_documents_are_sent_to_generator(
    password_document: KnowledgeDocument,
    storage_document: KnowledgeDocument,
) -> None:
    retriever = FakeRetriever(
        results=[
            RetrievedDocument(
                document=password_document,
                score=0.9,
            ),
            RetrievedDocument(
                document=storage_document,
                score=0.2,
            ),
        ]
    )

    generator = FakeGenerator(
        answer="Use Forgot password."
    )

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    await assistant.answer(
        "How do I reset my password?"
    )

    generated_context = generator.calls[0][1]

    assert len(generated_context) == 1
    assert generated_context[0].id == "snippet-1"


@pytest.mark.asyncio
async def test_sources_are_deterministic_and_not_model_generated(
    password_document: KnowledgeDocument,
) -> None:
    retriever = FakeRetriever(
        results=[
            RetrievedDocument(
                document=password_document,
                score=0.876543,
            )
        ]
    )

    generator = FakeGenerator(
        answer=(
            "According to an imaginary source, "
            "the reset link lasts one hour."
        )
    )

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    result = await assistant.answer(
        "How long is the reset link valid?"
    )

    assert result.sources[0].id == password_document.id
    assert result.sources[0].title == password_document.title
    assert result.sources[0].source == password_document.source
    assert result.sources[0].score == 0.8765


@pytest.mark.asyncio
async def test_generator_error_is_propagated(
    password_document: KnowledgeDocument,
) -> None:
    retriever = FakeRetriever(
        results=[
            RetrievedDocument(
                document=password_document,
                score=0.9,
            )
        ]
    )

    generator = FakeGenerator(
        error=ProviderUnavailableError()
    )

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    with pytest.raises(ProviderUnavailableError):
        await assistant.answer(
            "How do I reset my password?"
        )


@pytest.mark.asyncio
async def test_retriever_error_is_propagated() -> None:
    retriever = FakeRetriever(
        error=ProviderUnavailableError()
    )

    generator = FakeGenerator()

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        relevance_threshold=0.5,
        top_k=2,
    )

    with pytest.raises(ProviderUnavailableError):
        await assistant.answer(
            "How do I reset my password?"
        )