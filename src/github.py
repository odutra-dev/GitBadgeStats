# github.py
from datetime import datetime, timezone, timedelta, date
from os import getenv
from typing import Optional
from zoneinfo import ZoneInfo
import httpx
from fastapi import HTTPException

from src.cache import cache

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
DEFAULT_TIMEOUT = httpx.Timeout(12.0, connect=5.0)


def get_headers() -> dict:
    """Retrieve and validate GitHub token from environment variables."""
    token = getenv("GITHUB_TOKEN")
    if not token or not token.strip():
        raise HTTPException(
            status_code=500,
            detail="GitHub token not configured. Set GITHUB_TOKEN in your .env file",
        )
    return {"Authorization": f"bearer {token.strip()}"}


def get_stats_graphql_query() -> str:
    """GraphQL query for fetching user general statistics."""
    return """
    query userInfo($login: String!) {
      user(login: $login) {
        name
        login
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          nodes { stargazers { totalCount } }
        }
        contributionsCollection { totalCommitContributions }
        pullRequests { totalCount }
        issues { totalCount }
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) {
          totalCount
        }
      }
    }
    """


def get_streak_graphql_query() -> str:
    """GraphQL query for fetching contribution calendar and streak data."""
    return """
    query userStreak($login: String!) {
      user(login: $login) {
        name
        login
        createdAt
        contributionsCollection {
          totalCommitContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
      }
    }
    """


async def fetch_github_stats(username: str, use_cache: bool = True) -> dict:
    """Fetch general GitHub stats with TTL caching support."""
    clean_username = username.strip()
    cache_key = f"stats:{clean_username.lower()}"

    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            return cached

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(
                GITHUB_GRAPHQL_URL,
                json={"query": get_stats_graphql_query(), "variables": {"login": clean_username}},
                headers=get_headers(),
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub connection error: {exc.__class__.__name__}",
            )

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid or expired GitHub token")
    if response.status_code in (403, 429):
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Please try again later.",
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"Error communicating with GitHub (HTTP {response.status_code})"
        )

    data = response.json()
    if "errors" in data or not data.get("data") or not data["data"].get("user"):
        raise HTTPException(status_code=404, detail="User not found")

    user_data = data["data"]["user"]

    result = {
        "name": user_data["name"] or user_data["login"],
        "total_commits": user_data.get("contributionsCollection", {}).get("totalCommitContributions", 0),
        "stars": sum(repo["stargazers"]["totalCount"] for repo in user_data.get("repositories", {}).get("nodes", [])),
        "total_prs": user_data.get("pullRequests", {}).get("totalCount", 0),
        "total_issues": user_data.get("issues", {}).get("totalCount", 0),
        "contributed_to": user_data.get("repositoriesContributedTo", {}).get("totalCount", 0),
    }

    if use_cache:
        cache.set(cache_key, result)

    return result


def calculate_streak_from_days(
    all_days: list[dict],
    user_date: Optional[date] = None,
    locale: str = "en",
) -> dict:
    """Calculate current streak, longest streak, and last 7 days tracker.

    Business rules:
    - If user committed today: the flame is lit (painted) and counted.
    - If user has not committed today:
      - If user committed yesterday: the streak remains valid from yesterday, but today's flame remains unlit until a commit is made.
      - If user missed a full day (yesterday = 0 commits): streak resets to 0.
    - Consecutive commit days light up corresponding flames in the weekly tracker.
    """
    today = user_date or datetime.now(timezone.utc).date()
    day_map = {d["date"]: d["count"] for d in all_days}

    today_str = today.strftime("%Y-%m-%d")
    today_count = day_map.get(today_str, 0)
    is_active_today = today_count > 0

    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    yesterday_count = day_map.get(yesterday_str, 0)

    # 1. Current streak calculation
    current_streak = 0
    if is_active_today:
        current_streak = 1
        check_date = yesterday
        while True:
            c = day_map.get(check_date.strftime("%Y-%m-%d"), 0)
            if c > 0:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break
    else:
        # Not committed yet today; check if committed yesterday
        if yesterday_count > 0:
            current_streak = 1
            check_date = yesterday - timedelta(days=1)
            while True:
                c = day_map.get(check_date.strftime("%Y-%m-%d"), 0)
                if c > 0:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
        else:
            # 1 full missed day -> reset to 0
            current_streak = 0

    # 2. Historical longest streak calculation in period
    longest_streak = 0
    temp_streak = 0
    sorted_days = sorted(all_days, key=lambda x: x["date"])
    for d in sorted_days:
        if d["count"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    longest_streak = max(longest_streak, current_streak)

    # 3. 7-day weekly tracker (Duolingo style)
    if locale == "pt":
        weekday_labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    else:
        weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    weekly_days = []
    for i in reversed(range(7)):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        cnt = day_map.get(d_str, 0)
        weekly_days.append({
            "date": d_str,
            "day_name": weekday_labels[d.weekday()],
            "count": cnt,
            "is_active": cnt > 0,
            "is_today": (i == 0),
        })

    # 4. Contextual streak status message
    if is_active_today:
        if locale == "pt":
            message = "Ofensiva mantida! Chama acesa hoje"
        else:
            message = "Streak active! Flame is burning today"
    elif current_streak > 0:
        if locale == "pt":
            message = "Chama apagada • Faça um commit hoje!"
        else:
            message = "Flame unlit • Commit today to keep your streak!"
    else:
        if locale == "pt":
            message = "Chama apagada • Faça um commit para iniciar!"
        else:
            message = "Flame unlit • Commit to start your streak!"

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "is_active_today": is_active_today,
        "today_commits": today_count,
        "yesterday_commits": yesterday_count,
        "weekly_days": weekly_days,
        "streak_message": message,
    }


async def fetch_github_streak(
    username: str,
    timezone_name: str = "UTC",
    locale: str = "en",
    use_cache: bool = True,
) -> dict:
    """Fetch user contribution calendar and calculate Duolingo-style streak."""
    clean_username = username.strip()
    cache_key = f"streak:{clean_username.lower()}:{timezone_name}:{locale}"

    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            return cached

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            response = await client.post(
                GITHUB_GRAPHQL_URL,
                json={"query": get_streak_graphql_query(), "variables": {"login": clean_username}},
                headers=get_headers(),
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub connection error: {exc.__class__.__name__}",
            )

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid or expired GitHub token")
    if response.status_code in (403, 429):
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Please try again later.",
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502, detail=f"Error communicating with GitHub (HTTP {response.status_code})"
        )

    data = response.json()
    if "errors" in data or not data.get("data") or not data["data"].get("user"):
        raise HTTPException(status_code=404, detail="User not found")

    user_data = data["data"]["user"]
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
    streak_info = calculate_streak_from_days(all_days, user_date=user_today, locale=locale)

    result = {
        "name": user_data["name"] or user_data["login"],
        "login": user_data["login"],
        "total_commits": contributions.get("totalCommitContributions", 0),
        "total_contributions": calendar.get("totalContributions", 0),
        **streak_info,
    }

    if use_cache:
        cache.set(cache_key, result)

    return result
