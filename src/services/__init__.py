"""Application services, API clients, and caching."""

from src.services.cache import cache, CacheBackend, SimpleTTLCache
from src.services.github_client import GitHubGraphQLClient, default_github_client
from src.services.github_service import (
    fetch_github_stats,
    fetch_github_streak,
    fetch_github_top_languages,
)

__all__ = [
    "cache",
    "CacheBackend",
    "SimpleTTLCache",
    "GitHubGraphQLClient",
    "default_github_client",
    "fetch_github_stats",
    "fetch_github_streak",
    "fetch_github_top_languages",
]
