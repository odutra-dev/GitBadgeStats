"""Tests for GitHub streak calculations, localization, and SVG rendering."""

import xml.etree.ElementTree as ET
from datetime import date
from typing import Literal, TypedDict, cast

import pytest

from src.common.locales import SUPPORTED_LOCALES, get_translations
from src.domain.streak import StreakCalculator, calculate_streak_from_days
from src.renderers.streak_card import generate_streak_svg, render_flame_svg

Locale = Literal["en", "pt", "es", "fr", "de"]


class ContributionDay(TypedDict):
    """A single day from GitHub's contribution calendar."""

    date: str
    count: int


class WeeklyDay(TypedDict):
    """A day shown in the seven-day tracker."""

    date: str
    day_name: str
    count: int
    is_active: bool
    is_today: bool


class StreakResult(TypedDict):
    """Result returned by the streak calculation."""

    current_streak: int
    longest_streak: int
    is_active_today: bool
    today_commits: int
    yesterday_commits: int
    weekly_days: list[WeeklyDay]
    streak_message: str


TEST_TODAY = date(2026, 10, 22)


def _calculate_streak(
    days: list[ContributionDay],
    *,
    user_date: date = TEST_TODAY,
    locale: str = "en",
) -> StreakResult:
    """Call the domain method and expose its expected result shape to type checkers."""
    raw_result = StreakCalculator.calculate(
        cast(list[dict], days),
        user_date=user_date,
        locale=locale,
    )
    return cast(StreakResult, raw_result)


def test_streak_committed_today() -> None:
    """A commit today lights the flame and counts today in the current streak."""
    days: list[ContributionDay] = [
        {"date": "2026-10-19", "count": 1},
        {"date": "2026-10-20", "count": 3},
        {"date": "2026-10-21", "count": 2},
        {"date": "2026-10-22", "count": 4},
    ]

    result = _calculate_streak(days)

    assert result["current_streak"] == 4
    assert result["is_active_today"] is True
    assert result["today_commits"] == 4
    assert "burning" in result["streak_message"].lower()

    weekly = result["weekly_days"]
    assert len(weekly) == 7
    assert weekly[-1]["is_today"] is True
    assert weekly[-1]["is_active"] is True
    assert weekly[-1]["count"] == 4


@pytest.mark.parametrize(
    ("locale", "expected_message"),
    [
        ("en", "Streak active! Flame is burning today"),
        ("pt", "Ofensiva mantida! Chama acesa hoje"),
        ("es", "¡Racha activa! La llama sigue encendida hoy"),
        ("fr", "Série active ! La flamme brûle aujourd'hui"),
        ("de", "Serie aktiv! Die Flamme brennt heute"),
    ],
)
def test_streak_active_message_localization(
    locale: Locale,
    expected_message: str,
) -> None:
    """The active-streak message is translated for all supported locales."""
    days: list[ContributionDay] = [{"date": "2026-10-22", "count": 1}]

    result = _calculate_streak(days, locale=locale)

    assert result["is_active_today"] is True
    assert result["streak_message"] == expected_message


@pytest.mark.parametrize(
    ("locale", "expected_message"),
    [
        ("en", "Flame unlit • Commit today to keep your streak!"),
        ("pt", "Chama apagada • Faça um commit hoje!"),
        (
            "es",
            "Llama apagada • ¡Haz un commit hoy para mantener tu racha!",
        ),
        (
            "fr",
            "Flamme éteinte • Faites un commit aujourd'hui pour continuer votre série !",
        ),
        (
            "de",
            "Flamme aus • Erstelle heute einen Commit, um deine Serie fortzusetzen!",
        ),
    ],
)
def test_streak_pending_message_localization(
    locale: Locale,
    expected_message: str,
) -> None:
    """A streak continues from yesterday when there is no commit today."""
    days: list[ContributionDay] = [
        {"date": "2026-10-20", "count": 3},
        {"date": "2026-10-21", "count": 2},
        {"date": "2026-10-22", "count": 0},
    ]

    result = _calculate_streak(days, locale=locale)

    assert result["current_streak"] == 2
    assert result["is_active_today"] is False
    assert result["today_commits"] == 0
    assert result["streak_message"] == expected_message
    assert result["weekly_days"][-1]["is_today"] is True
    assert result["weekly_days"][-1]["is_active"] is False


@pytest.mark.parametrize(
    ("locale", "expected_message"),
    [
        ("en", "Flame unlit • Commit to start your streak!"),
        ("pt", "Chama apagada • Faça um commit para iniciar!"),
        ("es", "Llama apagada • ¡Haz un commit para empezar tu racha!"),
        (
            "fr",
            "Flamme éteinte • Faites un commit pour commencer votre série !",
        ),
        (
            "de",
            "Flamme aus • Erstelle einen Commit, um deine Serie zu starten!",
        ),
    ],
)
def test_streak_start_message_localization(
    locale: Locale,
    expected_message: str,
) -> None:
    """The start message is shown when the user has no current streak."""
    days: list[ContributionDay] = [
        {"date": "2026-10-21", "count": 0},
        {"date": "2026-10-22", "count": 0},
    ]

    result = _calculate_streak(days, locale=locale)

    assert result["current_streak"] == 0
    assert result["is_active_today"] is False
    assert result["streak_message"] == expected_message


@pytest.mark.parametrize(
    ("locale", "expected_weekdays"),
    [
        ("en", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
        ("pt", ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]),
        ("es", ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]),
        ("fr", ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]),
        ("de", ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]),
    ],
)
def test_weekday_localization(
    locale: Locale,
    expected_weekdays: list[str],
) -> None:
    """The weekly tracker uses translated weekday abbreviations."""
    # A Sunday endpoint makes this seven-day window run Monday through Sunday.
    result = _calculate_streak(
        [],
        user_date=date(2026, 10, 25),
        locale=locale,
    )
    actual_weekdays: list[str] = [
        day["day_name"] for day in result["weekly_days"]
    ]

    assert actual_weekdays == expected_weekdays


def test_weekly_tracker_covers_today_and_previous_six_days() -> None:
    """The tracker contains exactly seven consecutive dates ending today."""
    result = _calculate_streak([])
    weekly_days = result["weekly_days"]

    assert len(weekly_days) == 7
    assert [day["date"] for day in weekly_days] == [
        "2026-10-16",
        "2026-10-17",
        "2026-10-18",
        "2026-10-19",
        "2026-10-20",
        "2026-10-21",
        "2026-10-22",
    ]
    assert [day["is_today"] for day in weekly_days] == [
        False,
        False,
        False,
        False,
        False,
        False,
        True,
    ]


def test_supported_locales_have_all_translation_keys() -> None:
    """All supported locales provide every translation used by the streak card."""
    assert SUPPORTED_LOCALES == ("en", "pt", "es", "fr", "de")

    required_keys = {
        "weekdays",
        "status_active",
        "status_pending",
        "status_start",
        "card_title",
        "streak_label",
        "longest_label",
        "commits_label",
        "days_unit",
        "active_pill",
        "inactive_pill",
    }

    for locale in SUPPORTED_LOCALES:
        translations = get_translations(locale)

        assert required_keys.issubset(translations.keys())
        assert len(translations["weekdays"]) == 7
        assert all(translations[key] for key in required_keys - {"weekdays"})


def test_unsupported_locale_raises_value_error() -> None:
    """Direct domain calls reject locales that are not registered."""
    with pytest.raises(ValueError, match="Unsupported locale.*it"):
        StreakCalculator.calculate(
            [],
            user_date=TEST_TODAY,
            locale="it",
        )


def test_calculate_streak_from_days_matches_calculator() -> None:
    """The functional shortcut returns the same result as the class method."""
    days: list[ContributionDay] = [
        {"date": "2026-10-20", "count": 1},
        {"date": "2026-10-21", "count": 2},
        {"date": "2026-10-22", "count": 3},
    ]

    shortcut_result = calculate_streak_from_days(
        cast(list[dict], days),
        user_date=TEST_TODAY,
        locale="en",
    )
    direct_result = StreakCalculator.calculate(
        cast(list[dict], days),
        user_date=TEST_TODAY,
        locale="en",
    )

    assert shortcut_result == direct_result


def test_streak_resets_after_missed_day() -> None:
    """A missed day resets the current streak to zero."""
    days: list[ContributionDay] = [
        {"date": "2026-10-18", "count": 5},
        {"date": "2026-10-19", "count": 2},
        {"date": "2026-10-20", "count": 4},
        {"date": "2026-10-21", "count": 0},
        {"date": "2026-10-22", "count": 0},
    ]

    result = _calculate_streak(days)

    assert result["current_streak"] == 0
    assert result["is_active_today"] is False
    assert result["longest_streak"] == 3


def test_streak_reignites_on_commit_after_miss() -> None:
    """A commit today starts a new streak of one day."""
    days: list[ContributionDay] = [
        {"date": "2026-10-20", "count": 0},
        {"date": "2026-10-21", "count": 0},
        {"date": "2026-10-22", "count": 2},
    ]

    result = _calculate_streak(days)

    assert result["current_streak"] == 1
    assert result["is_active_today"] is True
    assert result["today_commits"] == 2


def test_longest_streak_historical_sorts_days_by_date() -> None:
    """The longest historical streak is computed chronologically, not by input order."""
    days: list[ContributionDay] = [
        {"date": "2026-10-22", "count": 1},
        {"date": "2026-10-05", "count": 2},
        {"date": "2026-10-02", "count": 2},
        {"date": "2026-10-06", "count": 0},
        {"date": "2026-10-03", "count": 3},
        {"date": "2026-10-21", "count": 1},
        {"date": "2026-10-01", "count": 1},
        {"date": "2026-10-04", "count": 1},
    ]

    result = _calculate_streak(days)

    assert result["current_streak"] == 2
    assert result["longest_streak"] == 5


def test_flame_rendering_lit_vs_unlit() -> None:
    """Lit flames use gradients and glow; unlit flames do not."""
    flame_lit = render_flame_svg(
        0,
        0,
        50,
        60,
        is_lit=True,
        dark_mode=True,
    )

    assert "flame-gradient-outer" in flame_lit
    assert "flame-glow" in flame_lit

    flame_unlit = render_flame_svg(
        0,
        0,
        50,
        60,
        is_lit=False,
        dark_mode=True,
    )

    assert "flame-gradient-outer" not in flame_unlit
    assert "filter=" not in flame_unlit


@pytest.mark.parametrize(
    ("locale", "expected_title", "expected_label"),
    [
        ("en", "Octocat's GitHub Streak", "DAY STREAK"),
        ("pt", "Ofensiva de Octocat", "DIAS DE OFENSIVA"),
        ("es", "Racha de GitHub de Octocat", "DÍAS DE RACHA"),
        ("fr", "Série GitHub de Octocat", "JOURS DE SÉRIE"),
        ("de", "GitHub-Serie von Octocat", "TAGE IN FOLGE"),
    ],
)
def test_streak_svg_localization(
    locale: Locale,
    expected_title: str,
    expected_label: str,
) -> None:
    """The rendered SVG localizes its title, labels, and status message."""
    days: list[ContributionDay] = [{"date": "2026-10-22", "count": 2}]
    calculated_stats = _calculate_streak(days, locale=locale)
    stats: dict[str, object] = {
        "name": "Octocat",
        "total_commits": 100,
        **calculated_stats,
    }

    svg = generate_streak_svg(stats, locale=locale)
    root: ET.Element = ET.fromstring(svg)

    assert root.tag.endswith("svg")

    # Check parsed XML text, not the serialized SVG: apostrophes may be escaped
    # as numeric XML entities (for example, &#x27;) in the SVG source.
    rendered_text: str = " ".join(
        element.text or ""
        for element in root.iter()
        if element.tag.endswith("text")
    )

    assert expected_title in rendered_text
    assert expected_label in rendered_text
    assert calculated_stats["streak_message"] in rendered_text
    assert calculated_stats["weekly_days"][-1]["day_name"] in rendered_text


def test_generate_streak_svg_validity_and_themes() -> None:
    """SVG output is valid XML and supports themes, gradients, and escaped text."""
    weekly_days: list[WeeklyDay] = [
        {
            "date": f"2026-10-{16 + index}",
            "day_name": "Day",
            "count": index,
            "is_active": index > 0,
            "is_today": index == 6,
        }
        for index in range(7)
    ]
    stats: dict[str, object] = {
        "name": "Tom <script> & Jerry",
        "current_streak": 7,
        "longest_streak": 20,
        "total_commits": 350,
        "is_active_today": True,
        "streak_message": "Streak active!",
        "weekly_days": weekly_days,
    }

    svg = generate_streak_svg(stats, theme_name="default", locale="en")
    root: ET.Element = ET.fromstring(svg)

    assert root.tag.endswith("svg")
    assert "Tom &lt;script&gt; &amp; Jerry" in svg
    assert "DAY STREAK" in svg

    svg_dracula = generate_streak_svg(stats, theme_name="dracula")
    assert ET.fromstring(svg_dracula).tag.endswith("svg")

    svg_gradient = generate_streak_svg(stats, theme_name="ambient_gradient")
    assert ET.fromstring(svg_gradient).tag.endswith("svg")
    assert 'linearGradient id="bg-gradient"' in svg_gradient

    svg_compact = generate_streak_svg(stats, hide_days=True)
    root_compact: ET.Element = ET.fromstring(svg_compact)

    assert int(root_compact.attrib["height"]) == 145
    assert 'rx="4.5"' in svg

    evil_svg = generate_streak_svg(stats, border_color_override="red;}</style><script>alert(1)</script><style>")
    assert "<script>" not in evil_svg
    assert "alert(1)" not in evil_svg


def test_streak_message_does_not_overlap_weekly_tracker() -> None:
    """The subtitle and weekly tracker remain separated in the SVG layout."""
    weekly_days: list[WeeklyDay] = [
        {
            "date": f"2026-10-{16 + index}",
            "day_name": f"Day{index}",
            "count": index,
            "is_active": True,
            "is_today": index == 6,
        }
        for index in range(7)
    ]
    streak_message = "Streak active! Flame is burning today"
    stats: dict[str, object] = {
        "name": "Octocat",
        "current_streak": 5,
        "longest_streak": 10,
        "total_commits": 100,
        "is_active_today": True,
        "streak_message": streak_message,
        "weekly_days": weekly_days,
    }

    svg = generate_streak_svg(stats, locale="en")
    root: ET.Element = ET.fromstring(svg)

    message_elements: list[ET.Element] = [
        element
        for element in root.iter()
        if element.tag.endswith("text")
        and element.attrib.get("class") == "streak-msg"
    ]

    assert len(message_elements) == 1
    message_element = message_elements[0]
    message_y = float(message_element.attrib["y"])

    assert message_y <= 55
    assert streak_message in (message_element.text or "")

    weekly_groups: list[ET.Element] = [
        element
        for element in root.iter()
        if element.tag.endswith("g")
        and element.attrib.get("class") == "weekly-tracker"
    ]

    assert len(weekly_groups) == 1
    weekly_group = weekly_groups[0]

    for child in weekly_group:
        transform = child.attrib.get("transform", "")
        if "translate" not in transform:
            continue

        coordinates = (
            transform.replace("translate(", "")
            .replace(")", "")
            .split(",")
        )
        y_value = float(coordinates[1].strip())

        assert y_value >= 140
        assert y_value - message_y >= 80
