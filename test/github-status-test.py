import os
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure token is present for test environment.
if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "test-token-value"

from main import app
from src.services.cache import cache

client = TestClient(app)

# Mocks for GitHub GraphQL API simulation.
MOCK_USER_STATS = {
    "data": {
        "user": {
            "name": "The Octocat",
            "login": "octocat",
            "repositories": {"nodes": [{"stargazers": {"totalCount": 85}}]},
            "contributionsCollection": {"totalCommitContributions": 150},
            "pullRequests": {"totalCount": 12},
            "issues": {"totalCount": 6},
            "repositoriesContributedTo": {"totalCount": 4},
        }
    }
}

MOCK_USER_STREAK = {
    "data": {
        "user": {
            "name": "The Octocat",
            "login": "octocat",
            "createdAt": "2011-01-25T18:44:36Z",
            "contributionsCollection": {
                "totalCommitContributions": 150,
                "contributionCalendar": {
                    "totalContributions": 200,
                    "weeks": [
                        {
                            "contributionDays": [
                                {
                                    "date": "2026-10-21",
                                    "contributionCount": 3,
                                    "weekday": 3,
                                },
                                {
                                    "date": "2026-10-22",
                                    "contributionCount": 5,
                                    "weekday": 4,
                                },
                            ]
                        }
                    ],
                },
            },
        }
    }
}

MOCK_USER_LANGUAGES = {
    "data": {
        "user": {
            "name": "The Octocat",
            "login": "octocat",
            "repositories": {
                "nodes": [
                    {
                        "name": "Hello-World",
                        "isFork": False,
                        "languages": {
                            "edges": [
                                {
                                    "size": 3000,
                                    "node": {"name": "Python", "color": "#3572A5"},
                                },
                                {
                                    "size": 1500,
                                    "node": {"name": "JavaScript", "color": "#f1e05a"},
                                },
                                {
                                    "size": 800,
                                    "node": {"name": "HTML", "color": "#e34c26"},
                                },
                                {
                                    "size": 500,
                                    "node": {"name": "CSS", "color": "#563d7c"},
                                },
                                {
                                    "size": 200,
                                    "node": {"name": "Shell", "color": "#89e051"},
                                },
                            ]
                        },
                    }
                ]
            },
        }
    }
}

MOCK_USER_NOT_FOUND = {
    "data": {"user": None},
    "errors": [
        {
            "message": (
                "Could not resolve to a User with the login of "
                "'nonexistentuser1234567890'."
            )
        }
    ],
}

MOCK_USER_PROFILE = {
    "data": {
        "user": {
            "name": "The Octocat",
            "login": "octocat",
            "createdAt": "2011-01-25T18:44:36Z",
            "followers": {"totalCount": 21400},
            "following": {"totalCount": 9},
            "repositories": {
                "totalCount": 8,
                "nodes": [{"stargazers": {"totalCount": 85}}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            },
        }
    }
}

def mock_github_post(url: str, *args: object, **kwargs: object) -> httpx.Response:
    """Simulate GitHub GraphQL responses for endpoint tests."""
    req_json = kwargs.get("json", {})
    if not isinstance(req_json, dict):
        return httpx.Response(400, json={"errors": [{"message": "Invalid mock request"}]})

    variables = req_json.get("variables", {})
    if not isinstance(variables, dict):
        variables = {}
    login = variables.get("login", "")

    if login == "nonexistentuser1234567890":
        return httpx.Response(200, json=MOCK_USER_NOT_FOUND)

    query = req_json.get("query", "")
    if "userTopLanguages" in query:
        return httpx.Response(200, json=MOCK_USER_LANGUAGES)
    if "userStreak" in query:
        return httpx.Response(200, json=MOCK_USER_STREAK)
    if "userProfile" in query:
        return httpx.Response(200, json=MOCK_USER_PROFILE)
    return httpx.Response(200, json=MOCK_USER_STATS)


def assert_user_not_found_error_card(response: httpx.Response) -> None:
    """Verify that an unknown user is represented by an SVG error card."""
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "User not found" in response.text


@pytest.fixture(autouse=True)
def setup_mock_and_clear_cache():
    """Mock GitHub requests and clear cached values for each test."""
    cache.clear()
    with patch("httpx.AsyncClient.post", side_effect=mock_github_post):
        yield
    cache.clear()


def test_get_user_success() -> None:
    response = client.get("/api?username=octocat&theme=default")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "The Octocat" in response.text


def test_get_user_not_found() -> None:
    response = client.get(
        "/api?username=nonexistentuser1234567890&theme=default"
    )

    assert_user_not_found_error_card(response)


def test_get_user_no_username() -> None:
    response = client.get("/api?theme=default")

    assert response.status_code == 422
    assert response.headers["Content-Type"] == "application/json"
    assert "username" in str(response.json()["detail"])


def test_get_streak_success() -> None:
    response = client.get("/api/streak?username=octocat&theme=dracula")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "STREAK" in response.text
    assert "flame-gradient" in response.text


def test_get_streak_portuguese_locale() -> None:
    response = client.get("/api/streak?username=octocat&locale=pt")

    assert response.status_code == 200
    assert "OFENSIVA" in response.text


def test_get_streak_not_found() -> None:
    response = client.get(
        "/api/streak?username=nonexistentuser1234567890"
    )

    assert_user_not_found_error_card(response)


def test_get_streak_no_username() -> None:
    response = client.get("/api/streak")

    assert response.status_code == 422


def test_get_top_languages_success() -> None:
    response = client.get("/api/top-langs?username=octocat&theme=dracula")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "Most Used Languages" in response.text
    assert "Python" in response.text
    assert "JavaScript" in response.text


def test_get_top_languages_hide_param() -> None:
    response = client.get("/api/top-langs?username=octocat&hide=html,css")

    assert response.status_code == 200
    assert "Python" in response.text
    assert "HTML" not in response.text


def test_get_top_languages_not_found() -> None:
    response = client.get(
        "/api/top-langs?username=nonexistentuser1234567890"
    )

    assert_user_not_found_error_card(response)


def test_get_top_languages_no_username() -> None:
    response = client.get("/api/top-langs")

    assert response.status_code == 422


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_profile_success() -> None:
    response = client.get("/api/profile?username=octocat&theme=dracula")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "max-age=14400" in response.headers["Cache-Control"]
    assert "The Octocat" in response.text
    assert "Followers" in response.text
    assert "21.4k" in response.text


def test_get_profile_portuguese_locale() -> None:
    response = client.get("/api/profile?username=octocat&locale=pt")

    assert response.status_code == 200
    assert "Seguidores" in response.text
    assert "Perfil GitHub de The Octocat" in response.text


def test_get_profile_custom_title() -> None:
    response = client.get("/api/profile?username=octocat&card_title=My%20business%20card")

    assert response.status_code == 200
    assert "My business card" in response.text


def test_get_profile_not_found() -> None:
    response = client.get("/api/profile?username=nonexistentuser1234567890")

    assert_user_not_found_error_card(response)


def test_get_profile_no_username() -> None:
    response = client.get("/api/profile?theme=default")

    assert response.status_code == 422
    assert response.headers["Content-Type"] == "application/json"


def test_get_repo_stats_locale() -> None:
    response = client.get("/api/stats?username=octocat&locale=pt")
    assert response.status_code == 200
    assert "Estatísticas do GitHub de The Octocat" in response.text
    assert "Total de commits:" in response.text
    assert "Rank GitHub" in response.text


def test_get_repo_stats_invalid_locale() -> None:
    response = client.get("/api/stats?username=octocat&locale=invalid")
    assert response.status_code == 200  # Returns error SVG
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "Could not load GitHub data" in response.text


def test_get_top_languages_locale() -> None:
    response = client.get("/api/top-langs?username=octocat&locale=pt")
    assert response.status_code == 200
    assert "Linguagens Mais Usadas" in response.text


def test_get_top_languages_invalid_locale() -> None:
    response = client.get("/api/top-langs?username=octocat&locale=invalid")
    assert response.status_code == 200  # Returns error SVG
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "Could not load GitHub data" in response.text