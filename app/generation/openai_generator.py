from collections.abc import Sequence

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    RateLimitError,
)

from app.core.errors import ProviderUnavailableError
from app.domain.models import KnowledgeDocument
from app.domain.protocols import AnswerGenerator
from app.generation.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)


class OpenAIAnswerGenerator(AnswerGenerator):
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

    async def generate(
        self,
        question: str,
        context: Sequence[KnowledgeDocument],
    ) -> str:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError(
                "Question cannot be empty."
            )

        if not context:
            raise ValueError(
                "At least one context document is required."
            )

        context_blocks = [
            (
                f'<source id="{document.id}" '
                f'title="{document.title}">\n'
                f"{document.content}\n"
                "</source>"
            )
            for document in context
        ]

        prompt = build_user_prompt(
            question=normalized_question,
            context_blocks=context_blocks,
        )

        try:
            response = await self.client.responses.create(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=prompt,
                temperature=0,
            )
        except (
            RateLimitError,
            APIConnectionError,
            APIStatusError,
            RuntimeError,
        ) as exc:
            raise ProviderUnavailableError() from exc

        answer = response.output_text.strip()

        if not answer:
            raise ValueError(
                "The model returned an empty answer."
            )

        return answer
