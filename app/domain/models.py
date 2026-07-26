from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeDocument:
    id: str
    title: str
    content: str
    source: str


@dataclass(frozen=True)
class RetrievedDocument:
    document: KnowledgeDocument
    score: float


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    source: str
    score: float


@dataclass(frozen=True)
class SecurityMetadata:
    prompt_injection_detected: bool = False
    blocked: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class SupportAnswer:
    answer: str
    grounded: bool
    sources: list[Source]
    security: SecurityMetadata = field(
        default_factory=SecurityMetadata
    )
