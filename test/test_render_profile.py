"""Unit tests for the profile card renderer."""

import html
import re
from datetime import date

import pytest

from src.common.icons import icons
from src.common.locales import PROFILE_TRANSLATIONS
from src.renderers.profile_card import generate_profile_svg

TODAY = date(2026, 10, 27)
EVIL = "red;}</style><script>alert(1)</script><style>"

PROFILE = {
    "name": "The Octocat",
    "login": "octocat",
    "created_at": "2011-01-25T18:44:36Z",
    "followers": 21400,
    "following": 9,
    "repositories": 8,
    "stars": 15300,
}


def render(data: dict | None = None, **kwargs: object) -> str:
    return generate_profile_svg(PROFILE if data is None else data, today=TODAY, **kwargs)


def card_title(svg: str) -> str:
    match = re.search(r"<title>(.*?)</title>", svg)
    assert match is not None
    return html.unescape(match.group(1))


def test_renders_every_metric() -> None:
    svg = render()
    assert svg.startswith("<svg")
    for expected in (
        "Followers",
        "21.4k",
        "Following",
        "Repositories",
        "Stars",
        "15.3k",
        "Account age",
        "15 years, 9 months",
    ):
        assert expected in svg


def test_renders_one_icon_per_metric() -> None:
    svg = render()
    assert svg.count('viewBox="0 0 16 16"') == 5
    for key in ("followers", "following", "repo", "star", "calendar"):
        assert icons[key] in svg


def test_default_title_uses_the_user_name() -> None:
    assert card_title(render()) == "The Octocat's GitHub Profile"


def test_custom_title_replaces_the_default() -> None:
    assert card_title(render(custom_title="My business card")) == "My business card"


def test_blank_custom_title_falls_back_to_default() -> None:
    assert card_title(render(custom_title="   ")) == "The Octocat's GitHub Profile"


def test_portuguese_locale() -> None:
    svg = render(locale="pt")
    assert card_title(svg) == "Perfil GitHub de The Octocat"
    assert "Seguidores" in svg
    assert "15 anos e 9 meses" in svg


def test_unsupported_locale_raises_value_error() -> None:
    with pytest.raises(ValueError):
        render(locale="xx")


def test_missing_data_renders_zeros_and_placeholder() -> None:
    svg = render({})
    assert card_title(svg) == "User's GitHub Profile"
    assert svg.count(">0<") == 4
    assert "—" in svg


def test_invalid_creation_date_renders_placeholder() -> None:
    assert "—" in render({**PROFILE, "created_at": "not-a-date"})


def test_default_today_is_used_when_not_provided() -> None:
    assert "years" in generate_profile_svg(PROFILE)


def test_name_is_escaped() -> None:
    svg = render({**PROFILE, "name": "<script>alert(1)</script>"})
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg


def test_custom_title_is_escaped() -> None:
    svg = render(custom_title="<img src=x onerror=alert(1)>")
    assert "<img" not in svg


@pytest.mark.parametrize("locale", sorted(PROFILE_TRANSLATIONS))
def test_title_stays_within_the_card_for_long_names(locale: str) -> None:
    svg = render({**PROFILE, "name": "Maximiliane Wolfgang-Schmidt Ferreira"}, locale=locale)
    title = card_title(svg)
    assert len(title) <= 34
    assert "…" in title


def test_long_custom_title_is_truncated() -> None:
    title = card_title(render(custom_title="x" * 80))
    assert len(title) == 34
    assert title.endswith("…")


def test_valid_color_overrides_are_applied() -> None:
    svg = render(
        title_color_override="ff0000",
        text_color_override="0000ff",
        icon_color_override="00ff00",
        bg_color_override="123456",
        border_color_override="abcdef",
    )
    assert "fill: #ff0000" in svg
    assert "fill: #0000ff" in svg
    assert 'fill="#00ff00"' in svg
    assert 'fill="#123456"' in svg
    assert 'stroke="#abcdef"' in svg


def test_gradient_background_is_supported() -> None:
    svg = render(bg_color_override="35,4158d0,c850c0")
    assert "linearGradient" in svg
    assert 'fill="url(#bg-gradient)"' in svg


def test_unknown_theme_falls_back_to_default() -> None:
    assert "fill: #2f80ed" in render(theme_name="nonexistenttheme")


def test_malicious_color_overrides_are_ignored() -> None:
    svg = render(
        title_color_override=EVIL,
        text_color_override=EVIL,
        icon_color_override=EVIL,
        bg_color_override=EVIL,
        border_color_override=EVIL,
    )
    assert "<script>" not in svg
    assert "alert(1)" not in svg
    assert "fill: #2f80ed" in svg