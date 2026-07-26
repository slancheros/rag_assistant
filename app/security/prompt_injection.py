import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.models import KnowledgeDocument


@dataclass(frozen=True)
class PromptInjectionAssessment:
    detected: bool
    reason: str | None = None


QUESTION_RULES: tuple[
    tuple[str, re.Pattern[str]],
    ...,
] = (
    (
        "prompt_extraction",
        re.compile(
            r"\b(?:reveal|show|print|repeat|display|return|expose)"
            r"\b.{0,40}\b(?:system|developer|hidden|initial)"
            r"\s+(?:prompt|instructions?|message)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "unauthorized_data_access",
        re.compile(
            r"\b(?:reveal|show|print|list|give|send|expose|access"
            r"|retrieve|dump)\b.{0,50}\b(?:api[- ]?keys?"
            r"|passwords?|credentials?|secrets?|private\s+data"
            r"|other\s+(?:users?|customers?)(?:'|’)?\s+"
            r"(?:data|files?|accounts?))\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "direct_prompt_injection",
        re.compile(
            r"\b(?:ignore|disregard|forget|override|bypass)\b"
            r".{0,50}\b(?:previous|prior|system|developer|original"
            r"|safety|security)\b.{0,30}\b(?:instructions?|rules?"
            r"|prompt|controls?)\b"
            r"|\b(?:act|behave|respond)\s+as\s+(?:the\s+)?"
            r"(?:system|developer|administrator|root)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
)

CONTEXT_RULES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:ignore|disregard|forget|override|bypass)\b"
        r".{0,50}\b(?:previous|prior|system|developer|original"
        r"|safety|security)\b.{0,30}\b(?:instructions?|rules?"
        r"|prompt|controls?)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:assistant|model|chatbot|llm)\s*[:,]\s*"
        r"(?:reveal|send|return|expose|ignore|follow|execute)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:system|developer)\s+(?:message|instruction)"
        r"\s*:",
        re.IGNORECASE,
    ),
)


def assess_question(
    question: str,
) -> PromptInjectionAssessment:
    for reason, pattern in QUESTION_RULES:
        if pattern.search(question):
            return PromptInjectionAssessment(
                detected=True,
                reason=reason,
            )

    return PromptInjectionAssessment(detected=False)


def assess_context(
    documents: Sequence[KnowledgeDocument],
) -> PromptInjectionAssessment:
    for document in documents:
        content = f"{document.title}\n{document.content}"
        if any(
            pattern.search(content)
            for pattern in CONTEXT_RULES
        ):
            return PromptInjectionAssessment(
                detected=True,
                reason="indirect_prompt_injection",
            )

    return PromptInjectionAssessment(detected=False)
