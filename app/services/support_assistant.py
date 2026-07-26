import logging
from dataclasses import replace
from hashlib import sha256

from app.domain.models import (
    CacheMetadata,
    SecurityMetadata,
    Source,
    SupportAnswer,
)
from app.domain.protocols import (
    AnswerGenerator,
    GroundingEvaluator,
    Retriever,
)
from app.security.prompt_injection import (
    assess_context,
    assess_question,
)
from app.services.answer_cache import TTLAnswerCache


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
        grounding_evaluator: GroundingEvaluator,
        relevance_threshold: float,
        top_k: int,
        cache: TTLAnswerCache | None = None,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.grounding_evaluator = grounding_evaluator
        self.relevance_threshold = relevance_threshold
        self.top_k = top_k
        self.cache = cache

    async def answer(
        self,
        question: str,
        top_k: int | None = None,
        relevance_threshold: float | None = None,
    ) -> SupportAnswer:
        question_assessment = assess_question(question)
        if question_assessment.detected:
            logger.warning(
                "prompt_injection_blocked",
                extra={
                    "reason": question_assessment.reason,
                    "source": "question",
                },
            )
            return self._blocked_answer(
                question_assessment.reason
            )

        selected_top_k = (
            top_k if top_k is not None else self.top_k
        )
        selected_threshold = (
            relevance_threshold
            if relevance_threshold is not None
            else self.relevance_threshold
        )
        cache_key = self._cache_key(
            question=question,
            top_k=selected_top_k,
            relevance_threshold=selected_threshold,
        )

        if self.cache is not None:
            cached_entry = await self.cache.get(cache_key)
            if cached_entry is not None:
                logger.info(
                    "answer_cache_hit",
                    extra={
                        "top_k": selected_top_k,
                        "relevance_threshold": (
                            selected_threshold
                        ),
                    },
                )
                return replace(
                    cached_entry.answer,
                    cache=CacheMetadata(
                        hit=True,
                        status="hit",
                        cached_at=cached_entry.created_at,
                        expires_at=cached_entry.expires_at,
                    ),
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
            return await self._cache_answer(
                cache_key,
                SupportAnswer(
                    answer=FALLBACK_ANSWER,
                    grounded=False,
                    sources=[],
                ),
            )

        generated_context = [
            item.document
            for item in relevant_documents
        ]
        context_assessment = assess_context(
            generated_context
        )
        if context_assessment.detected:
            logger.warning(
                "prompt_injection_blocked",
                extra={
                    "reason": context_assessment.reason,
                    "source": "retrieved_context",
                    "context_ids": [
                        document.id
                        for document in generated_context
                    ],
                },
            )
            return self._blocked_answer(
                context_assessment.reason
            )

        generated_answer = await self.generator.generate(
            question=question,
            context=generated_context,
        )

        answer_is_grounded = (
            await self.grounding_evaluator.is_grounded(
                answer=generated_answer,
                context=generated_context,
            )
        )

        logger.info(
            "grounding_check_completed",
            extra={
                "grounded": answer_is_grounded,
                "context_ids": [
                    document.id
                    for document in generated_context
                ],
            },
        )

        if not answer_is_grounded:
            return SupportAnswer(
                answer=FALLBACK_ANSWER,
                grounded=False,
                sources=[],
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

        return await self._cache_answer(
            cache_key,
            SupportAnswer(
                answer=generated_answer,
                grounded=True,
                sources=sources,
            ),
        )

    async def invalidate_cache(self) -> int:
        if self.cache is None:
            return 0
        return await self.cache.invalidate()

    async def _cache_answer(
        self,
        key: str,
        answer: SupportAnswer,
    ) -> SupportAnswer:
        if self.cache is None:
            return answer

        entry = await self.cache.set(key, answer)
        logger.info("answer_cache_stored")
        return replace(
            answer,
            cache=CacheMetadata(
                hit=False,
                status="miss",
                cached_at=entry.created_at,
                expires_at=entry.expires_at,
            ),
        )

    @staticmethod
    def _cache_key(
        question: str,
        top_k: int,
        relevance_threshold: float,
    ) -> str:
        normalized_question = " ".join(
            question.lower().split()
        )
        key_material = (
            f"{normalized_question}|{top_k}|"
            f"{relevance_threshold:.6f}"
        )
        return sha256(key_material.encode()).hexdigest()

    @staticmethod
    def _blocked_answer(
        reason: str | None,
    ) -> SupportAnswer:
        return SupportAnswer(
            answer=FALLBACK_ANSWER,
            grounded=False,
            sources=[],
            security=SecurityMetadata(
                prompt_injection_detected=True,
                blocked=True,
                reason=reason,
            ),
        )
