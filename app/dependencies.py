from dataclasses import dataclass

from app.core.config import Settings
from app.generation.openai_generator import (
    OpenAIAnswerGenerator,
)
from app.generation.openai_grounding_evaluator import (
    OpenAIGroundingEvaluator,
)
from app.ingestion.markdown_loader import (
    MarkdownKnowledgeBaseLoader,
)
from app.retrieval.in_memory_retriever import (
    InMemoryRetriever,
)
from app.retrieval.openai_embedder import (
    OpenAIEmbedder,
)
from app.services.support_assistant import SupportAssistant
from app.services.answer_cache import TTLAnswerCache


@dataclass
class Container:
    assistant: SupportAssistant


def get_provider_configuration(
    settings: Settings,
) -> tuple[str, str]:
    if settings.ai_provider == "ollama":
        return (
            settings.ollama_base_url,
            settings.ollama_api_key.get_secret_value(),
        )

    return (
        settings.openai_base_url,
        settings.openai_api_key.get_secret_value(),
    )


async def build_container(
    settings: Settings,
) -> Container:
    loader = MarkdownKnowledgeBaseLoader()

    documents = loader.load(
        settings.knowledge_base_path
    )

    base_url, api_key = get_provider_configuration(
        settings
    )

    if not api_key:
        raise ValueError(
            f"An API key is required for provider "
            f"'{settings.ai_provider}'."
        )

    embedder = OpenAIEmbedder(
        api_key=api_key,
        base_url=base_url,
        model=settings.embedding_model,
        timeout_seconds=settings.provider_timeout_seconds,
    )

    retriever = await InMemoryRetriever.create(
        documents=documents,
        embedder=embedder,
    )

    generator = OpenAIAnswerGenerator(
        api_key=api_key,
        base_url=base_url,
        model=settings.llm_model,
        timeout_seconds=settings.provider_timeout_seconds,
    )

    grounding_evaluator = OpenAIGroundingEvaluator(
        api_key=api_key,
        base_url=base_url,
        model=settings.llm_model,
        timeout_seconds=settings.provider_timeout_seconds,
    )

    assistant = SupportAssistant(
        retriever=retriever,
        generator=generator,
        grounding_evaluator=grounding_evaluator,
        relevance_threshold=settings.relevance_threshold,
        top_k=settings.top_k,
        cache=TTLAnswerCache(
            ttl_seconds=settings.cache_ttl_seconds,
            max_entries=settings.cache_max_entries,
        ),
    )

    return Container(assistant=assistant)
