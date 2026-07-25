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
    ) -> SupportAnswer:
        retrieved_documents = await self.retriever.retrieve(
            query=question,
            limit=self.top_k,
        )

        relevant_documents = [
            item
            for item in retrieved_documents
            if item.score >= self.relevance_threshold
        ]

        logger.info(
            "retrieval_completed retrieved_ids=%s scores=%s",
            [
                item.document.id
                for item in retrieved_documents
            ],
            [
                round(item.score, 4)
                for item in retrieved_documents
            ],
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