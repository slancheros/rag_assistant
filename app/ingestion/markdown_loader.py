import re
from pathlib import Path

from app.domain.models import KnowledgeDocument


SNIPPET_PATTERN = re.compile(
    r"^\*\*Snippet\s+(?P<number>\d+)\s+[—-]\s+"
    r"(?P<title>.*?)\*\*[^\S\r\n]*(?:\r?\n|\Z)"
    r"(?P<content>.*?)(?=^\*\*Snippet\s+\d+\s+[—-]|\Z)",
    flags=re.DOTALL | re.MULTILINE,
)


class MarkdownKnowledgeBaseLoader:
    def load(self, path: Path) -> list[KnowledgeDocument]:
        if not path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {path}"
            )

        raw_text = path.read_text(encoding="utf-8")

        documents: list[KnowledgeDocument] = []

        for match in SNIPPET_PATTERN.finditer(raw_text):
            number = match.group("number")
            title = match.group("title").strip()
            content = match.group("content").strip()

            if not title or not content:
                continue

            documents.append(
                KnowledgeDocument(
                    id=f"snippet-{number}",
                    title=title,
                    content=content,
                    source=path.name,
                )
            )

        if not documents:
            raise ValueError(
                "No valid knowledge-base snippets were found."
            )

        return documents
