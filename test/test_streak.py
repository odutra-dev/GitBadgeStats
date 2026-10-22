import xml.etree.ElementTree as ET
from datetime import date
import pytest

from src.github import calculate_streak_from_days
from src.render_streak import render_flame_svg, generate_streak_svg
from src.utils import parse_background, escape_text, format_color
from src.cache import SimpleTTLCache


def test_streak_committed_today():
    """If user committed today: flame is lit (painted) and included in count."""
    test_today = date(2026, 10, 22)
    days = [
        {"date": "2026-10-19", "count": 1},
        {"date": "2026-10-20", "count": 3},
        {"date": "2026-10-21", "count": 2},
        {"date": "2026-10-22", "count": 4},
    ]

    result = calculate_streak_from_days(days, user_date=test_today, locale="en")
    assert result["current_streak"] == 4
    assert result["is_active_today"] is True
    assert result["today_commits"] == 4
    assert "burning" in result["streak_message"].lower()

    # Verify last 7 days tracker
    weekly = result["weekly_days"]
    assert len(weekly) == 7
    assert weekly[-1]["is_today"] is True
    assert weekly[-1]["is_active"] is True
    assert weekly[-1]["count"] == 4


def test_streak_committed_today_pt():
    """Test streak message in Portuguese locale."""
    test_today = date(2026, 10, 22)
    days = [{"date": "2026-10-22", "count": 1}]
    result = calculate_streak_from_days(days, user_date=test_today, locale="pt")
    assert "acesa" in result["streak_message"].lower()


def test_streak_pending_today():
    """If user committed yesterday but not today: streak preserved from yesterday, flame unlit today."""
    test_today = date(2026, 10, 22)
    days = [
        {"date": "2026-10-20", "count": 3},
        {"date": "2026-10-21", "count": 2},
        {"date": "2026-10-22", "count": 0},
    ]

    result = calculate_streak_from_days(days, user_date=test_today, locale="en")
    assert result["current_streak"] == 2
    assert result["is_active_today"] is False
    assert result["today_commits"] == 0
    assert "unlit" in result["streak_message"].lower()

    weekly = result["weekly_days"]
    assert weekly[-1]["is_today"] is True
    assert weekly[-1]["is_active"] is False


def test_streak_resets_after_missed_day():
    """If a full day is missed (yesterday = 0), the streak resets to 0."""
    test_today = date(2026, 10, 22)
    days = [
        {"date": "2026-10-18", "count": 5},
        {"date": "2026-10-19", "count": 2},
        {"date": "2026-10-20", "count": 4},
        {"date": "2026-10-21", "count": 0},  # Missed day
        {"date": "2026-10-22", "count": 0},  # Today also uncommitted
    ]

    result = calculate_streak_from_days(days, user_date=test_today, locale="en")
    assert result["current_streak"] == 0
    assert result["is_active_today"] is False
    assert result["longest_streak"] == 3


def test_streak_reignites_on_commit_after_miss():
    """If previously reset, committing today starts a new streak of 1 with lit flame."""
    test_today = date(2026, 10, 22)
    days = [
        {"date": "2026-10-20", "count": 0},
        {"date": "2026-10-21", "count": 0},
        {"date": "2026-10-22", "count": 2},  # Committed today
    ]

    result = calculate_streak_from_days(days, user_date=test_today, locale="en")
    assert result["current_streak"] == 1
    assert result["is_active_today"] is True


def test_longest_streak_historical():
    """Historical longest streak accurately computed across period."""
    test_today = date(2026, 10, 22)
    days = [
        {"date": "2026-10-01", "count": 1},
        {"date": "2026-10-02", "count": 2},
        {"date": "2026-10-03", "count": 3},
        {"date": "2026-10-04", "count": 1},
        {"date": "2026-10-05", "count": 2},  # 5-day streak
        {"date": "2026-10-06", "count": 0},
        {"date": "2026-10-21", "count": 1},
        {"date": "2026-10-22", "count": 1},  # Current 2-day streak
    ]

    result = calculate_streak_from_days(days, user_date=test_today, locale="en")
    assert result["current_streak"] == 2
    assert result["longest_streak"] == 5


def test_flame_rendering_lit_vs_unlit():
    """Lit flame contains gradient and glow filter; unlit flame is desaturated without filter."""
    flame_lit = render_flame_svg(0, 0, 50, 60, is_lit=True, dark_mode=True)
    assert "flame-gradient-outer" in flame_lit
    assert "flame-glow" in flame_lit

    flame_unlit = render_flame_svg(0, 0, 50, 60, is_lit=False, dark_mode=True)
    assert "flame-gradient-outer" not in flame_unlit
    assert "filter=" not in flame_unlit


def test_generate_streak_svg_validity_and_themes():
    """Generated SVG is valid XML, supports themes, gradients, and escapes special characters."""
    stats = {
        "name": "Tom <script> & Jerry",
        "current_streak": 7,
        "longest_streak": 20,
        "total_commits": 350,
        "is_active_today": True,
        "streak_message": "Streak active!",
        "weekly_days": [
            {"date": f"2026-10-{16+i}", "day_name": "Day", "count": i, "is_active": (i > 0), "is_today": (i == 6)}
            for i in range(7)
        ],
    }

    # Test with default theme
    svg = generate_streak_svg(stats, theme_name="default", locale="en")
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "Tom &lt;script&gt; &amp; Jerry" in svg
    assert "DAY STREAK" in svg

    # Test with dark theme (dracula)
    svg_dracula = generate_streak_svg(stats, theme_name="dracula")
    root_dracula = ET.fromstring(svg_dracula)
    assert root_dracula.tag.endswith("svg")

    # Test with gradient theme (ambient_gradient)
    svg_grad = generate_streak_svg(stats, theme_name="ambient_gradient")
    root_grad = ET.fromstring(svg_grad)
    assert root_grad.tag.endswith("svg")
    assert "linearGradient id=\"bg-gradient\"" in svg_grad

    # Test compact mode (hide_days=True)
    svg_compact = generate_streak_svg(stats, hide_days=True)
    root_compact = ET.fromstring(svg_compact)
    assert int(root_compact.attrib["height"]) == 145


def test_ttl_cache():
    """Verify basic TTL cache behavior."""
    c = SimpleTTLCache(default_ttl_seconds=1)
    c.set("k1", "v1")
    assert c.get("k1") == "v1"
    c.delete("k1")
    assert c.get("k1") is None
    c.set("k2", "v2", ttl_seconds=0.01)
    import time
    time.sleep(0.02)
    assert c.get("k2") is None


def test_gradient_parser():
    """Verify color parsing and gradient definitions."""
    defs, fill = parse_background("35,4158d0,c850c0,ffcc70")
    assert "linearGradient" in defs
    assert fill == "url(#bg-gradient)"

    defs_solid, fill_solid = parse_background("151515")
    assert defs_solid == ""
    assert fill_solid == "#151515"
