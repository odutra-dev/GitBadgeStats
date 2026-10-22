"""Unit tests for cache module adhering to TDD."""

import time
from src.services.cache import SimpleTTLCache, CacheBackend


def test_cache_implements_protocol():
    """Verify SimpleTTLCache conforms to CacheBackend protocol."""
    cache: CacheBackend = SimpleTTLCache()
    assert hasattr(cache, "get")
    assert hasattr(cache, "set")
    assert hasattr(cache, "delete")
    assert hasattr(cache, "clear")


def test_cache_set_and_get():
    """Verify items can be stored and retrieved."""
    cache = SimpleTTLCache(default_ttl_seconds=10)
    cache.set("user:test", {"name": "Test User"})
    val = cache.get("user:test")
    assert val == {"name": "Test User"}


def test_cache_miss_returns_none():
    """Verify non-existent key returns None."""
    cache = SimpleTTLCache()
    assert cache.get("nonexistent") is None


def test_cache_ttl_expiration():
    """Verify expired items return None and are purged."""
    cache = SimpleTTLCache(default_ttl_seconds=1)
    cache.set("ephemeral", "value", ttl_seconds=0.01)
    time.sleep(0.02)
    assert cache.get("ephemeral") is None


def test_cache_delete_and_clear():
    """Verify explicit key deletion and cache clearing."""
    cache = SimpleTTLCache()
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    assert len(cache) == 2

    cache.delete("k1")
    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"

    cache.clear()
    assert len(cache) == 0
    assert cache.get("k2") is None
