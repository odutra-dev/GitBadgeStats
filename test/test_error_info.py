"""Unit tests for error card descriptions."""

from src.domain.error_info import build_error_info, format_wait


def test_not_found_is_specific_and_cached_briefly():
    info = build_error_info(404)
    assert info.title == "User not found"
    assert info.cache_seconds == 300


def test_not_found_in_portuguese():
    assert build_error_info(404, locale="pt").title == "Usuário não encontrado"


def test_unknown_locale_falls_back_to_english():
    assert build_error_info(404, locale="xx").title == "User not found"


def test_rate_limit_shows_wait_time_and_clamps_cache_lifetime():
    short = build_error_info(429, retry_after=45)
    assert short.title == "GitHub rate limit reached"
    assert short.hint == "Try again in 45s."
    assert short.cache_seconds == 60

    medium = build_error_info(429, retry_after=120)
    assert medium.hint == "Try again in 2 min."
    assert medium.cache_seconds == 120

    long_wait = build_error_info(429, retry_after=5000)
    assert long_wait.hint == "Try again in 84 min."
    assert long_wait.cache_seconds == 900


def test_rate_limit_without_retry_after_uses_generic_wait():
    info = build_error_info(429)
    assert info.hint == "Try again in a few minutes."
    assert info.cache_seconds == 60


def test_server_side_errors_are_generic():
    for status in (401, 500, 502, 503):
        info = build_error_info(status)
        assert info.title == "Could not load GitHub data"
        assert info.cache_seconds == 60


def test_format_wait_rounds_up_to_minutes():
    assert format_wait(59) == "59s"
    assert format_wait(60) == "1 min"
    assert format_wait(61) == "2 min"
