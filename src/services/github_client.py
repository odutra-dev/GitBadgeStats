"""GitHub GraphQL API Client.

Adheres to Single Responsibility Principle (SRP): strictly handles authentication,
GraphQL query transport, and HTTP error responses with the GitHub API.
"""

import time
from os import getenv
from typing import Optional

import httpx
from fastapi import HTTPException

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
DEFAULT_TIMEOUT = httpx.Timeout(12.0, connect=5.0)
RATE_LIMIT_DETAIL = "GitHub API rate limit exceeded. Please try again later."
MAX_UPSTREAM_MESSAGE_LENGTH = 200


class GitHubGraphQLClient:
    """Client for executing GraphQL queries against GitHub API."""

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ):
        self._token = token or getenv("GITHUB_TOKEN")
        self._timeout = timeout

    @property
    def headers(self) -> dict:
        """Retrieve and validate authorization headers."""
        token = self._token or getenv("GITHUB_TOKEN")

        if not token or not token.strip():
            raise HTTPException(
                status_code=500,
                detail=(
                    "GitHub token not configured. "
                    "Set GITHUB_TOKEN in your .env file"
                ),
            )

        return {"Authorization": f"bearer {token.strip()}"}

    @staticmethod
    def get_stats_graphql_query() -> str:
        """GraphQL query for general user profile statistics."""
        return """
        query userInfo($login: String!, $after: String) {
          user(login: $login) {
            name
            login
            repositories(
              first: 100,
              after: $after,
              ownerAffiliations: OWNER,
              isFork: false
            ) {
              nodes {
                stargazers {
                  totalCount
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
            contributionsCollection {
              totalCommitContributions
            }
            pullRequests {
              totalCount
            }
            issues {
              totalCount
            }
            repositoriesContributedTo(
              first: 1,
              contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]
            ) {
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
        query userTopLanguages($login: String!, $after: String) {
          user(login: $login) {
            name
            login
            repositories(
              first: 100,
              after: $after,
              ownerAffiliations: OWNER,
              isFork: false,
              orderBy: {field: STARGAZERS, direction: DESC}
            ) {
              nodes {
                name
                isFork
                languages(
                  first: 10,
                  orderBy: {field: SIZE, direction: DESC}
                ) {
                  edges {
                    size
                    node {
                      name
                      color
                    }
                  }
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

    @staticmethod
    def get_profile_graphql_query() -> str:
        """GraphQL query for profile summary: followers, repositories, stars and creation date."""
        return """
        query userProfile($login: String!, $after: String) {
          user(login: $login) {
            name
            login
            createdAt
            followers {
              totalCount
            }
            following {
              totalCount
            }
            repositories(
              first: 100,
              after: $after,
              ownerAffiliations: OWNER,
              isFork: false
            ) {
              totalCount
              nodes {
                stargazers {
                  totalCount
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

    @staticmethod
    def _upstream_message(response: httpx.Response) -> str:
        """Best-effort extraction of GitHub's own error message from a response body."""
        try:
            body = response.json()
        except ValueError:
            return ""

        if isinstance(body, dict):
            return str(body.get("message") or "")[:MAX_UPSTREAM_MESSAGE_LENGTH]

        return ""

    @staticmethod
    def _retry_after_seconds(headers) -> Optional[int]:
        """Seconds until the request can be retried, from Retry-After or X-RateLimit-Reset."""
        retry_after = (headers.get("retry-after") or "").strip()

        if retry_after.isdigit():
            return int(retry_after)

        reset = (headers.get("x-ratelimit-reset") or "").strip()

        if reset.isdigit():
            return max(int(reset) - int(time.time()), 0)

        return None

    @classmethod
    def _rate_limit_error(cls, headers) -> HTTPException:
        """Build a 429 error, exposing Retry-After when GitHub told us how long to wait."""
        retry_after = cls._retry_after_seconds(headers)
        response_headers = (
            {"Retry-After": str(retry_after)}
            if retry_after is not None
            else None
        )

        return HTTPException(
            status_code=429,
            detail=RATE_LIMIT_DETAIL,
            headers=response_headers,
        )

    @classmethod
    def _raise_for_http_error(cls, response: httpx.Response) -> None:
        """Translate non-200 GitHub responses into precise HTTP errors."""
        status = response.status_code

        if status == 200:
            return

        if status == 401:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired GitHub token",
            )

        if status in (403, 429):
            message = cls._upstream_message(response)
            headers = response.headers

            is_rate_limited = (
                status == 429
                or "retry-after" in headers
                or headers.get("x-ratelimit-remaining") == "0"
                or "rate limit" in message.lower()
            )

            if is_rate_limited:
                raise cls._rate_limit_error(headers)

            # A 403 that is not a rate limit is a permissions problem (token scopes,
            # SSO enforcement, blocked access), not something the caller can retry.
            detail = "GitHub denied the request (HTTP 403)"

            if message:
                detail += f": {message}"

            raise HTTPException(status_code=502, detail=detail)

        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with GitHub (HTTP {status})",
        )

    @classmethod
    def _extract_user(
        cls,
        data: object,
        response: httpx.Response,
    ) -> dict:
        """Return the user node, translating GraphQL errors into precise HTTP errors."""
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=502,
                detail="Invalid response from GitHub",
            )

        raw_errors = data.get("errors") or []
        errors = [error for error in raw_errors if isinstance(error, dict)]
        user = (data.get("data") or {}).get("user")

        if not errors and user:
            return user

        types = {
            str(error.get("type") or "").upper()
            for error in errors
        }
        messages = [
            str(error.get("message") or "")
            for error in errors
        ]

        if "RATE_LIMITED" in types or any(
            "rate limit" in message.lower()
            for message in messages
        ):
            raise cls._rate_limit_error(response.headers)

        # GitHub reports an unknown login as type NOT_FOUND; the message check is a
        # fallback for responses that omit the type.
        if "NOT_FOUND" in types or any(
            message.startswith("Could not resolve to a User")
            for message in messages
        ):
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        if errors:
            first = (
                messages[0][:MAX_UPSTREAM_MESSAGE_LENGTH]
                if messages and messages[0]
                else "unknown error"
            )

            if types & {"FORBIDDEN", "INSUFFICIENT_SCOPES"}:
                raise HTTPException(
                    status_code=502,
                    detail=f"GitHub denied the request: {first}",
                )

            raise HTTPException(
                status_code=502,
                detail=f"GitHub GraphQL error: {first}",
            )

        # No errors reported, but no user either.
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    async def execute_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query and translate GitHub failures into precise HTTP errors."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    GITHUB_GRAPHQL_URL,
                    json={
                        "query": query,
                        "variables": variables,
                    },
                    headers=self.headers,
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"GitHub connection error: {exc.__class__.__name__}",
                ) from exc

        self._raise_for_http_error(response)

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(
                status_code=502,
                detail="Invalid response from GitHub",
            ) from exc

        return self._extract_user(data, response)


# Default shared client instance
default_github_client = GitHubGraphQLClient()
