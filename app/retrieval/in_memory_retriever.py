import math

from app.domain.models import (
    KnowledgeDocument,
    RetrievedDocument,
)
from app.domain.protocols import Embedder


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    if len(left) != len(right):
        raise ValueError(
            "Vectors must have the same dimensions."
        )

    numerator = sum(
        left_value * right_value
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )

    left_norm = math.sqrt(
        sum(value * value for value in left)
    )

    right_norm = math.sqrt(
        sum(value * value for value in right)
    )

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


class InMemoryRetriever:
    def __init__(
        self,
        documents: list[KnowledgeDocument],
        vectors: list[list[float]],
        embedder: Embedder,
    ) -> None:
        if len(documents) != len(vectors):
            raise ValueError(
                "Each document must have one embedding vector."
            )

        self.documents = documents
        self.vectors = vectors
        self.embedder = embedder

    @classmethod
    async def create(
        cls,
        documents: list[KnowledgeDocument],
        embedder: Embedder,
    ) -> "InMemoryRetriever":
        if not documents:
            raise ValueError(
                "At least one knowledge document is required."
            )

        texts_to_embed = [
            f"{document.title}\n\n{document.content}"
            for document in documents
        ]

        vectors = await embedder.embed(texts_to_embed)

        return cls(
            documents=documents,
            vectors=vectors,
            embedder=embedder,
        )

    async def retrieve(
        self,
        query: str,
        limit: int,
    ) -> list[RetrievedDocument]:
        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError(
                "Retrieval limit must be greater than zero."
            )

        query_vectors = await self.embedder.embed(
            [normalized_query]
        )
        query_vector = query_vectors[0]

        ranked_documents = [
            RetrievedDocument(
                document=document,
                score=cosine_similarity(
                    query_vector,
                    document_vector,
                ),
            )
            for document, document_vector in zip(
                self.documents,
                self.vectors,
                strict=True,
            )
        ]

        ranked_documents.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return ranked_documents[:limit]
