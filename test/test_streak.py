import xml.etree.ElementTree as ET
from datetime import date
import pytest

from src.domain.streak import StreakCalculator, calculate_streak_from_days
from src.renderers.streak_card import StreakCardRenderer, render_flame_svg, generate_streak_svg
from src.common.utils import parse_background, escape_text, format_color
from src.services.cache import SimpleTTLCache


def test_streak_committed_today():
    """If user committed today: flame is lit (painted) and included in count."""
    test_today = date(2026, 10, 22)
    days = [
        {"date": "2026-10-19", "count": 1},
        {"date": "2026-10-20", "count": 3},
        {"date": "2026-10-21", "count": 2},
        {"date": "2026-10-22", "count": 4},
    ]

    result = StreakCalculator.calculate(days, user_date=test_today, locale="en")
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

    result = StreakCalculator.calculate(days, user_date=test_today, locale="en")
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

    result = StreakCalculator.calculate(days, user_date=test_today, locale="en")
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

    result = StreakCalculator.calculate(days, user_date=test_today, locale="en")
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

    result = StreakCalculator.calculate(days, user_date=test_today, locale="en")
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


def test_streak_msg_does_not_overlap_days():
    """Verify that the streak message (e.g. 'Streak active! Flame is burning today')
    is positioned cleanly in the header area (y <= 55) and has substantial vertical clearance
    from the weekly tracker day cards (y >= 140), preventing any visual overlap."""
    stats = {
        "name": "Octocat",
        "current_streak": 5,
        "longest_streak": 10,
        "total_commits": 100,
        "is_active_today": True,
        "streak_message": "Streak active! Flame is burning today",
        "weekly_days": [
            {"date": f"2026-10-{16+i}", "day_name": f"Day{i}", "count": i, "is_active": True, "is_today": (i == 6)}
            for i in range(7)
        ],
    }

    svg = generate_streak_svg(stats, locale="en")
    root = ET.fromstring(svg)

    # Find the streak message element
    streak_msg_elements = [
        elem for elem in root.iter()
        if elem.tag.endswith("text") and elem.attrib.get("class") == "streak-msg"
    ]
    assert len(streak_msg_elements) == 1
    msg_elem = streak_msg_elements[0]
    msg_y = float(msg_elem.attrib["y"])
    assert msg_y <= 55, f"Expected streak-msg y <= 55, but got {msg_y}"
    assert "Streak active! Flame is burning today" in msg_elem.text

    # Find weekly tracker group and check day box translation y-coordinates
    weekly_groups = [
        elem for elem in root.iter()
        if elem.tag.endswith("g") and elem.attrib.get("class") == "weekly-tracker"
    ]
    assert len(weekly_groups) == 1
    weekly_group = weekly_groups[0]

    # Every child item in weekly tracker must have transform="translate(x, y)" with y >= 140
    for child in weekly_group:
        transform = child.attrib.get("transform", "")
        if "translate" in transform:
            coords = transform.replace("translate(", "").replace(")", "").split(",")
            y_val = float(coords[1].strip())
            assert y_val >= 140, f"Weekly day card expected y >= 140, but got {y_val}"
            # Ensure at least 80px clearance between streak_msg and day card
            assert y_val - msg_y >= 80, f"Expected >= 80px vertical separation, got {y_val - msg_y}px"
