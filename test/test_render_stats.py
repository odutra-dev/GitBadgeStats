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
