from app.domain.models import (
    KnowledgeDocument,
    RetrievedDocument,
)
from app.services.support_assistant import SupportAssistant
from tests.conftest import (
    FakeGenerator,
    FakeGroundingEvaluator,
    FakeRetriever,
)


def build_assistant(
    document: KnowledgeDocument,
) -> tuple[
    SupportAssistant,
    FakeRetriever,
    FakeGenerator,
]:
    retriever = FakeRetriever(
        results=[
            RetrievedDocument(
                document=document,
                score=0.95,
            )
        ]
    )
    generator = FakeGenerator(answer="Generated answer")
    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        grounding_evaluator=FakeGroundingEvaluator(),
        relevance_threshold=0.5,
        top_k=2,
    )
    return assistant, retriever, generator
