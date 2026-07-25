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
        self.documents = documents
        self.vectors = vectors
        self.embedder = embedder

    @classmethod
    async def create(
        cls,
        documents: list[KnowledgeDocument],
        embedder: Embedder,
    ) -> "InMemoryRetriever":
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
        query_vectors = await self.embedder.embed([query])
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