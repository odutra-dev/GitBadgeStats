"""Unit tests for StatsCardRenderer module."""

import xml.etree.ElementTree as ET
from src.renderers.stats_card import StatsCardRenderer, generate_svg


def test_generate_stats_svg_standard():
    """Verify SVG stats card rendering and XML validity."""
    stats = {
        "name": "Octocat",
        "total_commits": 250,
        "stars": 45,
        "total_prs": 12,
        "total_issues": 8,
        "contributed_to": 3,
    }
    svg = generate_svg(stats, theme_name="default")
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "Octocat's GitHub Stats" in svg
    assert "Total Commits:" in svg
    assert "GitHub Rank" in svg


def test_generate_stats_svg_hide_rank():
    """Verify hiding rank reduces card width."""
    stats = {"name": "Octocat"}
    svg = generate_svg(stats, hide_rank=True)
    root = ET.fromstring(svg)
    assert int(root.attrib["width"]) == 330
    assert "GitHub Rank" not in svg


def test_generate_stats_svg_locales():
    """Verify stats card labels render properly in all supported locales."""
    stats = {
        "name": "Octocat",
        "total_commits": 10,
        "stars": 5,
        "total_prs": 2,
        "total_issues": 1,
        "contributed_to": 4,
    }
    expected_phrases = {
        "pt": ("Estatísticas do GitHub de Octocat", "Total de commits:", "Rank GitHub"),
        "es": ("Estadísticas de GitHub de Octocat", "Commits totales:", "Rank GitHub"),
        "fr": ("Statistiques GitHub de Octocat", "Commits au total:", "Rang GitHub"),
        "de": ("GitHub-Statistiken von Octocat", "Commits insgesamt:", "GitHub-Rang"),
    }
    for locale, (title, commits_label, rank_title) in expected_phrases.items():
        svg = generate_svg(stats, locale=locale)
        assert title in svg
        assert commits_label in svg
        assert rank_title in svg


def test_generate_stats_svg_invalid_locale():
    """Verify ValueError when locale is unsupported."""
    import pytest
    with pytest.raises(ValueError, match="Unsupported locale 'ja'"):
        generate_svg({"name": "Octocat"}, locale="ja")


def test_generate_stats_svg_icons():
    """Verify all metric icons are rendered inside the SVG."""
    from src.common.icons import icons
    stats = {
        "name": "Octocat",
        "total_commits": 10,
        "stars": 5,
        "total_prs": 2,
        "total_issues": 1,
        "contributed_to": 4,
    }
    svg = generate_svg(stats)
    for key in ("commits", "star", "prs", "issues", "contribs"):
        assert icons[key] in svg
