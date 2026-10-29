"""Unit tests for profile card domain logic and translations."""

from datetime import date

import pytest

from src.common.locales import PROFILE_TRANSLATIONS, TRANSLATIONS, get_profile_translations
from src.domain.profile import (
    AccountAge,
    calculate_account_age,
    format_account_age,
    format_compact_number,
    parse_created_date,
)

TODAY = date(2026, 10, 27)


def test_parse_created_date_accepts_github_timestamp() -> None:
    assert parse_created_date("2011-01-25T18:44:36Z") == date(2011, 1, 25)


@pytest.mark.parametrize("value", [None, "", "yesterday", "2011-13-45"])
def test_parse_created_date_rejects_invalid_values(value: str | None) -> None:
    assert parse_created_date(value) is None


def test_account_age_counts_whole_years_and_months() -> None:
    assert calculate_account_age("2011-01-25T18:44:36Z", TODAY) == AccountAge(15, 9)


def test_account_age_does_not_count_an_unfinished_month() -> None:
    assert calculate_account_age("2011-01-28T00:00:00Z", TODAY) == AccountAge(15, 8)


def test_account_age_on_exact_anniversary() -> None:
    assert calculate_account_age("2025-10-27T00:00:00Z", TODAY) == AccountAge(1, 0)


def test_account_age_of_a_new_account_is_zero_months() -> None:
    assert calculate_account_age("2026-10-01T00:00:00Z", TODAY) == AccountAge(0, 0)


def test_account_age_clamps_future_creation_date_to_zero() -> None:
    assert calculate_account_age("2026-12-01T00:00:00Z", TODAY) == AccountAge(0, 0)


def test_account_age_is_none_for_invalid_date() -> None:
    assert calculate_account_age("not-a-date", TODAY) is None
    assert calculate_account_age(None, TODAY) is None


@pytest.mark.parametrize(
    ("locale", "age", "expected"),
    [
        ("en", AccountAge(1, 1), "1 year, 1 month"),
        ("en", AccountAge(3, 0), "3 years"),
        ("en", AccountAge(0, 5), "5 months"),
        ("en", AccountAge(0, 0), "0 months"),
        ("pt", AccountAge(2, 3), "2 anos e 3 meses"),
        ("es", AccountAge(1, 2), "1 año y 2 meses"),
        ("fr", AccountAge(2, 1), "2 ans et 1 mois"),
        ("de", AccountAge(1, 0), "1 Jahr"),
    ],
)
def test_format_account_age_uses_locale_units(locale: str, age: AccountAge, expected: str) -> None:
    assert format_account_age(age, get_profile_translations(locale)) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0"),
        (999, "999"),
        (1000, "1k"),
        (1234, "1.2k"),
        (15300, "15.3k"),
        (999_940, "999.9k"),
        (999_960, "1M"),
        (1_000_000, "1M"),
        (2_500_000, "2.5M"),
        (999_999_999, "1B"),
        (1_000_000_000, "1B"),
        ("12", "12"),
        (None, "0"),
        ("abc", "0"),
        (-5, "0"),
    ],
)
def test_format_compact_number(value: object, expected: str) -> None:
    assert format_compact_number(value) == expected


def test_profile_locales_define_the_same_keys() -> None:
    expected = set(PROFILE_TRANSLATIONS["en"])
    for locale, translations in PROFILE_TRANSLATIONS.items():
        assert set(translations) == expected, locale


def test_profile_locales_match_streak_locales() -> None:
    assert set(PROFILE_TRANSLATIONS) == set(TRANSLATIONS)


def test_profile_card_titles_have_a_name_placeholder() -> None:
    for locale, translations in PROFILE_TRANSLATIONS.items():
        assert "{name}" in translations["card_title"], locale


def test_unsupported_profile_locale_raises_value_error() -> None:
    with pytest.raises(ValueError):
        get_profile_translations("xx")