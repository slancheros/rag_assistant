import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import monotonic

from app.domain.models import SupportAnswer


@dataclass(frozen=True)
class CacheEntry:
    answer: SupportAnswer
    created_at: datetime
    expires_at: datetime
    expires_monotonic: float


class TTLAnswerCache:
    def __init__(
        self,
        ttl_seconds: float,
        max_entries: int,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: OrderedDict[str, CacheEntry] = (
            OrderedDict()
        )
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> CacheEntry | None:
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None

            if monotonic() >= entry.expires_monotonic:
                del self._entries[key]
                return None

            self._entries.move_to_end(key)
            return entry

    async def set(
        self,
        key: str,
        answer: SupportAnswer,
    ) -> CacheEntry:
        async with self._lock:
            created_at = datetime.now(timezone.utc)
            entry = CacheEntry(
                answer=answer,
                created_at=created_at,
                expires_at=created_at + timedelta(
                    seconds=self.ttl_seconds
                ),
                expires_monotonic=(
                    monotonic() + self.ttl_seconds
                ),
            )
            self._entries[key] = entry
            self._entries.move_to_end(key)

            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

            return entry

    async def invalidate(self) -> int:
        async with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count
