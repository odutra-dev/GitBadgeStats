import pytest
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_user_success():
    response = client.get("/api?username=octocat&theme=default")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/svg+xml"
    assert "<svg" in response.text


def test_get_user_not_found():
    response = client.get(
        "/api?username=nonexistentuser1234567890&theme=default")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == {"detail": "User not found"}


def test_get_user_theme_not_found():
    response = client.get("/api?username=octocat&theme=nonexistenttheme")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/svg+xml"
    assert "<svg" in response.text

    response = client.get("/api?username=octocat&theme=default")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/svg+xml"
    assert "<svg" in response.text


def test_get_user_no_username():
    response = client.get("/api?theme=default")
    assert response.status_code == 422
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == {
        "detail": [
            {
                'type': 'missing',
                'loc': [
                    'query', 'username'],
                'msg': 'Field required',
                'input': None
            }
        ]
    }
