"""Typed unit tests for the GitHub service facade and repository pagination."""

import asyncio
from typing import Any, TypedDict

import pytest
from fastapi import HTTPException

from src.services.cache import SimpleTTLCache
from src.services.github_client import GitHubGraphQLClient
from src.services.github_service import (
    _fetch_all_repository_pages,
    fetch_github_profile,
    fetch_github_stats,
    fetch_github_streak,
    fetch_github_top_languages,
)

JSONDict = dict[str, Any]


class QueryCall(TypedDict):
    query: str
    variables: dict[str, Any]


class ScriptedGitHubClient(GitHubGraphQLClient):
    """Fake client returning prepared responses in order for each query."""

    def __init__(self, responses: dict[str, list[JSONDict]]) -> None:
        super().__init__(token="test-token")
        self.responses = {
            key: list(pages) for key, pages in responses.items()
        }
        self.calls: list[QueryCall] = []

    async def execute_query(
        self,
        query: str,
        variables: dict,
    ) -> dict:
        """Return the next prepared response for the supplied query type."""
        self.calls.append({
            "query": query,
            "variables": dict(variables),
        })

        if "userInfo" in query:
            key = "stats"
        elif "userTopLanguages" in query:
            key = "languages"
        elif "userStreak" in query:
            key = "streak"
        elif "userProfile" in query:
            key = "profile"        
        else:
            raise AssertionError(f"Unexpected GraphQL query: {query}")

        pages = self.responses.get(key, [])

        if not pages:
            raise AssertionError(
                f"No scripted response remaining for {key}"
            )

        return pages.pop(0)


def _stats_page(
    repositories: list[JSONDict],
    *,
    has_next_page: bool = False,
    end_cursor: str | None = None,
) -> JSONDict:
    """Build a user payload page for the statistics GraphQL query."""
    return {
        "name": "Octocat",
        "login": "octocat",
        "repositories": {
            "nodes": repositories,
            "pageInfo": {
                "hasNextPage": has_next_page,
                "endCursor": end_cursor,
            },
        },
        "contributionsCollection": {
            "totalCommitContributions": 123,
        },
        "pullRequests": {"totalCount": 12},
        "issues": {"totalCount": 6},
        "repositoriesContributedTo": {"totalCount": 4},
    }


def _language_repo(
    name: str,
    language: str,
    size: int,
    color: str,
) -> JSONDict:
    """Build a repository containing one language edge."""
    return {
        "name": name,
        "isFork": False,
        "languages": {
            "edges": [
                {
                    "size": size,
                    "node": {
                        "name": language,
                        "color": color,
                    },
                }
            ]
        },
    }


def _languages_page(
    repositories: list[JSONDict],
    *,
    has_next_page: bool = False,
    end_cursor: str | None = None,
) -> JSONDict:
    """Build a user payload page for the top-languages query."""
    return {
        "name": "Octocat",
        "login": "octocat",
        "repositories": {
            "nodes": repositories,
            "pageInfo": {
                "hasNextPage": has_next_page,
                "endCursor": end_cursor,
            },
        },
    }


def test_fetch_github_stats_aggregates_all_pages_and_passes_cursor() -> None:
    """Stars are summed across pages and the cursor is passed to the next query."""
    first_page = [
        {
            "name": f"repo-{index}",
            "stargazers": {"totalCount": 1},
        }
        for index in range(100)
    ]

    client = ScriptedGitHubClient({
        "stats": [
            _stats_page(
                first_page,
                has_next_page=True,
                end_cursor="cursor-1",
            ),
            _stats_page([
                {
                    "name": "repo-100",
                    "stargazers": {"totalCount": 50},
                }
            ]),
        ]
    })

    result = asyncio.run(
        fetch_github_stats(
            "  Octocat  ",
            use_cache=False,
            client=client,
            cache_backend=SimpleTTLCache(),
        )
    )

    assert result == {
        "name": "Octocat",
        "total_commits": 123,
        "stars": 150,
        "total_prs": 12,
        "total_issues": 6,
        "contributed_to": 4,
    }

    assert len(client.calls) == 2
    assert client.calls[0]["variables"] == {
        "login": "Octocat",
        "after": None,
    }
    assert client.calls[1]["variables"] == {
        "login": "Octocat",
        "after": "cursor-1",
    }


def test_fetch_github_stats_returns_cached_result() -> None:
    """Equivalent usernames reuse the normalized stats cache key."""
    client = ScriptedGitHubClient({
        "stats": [
            _stats_page([
                {"stargazers": {"totalCount": 8}},
            ])
        ]
    })
    test_cache = SimpleTTLCache()

    first = asyncio.run(
        fetch_github_stats(
            "Octocat",
            client=client,
            cache_backend=test_cache,
        )
    )
    second = asyncio.run(
        fetch_github_stats(
            " OCTOCAT ",
            client=client,
            cache_backend=test_cache,
        )
    )

    assert first == second
    assert first["stars"] == 8
    assert len(client.calls) == 1


def test_fetch_github_top_languages_aggregates_all_pages() -> None:
    """Languages from page two participate in the aggregate and percentages."""
    client = ScriptedGitHubClient({
        "languages": [
            _languages_page(
                [
                    _language_repo(
                        "repo-python",
                        "Python",
                        100,
                        "#3572A5",
                    )
                ],
                has_next_page=True,
                end_cursor="language-cursor-1",
            ),
            _languages_page([
                _language_repo(
                    "repo-rust",
                    "Rust",
                    300,
                    "#dea584",
                )
            ]),
        ]
    })

    result = asyncio.run(
        fetch_github_top_languages(
            "octocat",
            use_cache=False,
            client=client,
            cache_backend=SimpleTTLCache(),
        )
    )

    assert result["name"] == "Octocat"
    assert result["login"] == "octocat"
    assert result["languages"] == [
        {
            "name": "Rust",
            "color": "#dea584",
            "size": 300,
            "percent": 75.0,
        },
        {
            "name": "Python",
            "color": "#3572A5",
            "size": 100,
            "percent": 25.0,
        },
    ]

    assert len(client.calls) == 2
    assert client.calls[1]["variables"]["after"] == "language-cursor-1"


def test_fetch_github_top_languages_applies_exclusions_across_pages() -> None:
    """Language and repository exclusions apply to combined paginated data."""
    client = ScriptedGitHubClient({
        "languages": [
            _languages_page(
                [
                    _language_repo(
                        "keep-python",
                        "Python",
                        100,
                        "#3572A5",
                    )
                ],
                has_next_page=True,
                end_cursor="cursor-1",
            ),
            _languages_page([
                _language_repo(
                    "exclude-repo",
                    "Rust",
                    300,
                    "#dea584",
                ),
                _language_repo(
                    "keep-rust",
                    "Rust",
                    50,
                    "#dea584",
                ),
            ]),
        ]
    })

    result = asyncio.run(
        fetch_github_top_languages(
            "octocat",
            exclude_languages="rust",
            exclude_repos="EXCLUDE-REPO",
            use_cache=False,
            client=client,
            cache_backend=SimpleTTLCache(),
        )
    )

    assert result["languages"] == [
        {
            "name": "Python",
            "color": "#3572A5",
            "size": 100,
            "percent": 100.0,
        }
    ]
    assert len(client.calls) == 2


def test_fetch_github_top_languages_returns_cached_result() -> None:
    """Repeated requests with the same filters reuse the language cache."""
    client = ScriptedGitHubClient({
        "languages": [
            _languages_page([
                _language_repo(
                    "repo-python",
                    "Python",
                    100,
                    "#3572A5",
                )
            ])
        ]
    })
    test_cache = SimpleTTLCache()

    first = asyncio.run(
        fetch_github_top_languages(
            "octocat",
            client=client,
            cache_backend=test_cache,
        )
    )
    second = asyncio.run(
        fetch_github_top_languages(
            "octocat",
            client=client,
            cache_backend=test_cache,
        )
    )

    assert first == second
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    "pages",
    [
        [
            _stats_page(
                [{"stargazers": {"totalCount": 1}}],
                has_next_page=True,
                end_cursor=None,
            )
        ],
        [
            _stats_page(
                [{"stargazers": {"totalCount": 1}}],
                has_next_page=True,
                end_cursor="same-cursor",
            ),
            _stats_page(
                [{"stargazers": {"totalCount": 1}}],
                has_next_page=True,
                end_cursor="same-cursor",
            ),
        ],
    ],
    ids=["missing-cursor", "repeated-cursor"],
)
def test_pagination_rejects_missing_or_repeated_cursors(
    pages: list[JSONDict],
) -> None:
    """Invalid cursors return 502 rather than creating an infinite loop."""
    client = ScriptedGitHubClient({"stats": pages})

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            _fetch_all_repository_pages(
                username="octocat",
                query=client.get_stats_graphql_query(),
                client=client,
            )
        )

    assert exc_info.value.status_code == 502
    assert (
        exc_info.value.detail
        == "Invalid pagination response from GitHub"
    )


def test_pagination_accepts_a_single_page_without_page_info() -> None:
    """Missing pageInfo is treated as a final page for a one-page response."""
    page: JSONDict = {
        "name": "Octocat",
        "login": "octocat",
        "repositories": {
            "nodes": [
                {"stargazers": {"totalCount": 7}},
            ],
        },
    }
    client = ScriptedGitHubClient({"stats": [page]})

    result = asyncio.run(
        _fetch_all_repository_pages(
            username="octocat",
            query=client.get_stats_graphql_query(),
            client=client,
        )
    )

    assert (
        result["repositories"]["nodes"]
        == page["repositories"]["nodes"]
    )
    assert result["repositories"]["pageInfo"] == {
        "hasNextPage": False,
        "endCursor": None,
    }
    assert len(client.calls) == 1


def test_fetch_github_streak_maps_calendar_and_uses_cache() -> None:
    """The streak service maps contribution totals and caches by its parameters."""
    client = ScriptedGitHubClient({
        "streak": [
            {
                "name": "Octocat",
                "login": "octocat",
                "contributionsCollection": {
                    "totalCommitContributions": 120,
                    "contributionCalendar": {
                        "totalContributions": 250,
                        "weeks": [
                            {
                                "contributionDays": [
                                    {
                                        "date": "2026-10-22",
                                        "contributionCount": 3,
                                        "weekday": 3,
                                    }
                                ]
                            }
                        ],
                    },
                },
            }
        ]
    })
    test_cache = SimpleTTLCache()

    first = asyncio.run(
        fetch_github_streak(
            " octocat ",
            timezone_name="UTC",
            locale="de",
            client=client,
            cache_backend=test_cache,
        )
    )
    second = asyncio.run(
        fetch_github_streak(
            "OCTOCAT",
            timezone_name="UTC",
            locale="de",
            client=client,
            cache_backend=test_cache,
        )
    )

    assert first == second
    assert first["name"] == "Octocat"
    assert first["login"] == "octocat"
    assert first["total_commits"] == 120
    assert first["total_contributions"] == 250
    assert len(first["weekly_days"]) == 7
    assert client.calls[0]["variables"] == {"login": "octocat"}
    assert len(client.calls) == 1


def _profile_page(
    repositories: list[JSONDict],
    *,
    total_count: int | None = None,
    has_next_page: bool = False,
    end_cursor: str | None = None,
) -> JSONDict:
    """Build a user payload page for the profile GraphQL query."""
    return {
        "name": "Octocat",
        "login": "octocat",
        "createdAt": "2011-01-25T18:44:36Z",
        "followers": {"totalCount": 21400},
        "following": {"totalCount": 9},
        "repositories": {
            "totalCount": len(repositories) if total_count is None else total_count,
            "nodes": repositories,
            "pageInfo": {
                "hasNextPage": has_next_page,
                "endCursor": end_cursor,
            },
        },
    }


def test_profile_query_supports_repository_pagination() -> None:
    """The query must accept the cursor used by the shared pagination helper."""
    query = GitHubGraphQLClient.get_profile_graphql_query()

    assert "userProfile" in query
    assert "$after: String" in query
    assert "pageInfo" in query
    assert "createdAt" in query


def test_fetch_github_profile_maps_fields_and_sums_stars_across_pages() -> None:
    """Stars are summed across pages while the repository total comes from GitHub."""
    first_page = [
        {"stargazers": {"totalCount": 1}}
        for _ in range(100)
    ]
    client = ScriptedGitHubClient({
        "profile": [
            _profile_page(
                first_page,
                total_count=101,
                has_next_page=True,
                end_cursor="profile-cursor-1",
            ),
            _profile_page(
                [{"stargazers": {"totalCount": 50}}],
                total_count=101,
            ),
        ]
    })

    result = asyncio.run(
        fetch_github_profile(
            "  Octocat  ",
            use_cache=False,
            client=client,
            cache_backend=SimpleTTLCache(),
        )
    )

    assert result == {
        "name": "Octocat",
        "login": "octocat",
        "created_at": "2011-01-25T18:44:36Z",
        "followers": 21400,
        "following": 9,
        "repositories": 101,
        "stars": 150,
    }
    assert len(client.calls) == 2
    assert client.calls[0]["variables"] == {"login": "Octocat", "after": None}
    assert client.calls[1]["variables"] == {
        "login": "Octocat",
        "after": "profile-cursor-1",
    }


def test_fetch_github_profile_uses_defaults_for_missing_fields() -> None:
    """A sparse payload falls back to the login and zero counts."""
    client = ScriptedGitHubClient({
        "profile": [
            {
                "name": None,
                "login": "octocat",
                "repositories": {"nodes": []},
            }
        ]
    })

    result = asyncio.run(
        fetch_github_profile(
            "octocat",
            use_cache=False,
            client=client,
            cache_backend=SimpleTTLCache(),
        )
    )

    assert result == {
        "name": "octocat",
        "login": "octocat",
        "created_at": None,
        "followers": 0,
        "following": 0,
        "repositories": 0,
        "stars": 0,
    }


def test_fetch_github_profile_returns_cached_result() -> None:
    """Equivalent usernames reuse the normalized profile cache key."""
    client = ScriptedGitHubClient({
        "profile": [_profile_page([{"stargazers": {"totalCount": 8}}])]
    })
    test_cache = SimpleTTLCache()

    first = asyncio.run(
        fetch_github_profile(
            "Octocat",
            client=client,
            cache_backend=test_cache,
        )
    )
    second = asyncio.run(
        fetch_github_profile(
            " OCTOCAT ",
            client=client,
            cache_backend=test_cache,
        )
    )

    assert first == second
    assert first["stars"] == 8
    assert len(client.calls) == 1
