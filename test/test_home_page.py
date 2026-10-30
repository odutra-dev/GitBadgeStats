"""Unit and integration tests for the home page (root route /) and its interactive components."""

import os
from unittest.mock import patch
from pathlib import Path
from fastapi.testclient import TestClient

if not os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = "test-token-value"

from main import app

client = TestClient(app)


def test_home_page_status_and_headers():
    """Validate that GET / returns HTTP 200 with HTML content-type."""
    response = client.get("/")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert "text/html" in content_type


def test_home_page_document_structure():
    """Validate document structure, language, and core titles."""
    response = client.get("/")
    html = response.text

    assert "<!DOCTYPE html>" in html
    assert '<html lang="en"' in html
    assert "<title>Git Badge Stats - Dynamic GitHub Profile Badges</title>" in html
    assert 'href="/static/style.css"' in html
    assert 'src="/static/app.js"' in html
    assert 'href="/docs"' in html


def test_home_page_card_selection_options():
    """Validate that all 3 card options (stats, streak, languages) are present in the left panel."""
    response = client.get("/")
    html = response.text

    # Card tab buttons with their identifiers
    assert 'data-card="stats"' in html
    assert 'data-card="streak"' in html
    assert 'data-card="languages"' in html

    # Titles and descriptions
    assert "GitHub Stats" in html
    assert "Commit Streak" in html
    assert "Top Languages" in html


def test_home_page_preview_canvas_components():
    """Validate that the preview canvas elements, loading indicator, and refresh actions exist."""
    response = client.get("/")
    html = response.text

    assert 'id="preview-wrapper"' in html
    assert 'id="preview-loading"' in html
    assert 'id="preview-placeholder"' in html
    assert 'id="preview-img"' in html
    assert 'id="btn-refresh-preview"' in html
    assert 'id="link-open-raw"' in html
    assert 'id="active-badge-endpoint"' in html


def test_home_page_readme_export_options():
    """Validate the 3 export format options (Markdown, HTML, Direct Link), copy button, and URL toggle."""
    response = client.get("/")
    html = response.text

    # 3 Export formats
    assert 'data-format="markdown"' in html
    assert 'data-format="html"' in html
    assert 'data-format="link"' in html

    # Code snippet output and copy button
    assert 'id="code-output"' in html
    assert 'id="btn-copy-code"' in html
    assert 'id="copy-text"' in html
    assert 'id="copy-icon"' in html

    # Production URL toggle
    assert 'id="toggle-production-url"' in html


def test_home_page_form_inputs_and_validation():
    """Validate the configuration form, required username field, and card parameter controls."""
    response = client.get("/")
    html = response.text

    # Form and required username
    assert 'id="card-form"' in html
    assert 'id="input-username"' in html
    assert 'id="username-error"' in html
    assert 'required' in html

    # Theme selector and reset button
    assert 'id="select-theme"' in html
    assert 'id="btn-reset-form"' in html

    # Specific card inputs
    assert 'id="select-stats-locale"' in html
    assert 'id="input-hide-rank"' in html
    assert 'id="select-locale"' in html
    assert 'id="input-timezone"' in html
    assert 'id="input-hide-days"' in html
    assert 'id="select-langs-locale"' in html
    assert 'id="input-card-title"' in html
    assert 'id="input-hide-langs"' in html
    assert 'id="input-exclude-repos"' in html


def test_home_page_color_customizer_controls():
    """Validate custom color controls and their corresponding color pickers."""
    response = client.get("/")
    html = response.text

    assert 'id="btn-toggle-colors"' in html
    assert 'id="container-colors"' in html

    # Inputs and pickers
    for param in ["title-color", "text-color", "icon-color", "bg-color", "border-color"]:
        assert f'id="input-{param}"' in html
        assert f'id="picker-{param}"' in html


def test_home_page_static_assets_served():
    """Validate that static assets linked on the home page are served with correct headers."""
    css_res = client.get("/static/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers.get("content-type", "")
    assert len(css_res.text) > 50

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers.get("content-type", "")
    assert "PRODUCTION_BASE_URL" in js_res.text


def test_home_page_missing_file_returns_404():
    """Validate that serve_home returns HTTP 404 when index.html does not exist."""
    with patch.object(Path, "exists", return_value=False):
        response = client.get("/")
        assert response.status_code == 404
        assert response.json()["detail"] == "Homepage not found"

def test_home_page_profile_card_option_and_settings():
    """Validate the profile card tab and its settings section."""
    response = client.get("/")
    html = response.text

    assert 'data-card="profile"' in html
    assert "GitHub Profile" in html
    assert 'id="section-profile-options"' in html
    assert 'id="select-profile-locale"' in html
    assert 'id="input-profile-title"' in html


def test_home_page_script_knows_the_profile_route():
    """Validate that the generator script maps the profile card to its API route."""
    js_res = client.get("/static/app.js")

    assert js_res.status_code == 200
    assert "'/api/profile'" in js_res.text
    

def test_home_page_script_maps_profile_card_metadata():
    """The profile card must have its route, title, and endpoint label."""
    response = client.get("/static/app.js")

    assert response.status_code == 200
    js = response.text

    assert "profile: '/api/profile'" in js
    assert "profile: 'GitHub Profile'" in js
    assert "profile: 'GET /api/profile'" in js


def test_home_page_script_reads_profile_settings():
    """The script must reference the profile-specific form controls."""
    response = client.get("/static/app.js")
    js = response.text

    assert "section-profile-options" in js
    assert "select-profile-locale" in js
    assert "input-profile-title" in js


def test_home_page_script_toggles_profile_settings():
    """Only the active card's specific settings section should be visible."""
    response = client.get("/static/app.js")
    js = response.text

    assert "sectionProfileOptions.classList.toggle" in js
    assert "cardType !== 'profile'" in js


def test_home_page_script_resets_profile_settings():
    """Reset must restore the profile locale and clear the custom title."""
    response = client.get("/static/app.js")
    js = response.text

    assert "selectProfileLocale.value = 'en'" in js
    assert "inputProfileTitle.value = ''" in js


def test_home_page_script_registers_profile_listeners():
    """Changes to profile controls must trigger an update."""
    response = client.get("/static/app.js")
    js = response.text

    assert (
        "selectProfileLocale.addEventListener"
        "('change', handleImmediateChange)"
    ) in js

    assert (
        "inputProfileTitle.addEventListener"
        "('input', handleInputDebounced)"
    ) in js


def test_home_page_profile_icon_color_remains_enabled():
    """The icon color override must remain available for the profile card."""
    response = client.get("/static/app.js")
    js = response.text

    assert "if (activeCard !== 'languages')" in js
    assert "params.set('icon_color', iconColor)" in js
