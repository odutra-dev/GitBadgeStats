"""Unit tests for GitHubGraphQLClient module."""

import asyncio
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException

from src.services.github_client import GitHubGraphQLClient


def test_client_missing_token_raises_http_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing GITHUB_TOKEN environment variable raises 500."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    client = GitHubGraphQLClient(token="")

    with pytest.raises(HTTPException) as exc_info:
        _ = client.headers

    assert exc_info.value.status_code == 500
    assert "token not configured" in exc_info.value.detail.lower()


def test_client_valid_token_headers() -> None:
    """Verify authorization header formatting."""
    client = GitHubGraphQLClient(token="ghp_sampletoken123")

    assert client.headers == {
        "Authorization": "bearer ghp_sampletoken123"
    }


# --- GraphQL query definitions --------------------------------------------------


def test_stats_query_supports_repository_pagination() -> None:
    """Verify the statistics query supports cursor-based pagination."""
    query = GitHubGraphQLClient.get_stats_graphql_query()

    assert "query userInfo($login: String!, $after: String)" in query
    assert "repositories(" in query
    assert "first: 100" in query
    assert "after: $after" in query
    assert "ownerAffiliations: OWNER" in query
    assert "isFork: false" in query

    assert "pageInfo" in query
    assert "hasNextPage" in query
    assert "endCursor" in query

    assert "stargazers" in query
    assert "totalCount" in query
    assert "contributionsCollection" in query
    assert "pullRequests" in query
    assert "issues" in query


def test_streak_query_contains_expected_fields() -> None:
    """Verify the streak query retrieves the contribution calendar."""
    query = GitHubGraphQLClient.get_streak_graphql_query()

    assert "query userStreak($login: String!)" in query
    assert "contributionCalendar" in query
    assert "contributionDays" in query
    assert "contributionCount" in query
    assert "totalCommitContributions" in query


def test_top_languages_query_supports_repository_pagination() -> None:
    """Verify the languages query supports cursor-based pagination."""
    query = GitHubGraphQLClient.get_top_languages_graphql_query()

    assert "query userTopLanguages($login: String!, $after: String)" in query
    assert "repositories(" in query
    assert "first: 100" in query
    assert "after: $after" in query
    assert "ownerAffiliations: OWNER" in query
    assert "isFork: false" in query

    assert "pageInfo" in query
    assert "hasNextPage" in query
    assert "endCursor" in query

    assert "orderBy: {field: STARGAZERS, direction: DESC}" in query
    assert "languages(" in query
    assert "orderBy: {field: SIZE, direction: DESC}" in query
    assert "edges" in query
    assert "color" in query


# --- Error handling -------------------------------------------------------------


def _execute(response: httpx.Response) -> dict:
    """Run execute_query against a canned GitHub response."""
    client = GitHubGraphQLClient(token="ghp_sampletoken123")

    with patch("httpx.AsyncClient.post", return_value=response):
        return asyncio.run(
            client.execute_query(
                "query",
                {"login": "octocat"},
            )
        )


def _error_from(response: httpx.Response) -> HTTPException:
    """Execute a request and return its expected HTTP exception."""
    with pytest.raises(HTTPException) as exc_info:
        _execute(response)

    return exc_info.value


def test_execute_query_returns_user_node() -> None:
    """Verify successful GraphQL responses return the user node."""
    response = httpx.Response(
        200,
        json={"data": {"user": {"login": "octocat"}}},
    )

    assert _execute(response) == {"login": "octocat"}


def test_http_401_is_invalid_token() -> None:
    """HTTP 401 indicates an invalid or expired GitHub token."""
    error = _error_from(
        httpx.Response(401, json={"message": "Bad credentials"})
    )

    assert error.status_code == 401


def test_http_403_with_exhausted_quota_is_rate_limit_with_retry_after() -> None:
    """An exhausted primary rate limit returns 429 and Retry-After."""
    response = httpx.Response(
        403,
        json={"message": "API rate limit exceeded"},
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1060",
        },
    )

    with patch("src.services.github_client.time.time", return_value=1000):
        error = _error_from(response)

    assert error.status_code == 429
    assert error.headers == {"Retry-After": "60"}


def test_http_403_secondary_rate_limit_uses_retry_after_header() -> None:
    """A secondary rate limit preserves GitHub's Retry-After header."""
    response = httpx.Response(
        403,
        json={"message": "You have exceeded a secondary rate limit."},
        headers={"Retry-After": "30"},
    )

    error = _error_from(response)

    assert error.status_code == 429
    assert error.headers == {"Retry-After": "30"}


def test_http_403_rate_limit_message_without_headers_is_rate_limit() -> None:
    """Rate-limit messages are recognized even without rate-limit headers."""
    response = httpx.Response(
        403,
        json={"message": "API rate limit exceeded for user ID 1."},
    )

    error = _error_from(response)

    assert error.status_code == 429
    assert error.headers is None


def test_http_429_is_rate_limit() -> None:
    """HTTP 429 is translated into a rate-limit exception."""
    error = _error_from(httpx.Response(429, json={}))

    assert error.status_code == 429


def test_rate_limit_reset_in_the_past_clamps_retry_after_to_zero() -> None:
    """Retry-After never becomes negative if the reset time has passed."""
    response = httpx.Response(
        403,
        json={"message": "API rate limit exceeded"},
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "900",
        },
    )

    with patch("src.services.github_client.time.time", return_value=1000):
        error = _error_from(response)

    assert error.status_code == 429
    assert error.headers == {"Retry-After": "0"}


def test_http_403_permission_error_is_not_reported_as_rate_limit() -> None:
    """A permissions-related 403 is distinguished from a rate limit."""
    response = httpx.Response(
        403,
        json={
            "message": (
                "Resource not accessible by personal access token"
            )
        },
        headers={"X-RateLimit-Remaining": "4999"},
    )

    error = _error_from(response)

    assert error.status_code == 502
    assert "Resource not accessible by personal access token" in error.detail


def test_http_403_with_non_json_body_is_not_reported_as_rate_limit() -> None:
    """A non-JSON 403 body is treated as a gateway error."""
    response = httpx.Response(
        403,
        text="<html>Forbidden</html>",
    )

    error = _error_from(response)

    assert error.status_code == 502
    assert "403" in error.detail


def test_http_500_is_bad_gateway() -> None:
    """Upstream server errors are translated into HTTP 502."""
    error = _error_from(httpx.Response(503, json={}))

    assert error.status_code == 502
    assert "503" in error.detail


def test_graphql_not_found_error_is_404() -> None:
    """A GraphQL NOT_FOUND error becomes HTTP 404."""
    response = httpx.Response(
        200,
        json={
            "data": {"user": None},
            "errors": [
                {
                    "type": "NOT_FOUND",
                    "path": ["user"],
                    "message": (
                        "Could not resolve to a User "
                        "with the login of 'ghost'."
                    ),
                }
            ],
        },
    )

    error = _error_from(response)

    assert error.status_code == 404
    assert error.detail == "User not found"


def test_graphql_not_found_without_error_type_is_still_404() -> None:
    """The unknown-user message is sufficient when the error type is absent."""
    response = httpx.Response(
        200,
        json={
            "data": {"user": None},
            "errors": [
                {
                    "message": (
                        "Could not resolve to a User "
                        "with the login of 'ghost'."
                    )
                }
            ],
        },
    )

    assert _error_from(response).status_code == 404


def test_graphql_null_user_without_errors_is_404() -> None:
    """A null user without GraphQL errors is translated into HTTP 404."""
    error = _error_from(
        httpx.Response(200, json={"data": {"user": None}})
    )

    assert error.status_code == 404


def test_graphql_rate_limited_error_is_429_with_retry_after() -> None:
    """GraphQL rate-limit errors preserve the calculated retry delay."""
    response = httpx.Response(
        200,
        json={
            "data": None,
            "errors": [
                {
                    "type": "RATE_LIMITED",
                    "message": "API rate limit exceeded for user ID 1.",
                }
            ],
        },
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1120",
        },
    )

    with patch("src.services.github_client.time.time", return_value=1000):
        error = _error_from(response)

    assert error.status_code == 429
    assert error.headers == {"Retry-After": "120"}


def test_graphql_insufficient_scopes_is_not_reported_as_user_not_found() -> None:
    """Insufficient token scopes are treated as a gateway error, not 404."""
    response = httpx.Response(
        200,
        json={
            "data": {"user": None},
            "errors": [
                {
                    "type": "INSUFFICIENT_SCOPES",
                    "message": (
                        "Your token has not been granted "
                        "the required scopes."
                    ),
                }
            ],
        },
    )

    error = _error_from(response)

    assert error.status_code == 502
    assert "required scopes" in error.detail


def test_graphql_unknown_error_is_not_reported_as_user_not_found() -> None:
    """Unknown GraphQL errors are translated into HTTP 502."""
    response = httpx.Response(
        200,
        json={
            "data": {"user": None},
            "errors": [
                {
                    "message": (
                        "Something went wrong while executing your query."
                    )
                }
            ],
        },
    )

    error = _error_from(response)

    assert error.status_code == 502
    assert error.detail.startswith("GitHub GraphQL error:")


def test_non_json_success_body_is_bad_gateway() -> None:
    """A successful HTTP response with an invalid JSON body becomes HTTP 502."""
    error = _error_from(httpx.Response(200, text="not json"))

    assert error.status_code == 502
