"""Unit tests for GitHub Achievements domain, service, renderer, and API routes.

Co-authored-by: Andersoncrs5 <anderson.c.rms2005@gmail.com>
"""

import re
from dataclasses import asdict
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app
from src.common.achievement_assets import (
    ACHIEVEMENT_BADGE_DATA_URIS,
    get_achievement_badge_data_uri,
    get_tier_style,
)
from src.common.locales import (
    ACHIEVEMENTS_TRANSLATIONS,
    get_achievements_translations,
)
from src.domain.achievements import (
    ACHIEVEMENT_DEFINITIONS,
    ORDERED_ACHIEVEMENT_IDS,
    UserAchievement,
    build_user_achievements,
    normalize_achievement_id,
    parse_profile_achievements,
)
from src.renderers.achievements_card import (
    AchievementsCardRenderer,
    generate_achievements_svg,
)
from src.services.achievements_service import fetch_github_achievements
from src.services.cache import SimpleTTLCache


# ---------------------------------------------------------------------------
# Domain Tests
# ---------------------------------------------------------------------------

def test_normalize_achievement_id() -> None:
    assert normalize_achievement_id("pull-shark") == "pull-shark"
    assert normalize_achievement_id("PullShark") == "pull-shark"
    assert normalize_achievement_id("StarStruck") == "starstruck"
    assert normalize_achievement_id("galaxy-brain") == "galaxy-brain"
    assert normalize_achievement_id("Pair_Extraordinaire") == "pair-extraordinaire"
    assert normalize_achievement_id("QuickDraw") == "quickdraw"
    assert normalize_achievement_id("yolo") == "yolo"
    assert normalize_achievement_id("sponsor") == "public-sponsor"
    assert normalize_achievement_id("non-existent-badge") is None


def test_parse_profile_achievements_from_html() -> None:
    sample_html = """
    <div>
        <img src="https://github.githubassets.com/assets/pull-shark-silver-0643f87ac9fd.png" alt="Achievement: Pull Shark" />
        <img src="https://github.githubassets.com/assets/starstruck-gold-a35e077693cc.png" alt="Achievement: Starstruck" />
        <img src="https://github.githubassets.com/assets/galaxy-brain-bronze-da3c4829fd22.png" alt="Achievement: Galaxy Brain" />
        <img src="https://github.githubassets.com/assets/quickdraw-default-39c6aec8ff89.png" alt="Achievement: Quickdraw" />
    </div>
    """
    detected = parse_profile_achievements(sample_html)
    assert len(detected) == 4
    assert detected["pull-shark"]["tier"] == "silver"
    assert detected["starstruck"]["tier"] == "gold"
    assert detected["galaxy-brain"]["tier"] == "bronze"
    assert detected["quickdraw"]["tier"] == "default"


def test_parse_profile_achievements_keeps_highest_tier() -> None:
    duplicate_html = """
    <img src="https://github.githubassets.com/assets/pull-shark-bronze-a37accb528d1.png" alt="Achievement: Pull Shark" />
    <img src="https://github.githubassets.com/assets/pull-shark-gold-5335a3b8ae7d.png" alt="Achievement: Pull Shark" />
    """
    detected = parse_profile_achievements(duplicate_html)
    assert detected["pull-shark"]["tier"] == "gold"


def test_parse_profile_achievements_empty_html() -> None:
    assert parse_profile_achievements("") == {}
    assert parse_profile_achievements("<html><body>No badges</body></html>") == {}


def test_build_user_achievements_progress_and_tiers() -> None:
    official = {
        "pull-shark": {"id": "pull-shark", "name": "Pull Shark", "tier": "silver", "src": "mock_src"},
        "quickdraw": {"id": "quickdraw", "name": "Quickdraw", "tier": "default", "src": "mock_src"},
    }
    metrics = {"starstruck": 200}  # 200 stars unlocks bronze (128) towards silver (512)

    achievements = build_user_achievements(official_badges=official, metric_counts=metrics)
    assert len(achievements) == len(ORDERED_ACHIEVEMENT_IDS)

    by_id = {a.id: a for a in achievements}

    # Pull shark has silver x3
    ps = by_id["pull-shark"]
    assert ps.unlocked is True
    assert ps.tier == "silver"
    assert ps.multiplier == "x3"
    assert ps.current_value >= 128
    assert ps.target_value == 1024

    # Starstruck unlocked via metrics
    st = by_id["starstruck"]
    assert st.unlocked is True
    assert st.tier == "bronze"
    assert st.current_value == 200
    assert st.target_value == 512

    # Quickdraw unlocked default
    qd = by_id["quickdraw"]
    assert qd.unlocked is True
    assert qd.tier == "default"
    assert qd.multiplier == "x1"

    # Galaxy brain is locked
    gb = by_id["galaxy-brain"]
    assert gb.unlocked is False
    assert gb.tier == "locked"
    assert gb.tier_label == "Locked"
    assert gb.target_value == 2


# ---------------------------------------------------------------------------
# Locales Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("locale", ["en", "pt", "es", "fr", "de"])
def test_get_achievements_translations_supported(locale: str) -> None:
    t = get_achievements_translations(locale)
    assert "card_title" in t
    assert "unlocked_label" in t
    assert "locked_label" in t
    assert "pull-shark" in t["achievements"]
    assert "yolo" in t["achievements"]


def test_get_achievements_translations_unsupported() -> None:
    with pytest.raises(ValueError, match="Unsupported locale 'ja'"):
        get_achievements_translations("ja")


# ---------------------------------------------------------------------------
# Assets Tests
# ---------------------------------------------------------------------------

def test_achievement_badge_data_uris_populated() -> None:
    assert len(ACHIEVEMENT_BADGE_DATA_URIS) == 7
    for ach_id in ORDERED_ACHIEVEMENT_IDS:
        uri = get_achievement_badge_data_uri(ach_id)
        assert uri.startswith("data:image/png;base64,")


def test_fallback_badge_data_uri_for_unknown() -> None:
    uri = get_achievement_badge_data_uri("unknown-custom-badge")
    assert uri.startswith("data:image/svg+xml,")


def test_tier_styles() -> None:
    gold = get_tier_style("gold")
    assert gold["border"] == "#e3b341"

    locked = get_tier_style("locked")
    assert locked["border"] == "#30363d"

    fallback = get_tier_style("unknown")
    assert fallback["border"] == "#388bfd"


# ---------------------------------------------------------------------------
# Service Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_fetch_github_achievements_cached() -> None:
    test_cache = SimpleTTLCache(default_ttl_seconds=300)
    cached_payload = {
        "username": "cacheduser",
        "name": "Cached User",
        "achievements": [],
        "total_unlocked": 0,
        "total_possible": 7,
    }
    test_cache.set("achievements:cacheduser", cached_payload)

    result = await fetch_github_achievements(
        username="cacheduser",
        use_cache=True,
        cache_backend=test_cache,
    )
    assert result == cached_payload


@pytest.mark.anyio
async def test_fetch_github_achievements_not_found() -> None:
    test_cache = SimpleTTLCache(default_ttl_seconds=300)

    # Mock 404 response
    mock_transport = httpx.MockTransport(
        lambda request: httpx.Response(404, request=request)
    )
    async with httpx.AsyncClient(transport=mock_transport) as mock_client:
        with pytest.raises(Exception) as exc_info:
            await fetch_github_achievements(
                username="nonexistent_user_123456",
                use_cache=False,
                cache_backend=test_cache,
                http_client=mock_client,
            )
        assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_fetch_github_achievements_success() -> None:
    test_cache = SimpleTTLCache(default_ttl_seconds=300)
    html_content = """
    <img src="https://github.githubassets.com/assets/pull-shark-bronze-a37accb528d1.png" alt="Achievement: Pull Shark" />
    <img src="https://github.githubassets.com/assets/yolo-default-be0bbff04951.png" alt="Achievement: YOLO" />
    """

    mock_transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=html_content, request=request)
    )
    async with httpx.AsyncClient(transport=mock_transport) as mock_client:
        mock_graphql = AsyncMock()
        mock_graphql.execute_query.return_value = {
            "name": "Octocat Hero",
            "login": "octocat",
            "repositories": {"nodes": [{"stargazers": {"totalCount": 42}}]},
        }

        result = await fetch_github_achievements(
            username="octocat",
            use_cache=False,
            cache_backend=test_cache,
            client=mock_graphql,
            http_client=mock_client,
        )

        assert result["username"] == "octocat"
        assert result["name"] == "Octocat Hero"
        assert result["total_unlocked"] >= 2
        assert len(result["achievements"]) == 7


# ---------------------------------------------------------------------------
# Renderer Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_achievements_data() -> dict:
    achievements = build_user_achievements(
        official_badges={
            "pull-shark": {"id": "pull-shark", "name": "Pull Shark", "tier": "gold", "src": "src"},
            "starstruck": {"id": "starstruck", "name": "Starstruck", "tier": "silver", "src": "src"},
            "galaxy-brain": {"id": "galaxy-brain", "name": "Galaxy Brain", "tier": "bronze", "src": "src"},
        }
    )
    return {
        "username": "dutra",
        "name": "Dutra Dev",
        "achievements": [asdict(a) for a in achievements],
        "total_unlocked": 3,
        "total_possible": 7,
    }


def test_generate_achievements_svg_basic(sample_achievements_data: dict) -> None:
    svg = generate_achievements_svg(sample_achievements_data, theme_name="tokyonight", locale="en")
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Achievements" in svg
    assert "Pull Shark" in svg
    assert "Starstruck" in svg
    assert "3 / 7 UNLOCKED" in svg


def test_generate_achievements_svg_locale_pt(sample_achievements_data: dict) -> None:
    svg = generate_achievements_svg(sample_achievements_data, locale="pt")
    assert "Conquistas de Dutra Dev" in svg
    assert "DESBLOQUEADAS" in svg


def test_generate_achievements_svg_show_locked_false(sample_achievements_data: dict) -> None:
    svg_all = generate_achievements_svg(sample_achievements_data, show_locked=True)
    svg_only_unlocked = generate_achievements_svg(sample_achievements_data, show_locked=False)

    # svg_all has 7 items in 2 rows (height=230)
    assert 'height="230"' in svg_all
    # svg_only_unlocked has 3 items in 1 row (height=150)
    assert 'height="150"' in svg_only_unlocked


def test_generate_achievements_svg_hide_specific(sample_achievements_data: dict) -> None:
    svg = generate_achievements_svg(sample_achievements_data, hide="pull-shark,yolo")
    assert 'clip-pull-shark' not in svg
    assert 'clip-yolo' not in svg
    assert 'clip-starstruck' in svg


def test_generate_achievements_svg_empty_state() -> None:
    empty_data = {
        "username": "emptyuser",
        "name": "Empty User",
        "achievements": [],
        "total_unlocked": 0,
        "total_possible": 7,
    }
    svg = generate_achievements_svg(empty_data, show_locked=False, locale="en")
    assert "No achievements unlocked yet" in svg
    assert 'height="140"' in svg


def test_generate_achievements_svg_custom_colors_and_title(sample_achievements_data: dict) -> None:
    svg = generate_achievements_svg(
        sample_achievements_data,
        custom_title="Hall of Fame",
        title_color_override="ff0000",
        bg_color_override="000000",
    )
    assert "Hall of Fame" in svg
    assert "#ff0000" in svg
    assert "#000000" in svg


def test_generate_achievements_svg_show_progress(sample_achievements_data: dict) -> None:
    # Default show_progress=False: no disclaimer, no progress elements
    svg_default = generate_achievements_svg(sample_achievements_data, show_progress=False, locale="en")
    assert 'class="progress-text"' not in svg_default
    assert 'class="disclaimer-text"' not in svg_default
    assert 'height="230"' in svg_default

    # show_progress=True: progress bar, remaining/max labels, disclaimer note
    svg_progress = generate_achievements_svg(sample_achievements_data, show_progress=True, locale="en")
    assert 'class="progress-text"' in svg_progress
    assert 'class="disclaimer-text"' in svg_progress
    assert "* Progress is an estimate based on public GitHub activity." in svg_progress
    assert 'height="275"' in svg_progress
    assert "Max Tier" in svg_progress or "left" in svg_progress

    # Portuguese locale
    svg_pt = generate_achievements_svg(sample_achievements_data, show_progress=True, locale="pt")
    assert "* Progresso estimado com base em atividades públicas do GitHub." in svg_pt

    # Single row height when locked items hidden
    svg_1row = generate_achievements_svg(sample_achievements_data, show_progress=True, show_locked=False)
    assert 'height="185"' in svg_1row


# ---------------------------------------------------------------------------
# API Routes Tests
# ---------------------------------------------------------------------------

client = TestClient(app)


def test_api_achievements_validation() -> None:
    # Invalid theme: caught by _validate_theme, rendered as SVG error badge
    response = client.get("/api/achievements?username=torvalds&theme=invalid_theme_xyz")
    assert response.status_code == 200  # Badge error rendered as SVG
    assert "image/svg+xml" in response.headers["content-type"]
    assert "Could not load GitHub data" in response.text

    # Invalid locale: caught by _validate_locale, rendered as SVG error badge
    response = client.get("/api/conquistas?username=torvalds&locale=xx")
    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]
    assert "Could not load GitHub data" in response.text


@patch("main.fetch_github_achievements")
def test_api_achievements_endpoint_success(mock_fetch: AsyncMock, sample_achievements_data: dict) -> None:
    mock_fetch.return_value = sample_achievements_data

    # Test /api/achievements
    resp1 = client.get("/api/achievements?username=dutra&theme=dracula&locale=pt")
    assert resp1.status_code == 200
    assert "image/svg+xml" in resp1.headers["content-type"]
    assert "Conquistas de Dutra Dev" in resp1.text

    # Test /api/conquistas alias
    resp2 = client.get("/api/conquistas?username=dutra&theme=dracula&locale=pt")
    assert resp2.status_code == 200
    assert "image/svg+xml" in resp2.headers["content-type"]
    assert "Conquistas de Dutra Dev" in resp2.text

    # Test show_progress=true
    resp3 = client.get("/api/conquistas?username=dutra&show_progress=true&locale=pt")
    assert resp3.status_code == 200
    assert "Progresso estimado" in resp3.text
    assert "progress-text" in resp3.text
