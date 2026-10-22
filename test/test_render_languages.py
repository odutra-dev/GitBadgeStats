"""Unit tests for LanguagesCardRenderer module."""

import xml.etree.ElementTree as ET
from src.renderers.languages_card import LanguagesCardRenderer, generate_languages_svg


def test_generate_languages_svg_standard():
    """Verify SVG languages card rendering, progress bar, and XML validity."""
    data = {
        "name": "Octocat",
        "languages": [
            {"name": "Python", "color": "#3572A5", "size": 3000, "percent": 50.0},
            {"name": "TypeScript", "color": "#3178c6", "size": 1800, "percent": 30.0},
            {"name": "HTML", "color": "#e34c26", "size": 600, "percent": 10.0},
            {"name": "CSS", "color": "#563d7c", "size": 360, "percent": 6.0},
            {"name": "Shell", "color": "#89e051", "size": 240, "percent": 4.0},
        ],
    }

    svg = generate_languages_svg(data, theme_name="dracula")
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert int(root.attrib["width"]) == 340
    assert int(root.attrib["height"]) == 165

    # Check title and language names
    assert "Most Used Languages" in svg or "Octocat's Top Languages" in svg
    assert "Python" in svg
    assert "50.0%" in svg or "50%" in svg
    assert "TypeScript" in svg
    assert "30.0%" in svg or "30%" in svg
    assert "HTML" in svg
    assert "CSS" in svg
    assert "Shell" in svg

    # Check progress bar elements
    assert "progress-bar-clip" in svg
    assert 'fill="#3572A5"' in svg
    assert 'fill="#3178c6"' in svg


def test_generate_languages_svg_empty_state():
    """Verify fallback message when no languages are present."""
    data = {"name": "EmptyUser", "languages": []}
    svg = generate_languages_svg(data)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "No languages found" in svg


def test_generate_languages_svg_custom_colors():
    """Verify custom colors and escaping."""
    data = {
        "name": "Special <>& Name",
        "languages": [
            {"name": "C# & C++", "color": "#178600", "size": 1000, "percent": 100.0}
        ],
    }
    svg = generate_languages_svg(
        data,
        title_color_override="ff0000",
        text_color_override="00ff00",
        bg_color_override="000000",
    )
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "C# &amp; C++" in svg
    assert "#ff0000" in svg
    assert "#00ff00" in svg
