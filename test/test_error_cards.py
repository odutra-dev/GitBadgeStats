"""Unit tests for the error card service."""

from src.services.error_cards import build_error_card, parse_retry_after


def test_builds_not_found_card():
    card = build_error_card(404, None, {})
    assert "User not found" in card.svg
    assert card.cache_seconds == 300


def test_card_follows_theme_colors_and_locale_from_query():
    card = build_error_card(
        404, None, {"locale": "pt", "bg_color": "123456", "title_color": "ff0000"}
    )
    assert "Usuário não encontrado" in card.svg
    assert 'fill="#123456"' in card.svg
    assert "fill: #ff0000" in card.svg


def test_rate_limit_card_uses_retry_after_header():
    card = build_error_card(429, {"Retry-After": "90"}, {})
    assert "GitHub rate limit reached" in card.svg
    assert "2 min" in card.svg
    assert card.cache_seconds == 90


def test_invalid_locale_falls_back_to_english():
    card = build_error_card(404, None, {"locale": '"><script>'})
    assert "User not found" in card.svg
    assert "<script>" not in card.svg


def test_parse_retry_after():
    assert parse_retry_after({"Retry-After": "30"}) == 30
    assert parse_retry_after({"retry-after": "30"}) == 30
    assert parse_retry_after({"Retry-After": "soon"}) is None
    assert parse_retry_after({}) is None
    assert parse_retry_after(None) is None
