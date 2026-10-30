"""Unit tests for the error card renderer."""

from src.renderers.error_card import generate_error_svg

EVIL = 'red;}</style><script>alert(1)</script><style>'


def test_renders_title_and_hint():
    svg = generate_error_svg("User not found", "Check the username in the URL.")
    assert svg.startswith("<svg")
    assert "User not found" in svg
    assert "Check the username in the URL." in svg
    assert 'class="hint"' in svg


def test_hint_is_optional():
    svg = generate_error_svg("User not found")
    assert "User not found" in svg
    assert 'class="hint"' not in svg


def test_text_is_escaped():
    svg = generate_error_svg("<script>alert(1)</script>", "a & b")
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg
    assert "a &amp; b" in svg


def test_long_text_is_truncated():
    title = "x" * 80
    svg = generate_error_svg(title)
    assert title not in svg
    assert "…" in svg


def test_unknown_theme_falls_back_to_default():
    svg = generate_error_svg("User not found", theme_name="nonexistenttheme")
    assert "#2f80ed" in svg


def test_valid_color_overrides_are_applied():
    svg = generate_error_svg(
        "User not found",
        title_color_override="ff0000",
        bg_color_override="123456",
        border_color_override="00ff00",
    )
    assert "fill: #ff0000" in svg
    assert 'fill="#123456"' in svg
    assert 'stroke="#00ff00"' in svg


def test_gradient_background_is_supported():
    svg = generate_error_svg("User not found", bg_color_override="35,4158d0,c850c0")
    assert "linearGradient" in svg
    assert 'fill="url(#bg-gradient)"' in svg


def test_malicious_color_overrides_are_ignored():
    svg = generate_error_svg(
        "User not found",
        title_color_override=EVIL,
        text_color_override=EVIL,
        icon_color_override=EVIL,
        bg_color_override=EVIL,
        border_color_override=EVIL,
    )
    assert "<script>" not in svg
    assert "alert(1)" not in svg
    assert "fill: #2f80ed" in svg


def test_malicious_gradient_is_ignored():
    svg = generate_error_svg("User not found", bg_color_override='35,4158d0,"/><script>alert(1)</script>')
    assert "<script>" not in svg
    assert "linearGradient" not in svg
