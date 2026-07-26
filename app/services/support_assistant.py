import logging

from app.domain.models import Source, SupportAnswer
from app.domain.protocols import (
    AnswerGenerator,
    Retriever,
)


logger = logging.getLogger(__name__)


FALLBACK_ANSWER = (
    "I could not find enough information in the NimbusCloud "
    "knowledge base to answer that reliably. "
    "Please contact a support representative."
)


class SupportAssistant:
    def __init__(
        self,
        retriever: Retriever,
        generator: AnswerGenerator,
        relevance_threshold: float,
        top_k: int,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.relevance_threshold = relevance_threshold
        self.top_k = top_k

    async def answer(
        self,
        question: str,
        top_k: int | None = None,
        relevance_threshold: float | None = None,
    ) -> SupportAnswer:
        selected_top_k = (
            top_k if top_k is not None else self.top_k
        )
        selected_threshold = (
            relevance_threshold
            if relevance_threshold is not None
            else self.relevance_threshold
        )

        retrieved_documents = await self.retriever.retrieve(
            query=question,
            limit=selected_top_k,
        )

        relevant_documents = [
            item
            for item in retrieved_documents
            if item.score >= selected_threshold
        ]

        logger.info(
            "retrieval_completed",
            extra={
                "top_k": selected_top_k,
                "relevance_threshold": selected_threshold,
                "retrieved_ids": [
                    item.document.id
                    for item in retrieved_documents
                ],
                "scores": [
                    round(item.score, 4)
                    for item in retrieved_documents
                ],
                "relevant_count": len(relevant_documents),
            },
        )

        if not relevant_documents:
            return SupportAnswer(
                answer=FALLBACK_ANSWER,
                grounded=False,
                sources=[],
            )

        generated_answer = await self.generator.generate(
            question=question,
            context=[
                item.document
                for item in relevant_documents
            ],
        )

        sources = [
            Source(
                id=item.document.id,
                title=item.document.title,
                source=item.document.source,
                score=round(item.score, 4),
            )
            for item in relevant_documents
        ]

        return SupportAnswer(
            answer=generated_answer,
            grounded=True,
            sources=sources,
        )
