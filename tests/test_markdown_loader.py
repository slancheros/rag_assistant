from pathlib import Path

import pytest

from app.ingestion.markdown_loader import (
    MarkdownKnowledgeBaseLoader,
)


def test_load_parses_multiple_snippets(
    tmp_path: Path,
) -> None:
    knowledge_base = tmp_path / "knowledge_base.md"

    knowledge_base.write_text(
        """
# Support Knowledge Base

**Snippet 1 — Password Reset**
Use the Forgot password option.

**Snippet 2 — Storage Limits**
Free accounts include 5GB.
""".strip(),
        encoding="utf-8",
    )

    loader = MarkdownKnowledgeBaseLoader()

    documents = loader.load(knowledge_base)

    assert len(documents) == 2

    assert documents[0].id == "snippet-1"
    assert documents[0].title == "Password Reset"
    assert documents[0].content == (
        "Use the Forgot password option."
    )
    assert documents[0].source == "knowledge_base.md"

    assert documents[1].id == "snippet-2"
    assert documents[1].title == "Storage Limits"


def test_load_supports_hyphen_separator(
    tmp_path: Path,
) -> None:
    knowledge_base = tmp_path / "knowledge_base.md"

    knowledge_base.write_text(
        """
**Snippet 1 - Password Reset**
Use the Forgot password option.
""".strip(),
        encoding="utf-8",
    )

    documents = MarkdownKnowledgeBaseLoader().load(
        knowledge_base
    )

    assert len(documents) == 1
    assert documents[0].title == "Password Reset"


def test_load_strips_surrounding_whitespace(
    tmp_path: Path,
) -> None:
    knowledge_base = tmp_path / "knowledge_base.md"

    knowledge_base.write_text(
        """
**Snippet 1 — Password Reset**

    Use the Forgot password option.

""".strip(),
        encoding="utf-8",
    )

    documents = MarkdownKnowledgeBaseLoader().load(
        knowledge_base
    )

    assert documents[0].content == (
        "Use the Forgot password option."
    )


def test_load_raises_when_file_does_not_exist(
    tmp_path: Path,
) -> None:
    missing_file = tmp_path / "missing.md"

    loader = MarkdownKnowledgeBaseLoader()

    with pytest.raises(
        FileNotFoundError,
        match="Knowledge base not found",
    ):
        loader.load(missing_file)


def test_load_raises_when_no_valid_snippets_exist(
    tmp_path: Path,
) -> None:
    knowledge_base = tmp_path / "knowledge_base.md"

    knowledge_base.write_text(
        "# Empty knowledge base",
        encoding="utf-8",
    )

    loader = MarkdownKnowledgeBaseLoader()

    with pytest.raises(
        ValueError,
        match="No valid knowledge-base snippets",
    ):
        loader.load(knowledge_base)


def test_load_ignores_invalid_empty_snippet(
    tmp_path: Path,
) -> None:
    knowledge_base = tmp_path / "knowledge_base.md"

    knowledge_base.write_text(
        """
**Snippet 1 — Password Reset**

**Snippet 2 — Storage Limits**
Free accounts include 5GB.
""".strip(),
        encoding="utf-8",
    )

    documents = MarkdownKnowledgeBaseLoader().load(
        knowledge_base
    )

    assert len(documents) == 1
    assert documents[0].id == "snippet-2"