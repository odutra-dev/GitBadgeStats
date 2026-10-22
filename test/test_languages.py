"""Unit tests for top languages domain logic."""

import pytest
from src.domain.languages import LanguagesCalculator, calculate_top_languages


def test_calculate_top_languages_basic():
    """Verify aggregation of languages across repositories."""
    repos = [
        {
            "name": "repo1",
            "languages": {
                "edges": [
                    {"size": 1000, "node": {"name": "Python", "color": "#3572A5"}},
                    {"size": 500, "node": {"name": "JavaScript", "color": "#f1e05a"}},
                ]
            },
        },
        {
            "name": "repo2",
            "languages": {
                "edges": [
                    {"size": 1000, "node": {"name": "Python", "color": "#3572A5"}},
                    {"size": 500, "node": {"name": "TypeScript", "color": "#3178c6"}},
                ]
            },
        },
    ]

    result = LanguagesCalculator.calculate_top_languages(repos, top_n=5)
    assert len(result) == 3

    # Python: 2000 / 3000 = 66.67%
    # JavaScript: 500 / 3000 = 16.67%
    # TypeScript: 500 / 3000 = 16.67%
    assert result[0]["name"] == "Python"
    assert result[0]["size"] == 2000
    assert result[0]["percent"] == 66.67
    assert result[0]["color"] == "#3572A5"

    assert result[1]["name"] in ("JavaScript", "TypeScript")
    assert result[1]["percent"] == 16.67


def test_calculate_top_languages_top_5_limit():
    """Verify that only top 5 languages are returned when more exist."""
    repos = [
        {
            "name": "polyglot",
            "languages": {
                "edges": [
                    {"size": 600, "node": {"name": "Lang1", "color": "#111111"}},
                    {"size": 500, "node": {"name": "Lang2", "color": "#222222"}},
                    {"size": 400, "node": {"name": "Lang3", "color": "#333333"}},
                    {"size": 300, "node": {"name": "Lang4", "color": "#444444"}},
                    {"size": 200, "node": {"name": "Lang5", "color": "#555555"}},
                    {"size": 100, "node": {"name": "Lang6", "color": "#666666"}},
                    {"size": 50, "node": {"name": "Lang7", "color": "#777777"}},
                ]
            },
        }
    ]

    result = calculate_top_languages(repos, top_n=5)
    assert len(result) == 5
    assert [r["name"] for r in result] == ["Lang1", "Lang2", "Lang3", "Lang4", "Lang5"]
    # Total of all 7 languages = 2150
    # Lang1: 600 / 2150 = 27.91%
    assert result[0]["percent"] == 27.91


def test_calculate_top_languages_exclude_language():
    """Verify excluded languages are filtered out and percentages re-proportioned."""
    repos = [
        {
            "name": "web-app",
            "languages": {
                "edges": [
                    {"size": 1000, "node": {"name": "Python", "color": "#3572A5"}},
                    {"size": 1000, "node": {"name": "HTML", "color": "#e34c26"}},
                ]
            },
        }
    ]

    result = LanguagesCalculator.calculate_top_languages(repos, exclude_languages={"html"})
    assert len(result) == 1
    assert result[0]["name"] == "Python"
    assert result[0]["percent"] == 100.0


def test_calculate_top_languages_exclude_repo():
    """Verify repositories can be excluded by name."""
    repos = [
        {
            "name": "ignored-repo",
            "languages": {
                "edges": [
                    {"size": 5000, "node": {"name": "C++", "color": "#f34b7d"}},
                ]
            },
        },
        {
            "name": "main-repo",
            "languages": {
                "edges": [
                    {"size": 1000, "node": {"name": "Python", "color": "#3572A5"}},
                ]
            },
        },
    ]

    result = LanguagesCalculator.calculate_top_languages(repos, exclude_repos={"ignored-repo"})
    assert len(result) == 1
    assert result[0]["name"] == "Python"
    assert result[0]["percent"] == 100.0


def test_calculate_top_languages_empty():
    """Verify empty repositories or zero size returns empty list without error."""
    assert LanguagesCalculator.calculate_top_languages([]) == []
    assert LanguagesCalculator.calculate_top_languages([{"name": "empty", "languages": {"edges": []}}]) == []
