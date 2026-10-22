import os
from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure token is present for test environment
if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "test-token-value"

from main import app
from src.services.cache import cache

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
                                {"size": 3000, "node": {"name": "Python", "color": "#3572A5"}},
                                {"size": 1500, "node": {"name": "JavaScript", "color": "#f1e05a"}},
                                {"size": 800, "node": {"name": "HTML", "color": "#e34c26"}},
                                {"size": 500, "node": {"name": "CSS", "color": "#563d7c"}},
                                {"size": 200, "node": {"name": "Shell", "color": "#89e051"}},
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
    "errors": [{"message": "Could not resolve to a User with the login of 'nonexistentuser1234567890'."}],
}


def mock_github_post(url, *args, **kwargs):
    req_json = kwargs.get("json", {})
    variables = req_json.get("variables", {})
    login = variables.get("login", "")

    if login == "nonexistentuser1234567890":
        return httpx.Response(200, json=MOCK_USER_NOT_FOUND)

    query = req_json.get("query", "")
    if "userTopLanguages" in query:
        return httpx.Response(200, json=MOCK_USER_LANGUAGES)
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


def test_get_top_languages_success():
    response = client.get("/api/top-langs?username=octocat&theme=dracula")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["Content-Type"]
    assert "<svg" in response.text
    assert "Most Used Languages" in response.text
    assert "Python" in response.text
    assert "JavaScript" in response.text


def test_get_top_languages_hide_param():
    response = client.get("/api/top-langs?username=octocat&hide=html,css")
    assert response.status_code == 200
    assert "Python" in response.text
    assert "HTML" not in response.text


def test_get_top_languages_not_found():
    response = client.get("/api/top-langs?username=nonexistentuser1234567890")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_get_top_languages_no_username():
    response = client.get("/api/top-langs")
    assert response.status_code == 422


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
