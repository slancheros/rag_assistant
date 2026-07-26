from dataclasses import dataclass, field
from datetime import datetime


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
class CacheMetadata:
    hit: bool = False
    status: str = "miss"
    cached_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class SupportAnswer:
    answer: str
    grounded: bool
    sources: list[Source]
    security: SecurityMetadata = field(
        default_factory=SecurityMetadata
    )
    cache: CacheMetadata = field(
        default_factory=CacheMetadata
    )
