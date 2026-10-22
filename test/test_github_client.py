"""Unit tests for GitHubGraphQLClient module."""

import pytest
from fastapi import HTTPException
from src.services.github_client import GitHubGraphQLClient


def test_client_missing_token_raises_http_500(monkeypatch):
    """Verify missing GITHUB_TOKEN environment variable raises 500."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    client = GitHubGraphQLClient(token="")
    with pytest.raises(HTTPException) as exc_info:
        _ = client.headers
    assert exc_info.value.status_code == 500
    assert "token not configured" in exc_info.value.detail.lower()


def test_client_valid_token_headers():
    """Verify authorization header formatting."""
    client = GitHubGraphQLClient(token="ghp_sampletoken123")
    assert client.headers == {"Authorization": "bearer ghp_sampletoken123"}


def test_queries_contain_expected_fields():
    """Verify GraphQL queries define required nodes."""
    stats_query = GitHubGraphQLClient.get_stats_graphql_query()
    assert "repositories" in stats_query
    assert "contributionsCollection" in stats_query

    streak_query = GitHubGraphQLClient.get_streak_graphql_query()
    assert "contributionCalendar" in streak_query
    assert "contributionDays" in streak_query
