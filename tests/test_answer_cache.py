import asyncio

import pytest

from app.domain.models import SupportAnswer
from app.services.answer_cache import TTLAnswerCache


@pytest.mark.asyncio
async def test_cache_entry_expires_after_ttl() -> None:
    cache = TTLAnswerCache(
        ttl_seconds=0.01,
        max_entries=2,
    )
    answer = SupportAnswer(
        answer="Cached answer",
        grounded=True,
        sources=[],
    )

    await cache.set("key", answer)
    assert await cache.get("key") is not None

    await asyncio.sleep(0.02)

    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_cache_evicts_least_recently_used_entry() -> None:
    cache = TTLAnswerCache(
        ttl_seconds=300,
        max_entries=2,
    )
    answer = SupportAnswer(
        answer="Cached answer",
        grounded=True,
        sources=[],
    )

    await cache.set("first", answer)
    await cache.set("second", answer)
    await cache.get("first")
    await cache.set("third", answer)

    assert await cache.get("first") is not None
    assert await cache.get("second") is None
    assert await cache.get("third") is not None
