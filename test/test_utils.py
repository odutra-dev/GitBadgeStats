"""Unit tests for color sanitizers in common.utils."""

from src.common.utils import sanitize_color, sanitize_background


def test_sanitize_color_accepts_hex_with_or_without_hash():
    assert sanitize_color("ff5555") == "ff5555"
    assert sanitize_color("#FF5555") == "FF5555"
    assert sanitize_color("f55") == "f55"
    assert sanitize_color("ffffff00") == "ffffff00"


def test_sanitize_color_rejects_non_hex_values():
    assert sanitize_color(None) is None
    assert sanitize_color("") is None
    assert sanitize_color("red") is None
    assert sanitize_color("12345") is None
    assert sanitize_color("ff5555;}") is None
    assert sanitize_color('ff5555" onload="alert(1)') is None
    assert sanitize_color("red;}</style><script>alert(1)</script>") is None


def test_sanitize_background_accepts_single_color_and_gradients():
    assert sanitize_background("ff0000") == "ff0000"
    assert sanitize_background("#ff0000") == "ff0000"
    assert sanitize_background("4158d0,c850c0") == "4158d0,c850c0"
    assert sanitize_background("35,4158d0,c850c0,ffcc70") == "35,4158d0,c850c0,ffcc70"
    assert sanitize_background("-45,ff0000,00ff00") == "-45,ff0000,00ff00"


def test_sanitize_background_rejects_any_invalid_part():
    assert sanitize_background(None) is None
    assert sanitize_background("") is None
    assert sanitize_background("35") is None
    assert sanitize_background("35,4158d0,notacolor") is None
    assert sanitize_background('35,4158d0,"/><script>alert(1)</script>') is None
