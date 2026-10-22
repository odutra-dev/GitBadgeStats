"""GitHub GraphQL API Client.

Adheres to Single Responsibility Principle (SRP): strictly handles authentication,
GraphQL query transport, and HTTP error responses with the GitHub API.
"""

from os import getenv
from typing import Optional
import httpx
from fastapi import HTTPException

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
DEFAULT_TIMEOUT = httpx.Timeout(12.0, connect=5.0)


class GitHubGraphQLClient:
    """Client for executing GraphQL queries against GitHub API."""

    def __init__(self, token: Optional[str] = None, timeout: httpx.Timeout = DEFAULT_TIMEOUT):
        self._token = token or getenv("GITHUB_TOKEN")
        self._timeout = timeout

    @property
    def headers(self) -> dict:
        """Retrieve and validate authorization headers."""
        token = self._token
        if not token or not token.strip():
            raise HTTPException(
                status_code=500,
                detail="GitHub token not configured. Set GITHUB_TOKEN in your .env file",
            )
        return {"Authorization": f"bearer {token.strip()}"}

    @staticmethod
    def get_stats_graphql_query() -> str:
        """GraphQL query for general user profile statistics."""
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

    @staticmethod
    def get_streak_graphql_query() -> str:
        """GraphQL query for contribution calendar and streak data."""
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

    @staticmethod
    def get_top_languages_graphql_query() -> str:
        """GraphQL query for fetching user repositories and their language usage."""
        return """
        query userTopLanguages($login: String!) {
          user(login: $login) {
            name
            login
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
              nodes {
                name
                isFork
                languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                  edges {
                    size
                    node {
                      name
                      color
                    }
                  }
                }
              }
            }
          }
        }
        """

    async def execute_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query and handle common GitHub error status codes."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    GITHUB_GRAPHQL_URL,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
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
                status_code=502,
                detail=f"Error communicating with GitHub (HTTP {response.status_code})",
            )

        data = response.json()
        if "errors" in data or not data.get("data") or not data["data"].get("user"):
            raise HTTPException(status_code=404, detail="User not found")

        return data["data"]["user"]


# Default shared client instance
default_github_client = GitHubGraphQLClient()
