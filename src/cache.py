"""Caching interfaces and implementations.

Adheres to Interface Segregation Principle (ISP) and Dependency Inversion (DIP).
"""

import time
from typing import Any, Optional, Protocol


class CacheBackend(Protocol):
    """Abstract cache backend protocol for Dependency Inversion."""

    def get(self, key: str) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...

    def clear(self) -> None:
        ...


class SimpleTTLCache:
    """In-memory cache with Time-To-Live (TTL) expiration."""

    def __init__(self, default_ttl_seconds: int = 600):
        self.default_ttl = default_ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        expire_at, value = self._cache[key]
        if time.time() > expire_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = (time.time() + ttl, value)

    def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        now = time.time()
        return sum(1 for exp, _ in self._cache.values() if exp > now)


# Global default cache instance with 10-minute TTL
cache: CacheBackend = SimpleTTLCache(default_ttl_seconds=600)
