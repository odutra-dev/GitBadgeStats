"""GitHub service facade.

Coordinates GitHubGraphQLClient, CacheBackend, and StreakCalculator.
Provides backward-compatible functional interface for FastAPI routes and consumers.
"""

from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from src.services.cache import cache, CacheBackend
from src.services.github_client import GitHubGraphQLClient, default_github_client
from src.domain.streak import StreakCalculator, calculate_streak_from_days
from src.domain.languages import LanguagesCalculator, calculate_top_languages

# Helper functions
def get_headers() -> dict:
    return default_github_client.headers


get_stats_graphql_query = GitHubGraphQLClient.get_stats_graphql_query
get_streak_graphql_query = GitHubGraphQLClient.get_streak_graphql_query
get_top_languages_graphql_query = GitHubGraphQLClient.get_top_languages_graphql_query


async def fetch_github_stats(
    username: str,
    use_cache: bool = True,
    client: Optional[GitHubGraphQLClient] = None,
    cache_backend: Optional[CacheBackend] = None,
) -> dict:
    """Fetch general GitHub stats with TTL caching support."""
    clean_username = username.strip()
    cache_key = f"stats:{clean_username.lower()}"
    active_cache = cache_backend or cache

    if use_cache:
        cached = active_cache.get(cache_key)
        if cached:
            return cached

    active_client = client or default_github_client
    user_data = await active_client.execute_query(
        query=active_client.get_stats_graphql_query(),
        variables={"login": clean_username},
    )

    result = {
        "name": user_data["name"] or user_data["login"],
        "total_commits": user_data.get("contributionsCollection", {}).get("totalCommitContributions", 0),
        "stars": sum(repo["stargazers"]["totalCount"] for repo in user_data.get("repositories", {}).get("nodes", [])),
        "total_prs": user_data.get("pullRequests", {}).get("totalCount", 0),
        "total_issues": user_data.get("issues", {}).get("totalCount", 0),
        "contributed_to": user_data.get("repositoriesContributedTo", {}).get("totalCount", 0),
    }

    if use_cache:
        active_cache.set(cache_key, result)

    return result


async def fetch_github_streak(
    username: str,
    timezone_name: str = "UTC",
    locale: str = "en",
    use_cache: bool = True,
    client: Optional[GitHubGraphQLClient] = None,
    cache_backend: Optional[CacheBackend] = None,
) -> dict:
    """Fetch user contribution calendar and calculate Duolingo-style streak."""
    clean_username = username.strip()
    cache_key = f"streak:{clean_username.lower()}:{timezone_name}:{locale}"
    active_cache = cache_backend or cache

    if use_cache:
        cached = active_cache.get(cache_key)
        if cached:
            return cached

    active_client = client or default_github_client
    user_data = await active_client.execute_query(
        query=active_client.get_streak_graphql_query(),
        variables={"login": clean_username},
    )

    contributions = user_data.get("contributionsCollection", {})
    calendar = contributions.get("contributionCalendar", {})

    all_days = []
    for week in calendar.get("weeks", []):
        for day in week.get("contributionDays", []):
            all_days.append({
                "date": day["date"],
                "count": day.get("contributionCount", 0),
                "weekday": day.get("weekday", 0),
            })

    # Timezone resolution
    try:
        user_tz = ZoneInfo(timezone_name) if timezone_name else timezone.utc
    except Exception:
        user_tz = timezone.utc

    user_today = datetime.now(user_tz).date()
    streak_info = StreakCalculator.calculate(all_days, user_date=user_today, locale=locale)

    result = {
        "name": user_data["name"] or user_data["login"],
        "login": user_data["login"],
        "total_commits": contributions.get("totalCommitContributions", 0),
        "total_contributions": calendar.get("totalContributions", 0),
        **streak_info,
    }

    if use_cache:
        active_cache.set(cache_key, result)

    return result


async def fetch_github_top_languages(
    username: str,
    exclude_languages: Optional[str] = None,
    exclude_repos: Optional[str] = None,
    top_n: int = 5,
    use_cache: bool = True,
    client: Optional[GitHubGraphQLClient] = None,
    cache_backend: Optional[CacheBackend] = None,
) -> dict:
    """Fetch user repositories and compute top 5 languages by code size."""
    clean_username = username.strip()

    excluded_langs_set = {
        lang.strip().lower() for lang in exclude_languages.split(",") if lang.strip()
    } if exclude_languages else set()

    excluded_repos_set = {
        repo.strip().lower() for repo in exclude_repos.split(",") if repo.strip()
    } if exclude_repos else set()

    clean_langs_key = ",".join(sorted(excluded_langs_set))
    clean_repos_key = ",".join(sorted(excluded_repos_set))
    cache_key = f"langs:{clean_username.lower()}:{clean_langs_key}:{clean_repos_key}:{top_n}"
    active_cache = cache_backend or cache

    if use_cache:
        cached = active_cache.get(cache_key)
        if cached:
            return cached

    active_client = client or default_github_client
    user_data = await active_client.execute_query(
        query=active_client.get_top_languages_graphql_query(),
        variables={"login": clean_username},
    )

    repo_nodes = user_data.get("repositories", {}).get("nodes", [])
    top_languages = LanguagesCalculator.calculate_top_languages(
        repo_nodes=repo_nodes,
        exclude_languages=excluded_langs_set,
        exclude_repos=excluded_repos_set,
        top_n=top_n,
    )

    result = {
        "name": user_data["name"] or user_data["login"],
        "login": user_data["login"],
        "languages": top_languages,
    }

    if use_cache:
        active_cache.set(cache_key, result)

    return result
