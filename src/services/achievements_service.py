"""GitHub Achievements service layer.

Adheres to Single Responsibility Principle (SRP): coordinates public profile scraping,
optional GraphQL metrics, in-memory caching, and error handling for user achievements.
"""

import logging
from dataclasses import asdict
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from src.domain.achievements import (
    build_user_achievements,
    parse_profile_achievements,
)
from src.services.cache import CacheBackend, cache
from src.services.github_client import GitHubGraphQLClient, default_github_client

logger = logging.getLogger("gitbadgestats")

DEFAULT_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def _fetch_profile_html(
    username: str,
    http_client: Optional[httpx.AsyncClient] = None,
    timeout: float = 8.0,
) -> str:
    """Fetch GitHub profile HTML (achievements tab or main profile)."""
    urls = [
        f"https://github.com/{username}?tab=achievements",
        f"https://github.com/{username}",
    ]

    close_client = False
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=timeout)
        close_client = True

    try:
        for url in urls:
            try:
                response = await http_client.get(
                    url,
                    headers=DEFAULT_SCRAPE_HEADERS,
                    follow_redirects=True,
                )
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"User '{username}' not found on GitHub",
                    )
                if response.status_code == 200 and "Achievement" in response.text:
                    return response.text
                if response.status_code == 200 and not url.endswith("?tab=achievements"):
                    return response.text
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(
                    "Failed to fetch profile URL %s for achievements: %s",
                    url,
                    e,
                )
        return ""
    finally:
        if close_client:
            await http_client.aclose()


async def fetch_github_achievements(
    username: str,
    use_cache: bool = True,
    client: Optional[GitHubGraphQLClient] = None,
    cache_backend: Optional[CacheBackend] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Fetch user achievements via hybrid profile scraping and optional GraphQL metrics."""
    clean_username = username.strip()
    if not clean_username:
        raise HTTPException(status_code=400, detail="Username is required")

    cache_key = f"achievements:{clean_username.lower()}"
    active_cache = cache_backend or cache

    if use_cache:
        cached = active_cache.get(cache_key)
        if cached is not None:
            return cached

    # 1. Scrape public profile for official badges and tiers
    html = await _fetch_profile_html(clean_username, http_client=http_client)
    official_badges = parse_profile_achievements(html)

    # 2. Query GraphQL API for profile name and star metric (if client/token available)
    display_name = clean_username
    metric_counts: dict[str, int] = {}

    active_graphql = client or default_github_client
    try:
        user_data = await active_graphql.execute_query(
            query="""
            query userInfo($login: String!) {
              user(login: $login) {
                name
                login
                repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
                  nodes {
                    stargazers {
                      totalCount
                    }
                  }
                }
              }
            }
            """,
            variables={"login": clean_username},
        )
        if user_data:
            display_name = user_data.get("name") or clean_username
            repos = (user_data.get("repositories") or {}).get("nodes") or []
            total_stars = sum(
                (r.get("stargazers") or {}).get("totalCount", 0) for r in repos
            )
            metric_counts["starstruck"] = total_stars
    except Exception as e:
        logger.debug(
            "GraphQL enrichment failed for %s (falling back to scraped profile): %s",
            clean_username,
            e,
        )

    # 3. Calculate achievement progress and tier snapshots
    achievements = build_user_achievements(
        official_badges=official_badges,
        metric_counts=metric_counts,
    )

    unlocked_count = sum(1 for a in achievements if a.unlocked)

    result: dict[str, Any] = {
        "username": clean_username,
        "name": display_name,
        "achievements": [asdict(a) for a in achievements],
        "total_unlocked": unlocked_count,
        "total_possible": len(achievements),
    }

    if use_cache:
        active_cache.set(cache_key, result)

    return result
