from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from app.domain.models import KnowledgeDocument, RetrievedDocument


EmbeddingVector = list[float]
EmbeddingBatch = list[EmbeddingVector]


@runtime_checkable
class Embedder(Protocol):
    """
    Contract for components that convert text into embedding vectors.
    """

    async def embed(
        self,
        texts: Sequence[str],
    ) -> EmbeddingBatch:
        """
        Generate one embedding vector per input text.

        The returned vectors must preserve the same ordering as the
        supplied texts.
        """
        ...


@runtime_checkable
class Retriever(Protocol):
    """
    Contract for components that retrieve relevant knowledge-base content.
    """

    async def retrieve(
        self,
        query: str,
        limit: int,
    ) -> list[RetrievedDocument]:
        """
        Return up to `limit` documents ordered by descending relevance.
        """
        ...


@runtime_checkable
class AnswerGenerator(Protocol):
    """
    Contract for components that generate answers from retrieved context.
    """

    async def generate(
        self,
        question: str,
        context: Sequence[KnowledgeDocument],
    ) -> str:
        """
        Generate an answer grounded in the supplied knowledge documents.
        """
        ...