from collections.abc import Sequence

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    RateLimitError,
)

from app.core.errors import ProviderUnavailableError
from app.domain.protocols import Embedder, EmbeddingBatch


class OpenAIEmbedder(Embedder):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )
        self.model = model

    async def embed(
        self,
        texts: Sequence[str],
    ) -> EmbeddingBatch:
        normalized_texts = [
            text.strip()
            for text in texts
            if text and text.strip()
        ]

        if not normalized_texts:
            raise ValueError(
                "At least one non-empty text is required."
            )

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=normalized_texts,
            )
        except (
            RateLimitError,
            APIConnectionError,
            APIStatusError,
            RuntimeError,
        ) as exc:
            raise ProviderUnavailableError() from exc

        embeddings = [
            item.embedding
            for item in response.data
        ]

        if len(embeddings) != len(normalized_texts):
            raise ValueError(
                "The embedding provider returned an unexpected "
                "number of vectors."
            )

        if not all(embeddings):
            raise ValueError(
                "The embedding provider returned an empty vector."
            )

        return embeddings
