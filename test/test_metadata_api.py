import os
from fastapi.testclient import TestClient

if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "test-token-value"

from main import app, SUPPORTED_LOCALES
from src.common.themes import themes

client = TestClient(app)


def test_get_themes():
    response = client.get("/api/themes")
    assert response.status_code == 200
    data = response.json()
    assert "themes" in data
    assert isinstance(data["themes"], list)
    assert len(data["themes"]) == len(themes)
    assert "default" in data["themes"]
    assert "tokyonight" in data["themes"]
    assert data["themes"] == sorted(themes.keys())


def test_get_locales():
    response = client.get("/api/locales")
    assert response.status_code == 200
    data = response.json()
    assert "locales" in data
    assert isinstance(data["locales"], list)
    assert set(data["locales"]) == set(SUPPORTED_LOCALES)


def test_serve_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Git Badge Stats" in response.text
    assert "card-tab-btn" in response.text
    assert "input-username" in response.text


def test_serve_static_assets():
    css_res = client.get("/static/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers.get("content-type", "")

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers.get("content-type", "")

