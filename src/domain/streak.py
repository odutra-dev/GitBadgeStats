"""Domain logic for GitHub commit streaks and weekly activity tracking.

Adheres to Single Responsibility Principle (SRP): strictly responsible for
calculating streak metrics, handling timezone dates, and formatting localized status messages.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Any

from src.common.locales import LocaleTranslations
from src.common.locales import get_translations

class StreakCalculator:
    """Calculates commit streak metrics following Duolingo-style rules:

    - Active Today: If user committed today, flame is lit and today is counted.
    - Pending Today: If user committed yesterday but not today, streak remains valid from
      yesterday, but today's flame remains unlit until a commit is pushed.
    - Reset Rule: If a full day is missed (yesterday = 0 commits), streak resets to 0.
    - Historical Longest: Highest consecutive daily commits in the contribution calendar.
    - 7-Day Tracker: Rolling 7-day window with lit mini-flames on active days.
    """

    @classmethod
    def calculate(
        cls,
        all_days: list[dict],
        user_date: Optional[date] = None,
        locale: str = "en",
    ) -> dict:
        """Calculate streak statistics from daily contribution counts."""
        translations: LocaleTranslations = get_translations(locale)

        today: date = user_date or datetime.now(timezone.utc).date()
        day_map: dict[Any, Any] = {day["date"]: day["count"] for day in all_days}

        today_str = today.strftime("%Y-%m-%d")
        today_count = day_map.get(today_str, 0)
        is_active_today = today_count > 0

        yesterday: date = today - timedelta(days=1)
        yesterday_str: str = yesterday.strftime("%Y-%m-%d")
        yesterday_count: Any = day_map.get(yesterday_str, 0)

        # 1. Calculate the current streak.
        current_streak: int = 0

        if is_active_today:
            current_streak = 1
            check_date = yesterday

            while day_map.get(check_date.strftime("%Y-%m-%d"), 0) > 0:
                current_streak += 1
                check_date -= timedelta(days=1)

        elif yesterday_count > 0:
            current_streak = 1
            check_date = yesterday - timedelta(days=1)

            while day_map.get(check_date.strftime("%Y-%m-%d"), 0) > 0:
                current_streak += 1
                check_date -= timedelta(days=1)

        # 2. Calculate the longest historical streak.
        longest_streak: int = 0
        temp_streak: int = 0

        for day in sorted(all_days, key=lambda item: item["date"]):
            if day["count"] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        longest_streak = max(longest_streak, current_streak)

        # 3. Build the rolling 7-day activity tracker.
        weekday_names = translations["weekdays"]
        weekly_days = []

        for days_ago in reversed(range(7)):
            current_date = today - timedelta(days=days_ago)
            date_str = current_date.strftime("%Y-%m-%d")
            count = day_map.get(date_str, 0)

            weekly_days.append(
                {
                    "date": date_str,
                    "day_name": weekday_names[current_date.weekday()],
                    "count": count,
                    "is_active": count > 0,
                    "is_today": days_ago == 0,
                }
            )

        # 4. Build the localized status message.
        message = cls._build_status_message(
            is_active_today=is_active_today,
            current_streak=current_streak,
            locale=locale,
        )

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "is_active_today": is_active_today,
            "today_commits": today_count,
            "yesterday_commits": yesterday_count,
            "weekly_days": weekly_days,
            "streak_message": message,
        }

    @classmethod
    def _build_status_message(
        cls,
        is_active_today: bool,
        current_streak: int,
        locale: str,
    ) -> str:
        """Build the appropriate status message for the selected locale."""
        translations = get_translations(locale)

        if is_active_today:
            return translations["status_active"]

        if current_streak > 0:
            return translations["status_pending"]

        return translations["status_start"]


def calculate_streak_from_days(
    all_days: list[dict],
    user_date: Optional[date] = None,
    locale: str = "en",
) -> dict:
    """Functional shortcut for StreakCalculator.calculate."""
    return StreakCalculator.calculate(
        all_days,
        user_date=user_date,
        locale=locale,
    )
