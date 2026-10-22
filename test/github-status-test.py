import os
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure token is present for test environment
if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "test-token-value"

from main import app
from src.cache import cache

client = TestClient(app)

# Mocks for GitHub GraphQL API simulation
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

MOCK_USER_NOT_FOUND = {
    "data": {"user": None},
    "errors": [{"message": "Could not resolve to a User with the login of 'nonexistentuser1234567890'."}],
}


def mock_github_post(url, *args, **kwargs):
    req_json = kwargs.get("json", {})
    variables = req_json.get("variables", {})
    login = variables.get("login", "")

    if login == "nonexistentuser1234567890":
        return httpx.Response(200, json=MOCK_USER_NOT_FOUND)

    query = req_json.get("query", "")
    if "userStreak" in query:
        return httpx.Response(200, json=MOCK_USER_STREAK)
    return httpx.Response(200, json=MOCK_USER_STATS)


@pytest.fixture(autouse=True)
def setup_mock_and_clear_cache():
    cache.clear()
    with patch("httpx.AsyncClient.post", side_effect=mock_github_post):
        yield
    cache.clear()


def test_get_user_success():
    response = client.get("/api?username=octocat&theme=default")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "The Octocat" in response.text


def test_get_user_not_found():
    response = client.get("/api?username=nonexistentuser1234567890&theme=default")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == {"detail": "User not found"}


def test_get_user_theme_not_found():
    response = client.get("/api?username=octocat&theme=nonexistenttheme")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text

    response = client.get("/api?username=octocat&theme=default")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text


def test_get_user_no_username():
    response = client.get("/api?theme=default")
    assert response.status_code == 422
    assert response.headers["Content-Type"] == "application/json"
    assert "username" in str(response.json()["detail"])


def test_get_streak_success():
    response = client.get("/api/streak?username=octocat&theme=dracula")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "STREAK" in response.text
    assert "flame-gradient" in response.text


def test_get_streak_portuguese_locale():
    response = client.get("/api/streak?username=octocat&locale=pt")
    assert response.status_code == 200
    assert "OFENSIVA" in response.text


def test_get_streak_not_found():
    response = client.get("/api/streak?username=nonexistentuser1234567890")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_get_streak_no_username():
    response = client.get("/api/streak")
    assert response.status_code == 422


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
