"""Sample async cache module for the reviewer/critic Quality Engine fixture.

This file is intentionally written with 4 known issues that map to
fixtures/code-async-cache.json findings. It is the artifact the reviewer
agent inspects.

DO NOT FIX the issues here — they are part of the test surface.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class AsyncCache:
    """Simple async cache that fetches from an upstream loader on miss.

    Used by request handlers that look up enrichment data per-request.
    """

    def __init__(self, loader: Callable[[str], Awaitable[Any]]):
        self._store: dict[str, Any] = {}
        self._loader = loader

    async def get(self, key: str) -> Any:
        # Hot path — return cached value if present.
        if key in self._store:
            return self._store[key]

        # Cache miss — fetch from upstream.
        value = await self._loader(key)
        self._store[key] = value
        return value

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        results = {}
        for k in keys:
            results[k] = await self.get(k)
        return results

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def size(self) -> int:
        return len(self._store)


async def example_loader(key: str) -> dict[str, Any]:
    """Stand-in upstream loader. In production this would hit an external API."""
    await asyncio.sleep(0.05)  # simulate network
    return {"key": key, "data": f"value-for-{key}"}


# Module-level singleton consumed by request handlers.
_cache: AsyncCache | None = None


def get_cache() -> AsyncCache:
    global _cache
    if _cache is None:
        _cache = AsyncCache(loader=example_loader)
    return _cache
