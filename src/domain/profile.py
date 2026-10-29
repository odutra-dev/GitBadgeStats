"""Profile card domain logic.

Adheres to Single Responsibility Principle (SRP): pure functions for account age
calculation and compact number formatting, with no I/O and no rendering concerns.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from src.common.locales import ProfileTranslations


@dataclass(frozen=True)
class AccountAge:
    """Whole years and remaining months since an account was created."""

    years: int
    months: int


def parse_created_date(created_at: Optional[str]) -> Optional[date]:
    """Parse a GitHub ISO-8601 timestamp (e.g. '2011-01-25T18:44:36Z') into a date."""
    if not created_at:
        return None
    try:
        return datetime.fromisoformat(str(created_at).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def calculate_account_age(created_at: Optional[str], today: date) -> Optional[AccountAge]:
    """Return the account age as whole years and months, or None for an invalid date.

    A creation date slightly in the future (clock skew) is clamped to zero months.
    """
    created = parse_created_date(created_at)
    if created is None:
        return None

    total_months = (today.year - created.year) * 12 + (today.month - created.month)
    if today.day < created.day:
        total_months -= 1

    years, months = divmod(max(total_months, 0), 12)
    return AccountAge(years=years, months=months)


def format_account_age(age: AccountAge, translations: ProfileTranslations) -> str:
    """Format an account age such as '3 years, 2 months' using locale unit names."""
    parts = []
    if age.years:
        unit = translations["year_one"] if age.years == 1 else translations["year_other"]
        parts.append(f"{age.years} {unit}")
    if age.months or not parts:
        unit = translations["month_one"] if age.months == 1 else translations["month_other"]
        parts.append(f"{age.months} {unit}")
    return translations["age_separator"].join(parts)


def format_compact_number(value: object) -> str:
    """Format a count compactly: 999 -> '999', 1234 -> '1.2k', 2500000 -> '2.5M'."""
    try:
        number = max(int(value), 0)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return "0"

    if number < 1000:
        return str(number)

    units = ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k"))
    for index, (divisor, suffix) in enumerate(units):
        if number >= divisor:
            scaled = round(number / divisor, 1)
            if scaled >= 1000 and index > 0:
                # Rounding pushed the value to the next unit (e.g. 999,960 -> 1M).
                divisor, suffix = units[index - 1]
                scaled = round(number / divisor, 1)
            return f"{scaled:.1f}".rstrip("0").rstrip(".") + suffix

    return str(number)