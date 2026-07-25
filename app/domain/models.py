from dataclasses import dataclass


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
class SupportAnswer:
    answer: str
    grounded: bool
    sources: list[Source]