"""Domain logic for GitHub commit streaks and weekly activity tracking.

Adheres to Single Responsibility Principle (SRP): strictly responsible for
calculating streak metrics, handling timezone dates, and formatting localized status messages.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional


class StreakCalculator:
    """Calculates commit streak metrics following Duolingo-style rules:

    - Active Today: If user committed today, flame is lit and today is counted.
    - Pending Today: If user committed yesterday but not today, streak remains valid from
      yesterday, but today's flame remains unlit until a commit is pushed.
    - Reset Rule: If a full day is missed (yesterday = 0 commits), streak resets to 0.
    - Historical Longest: Highest consecutive daily commits in the contribution calendar.
    - 7-Day Tracker: Rolling 7-day window with lit mini-flames on active days.
    """

    WEEKDAY_LABELS = {
        "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "pt": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
    }

    @classmethod
    def calculate(
        cls,
        all_days: list[dict],
        user_date: Optional[date] = None,
        locale: str = "en",
    ) -> dict:
        """Calculate streak statistics from daily contribution counts."""
        today = user_date or datetime.now(timezone.utc).date()
        day_map = {d["date"]: d["count"] for d in all_days}

        today_str = today.strftime("%Y-%m-%d")
        today_count = day_map.get(today_str, 0)
        is_active_today = today_count > 0

        yesterday = today - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        yesterday_count = day_map.get(yesterday_str, 0)

        # 1. Current streak calculation
        current_streak = 0
        if is_active_today:
            current_streak = 1
            check_date = yesterday
            while True:
                c = day_map.get(check_date.strftime("%Y-%m-%d"), 0)
                if c > 0:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
        else:
            if yesterday_count > 0:
                current_streak = 1
                check_date = yesterday - timedelta(days=1)
                while True:
                    c = day_map.get(check_date.strftime("%Y-%m-%d"), 0)
                    if c > 0:
                        current_streak += 1
                        check_date -= timedelta(days=1)
                    else:
                        break
            else:
                current_streak = 0

        # 2. Historical longest streak calculation
        longest_streak = 0
        temp_streak = 0
        sorted_days = sorted(all_days, key=lambda x: x["date"])
        for d in sorted_days:
            if d["count"] > 0:
                temp_streak += 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak
            else:
                temp_streak = 0

        longest_streak = max(longest_streak, current_streak)

        # 3. 7-day weekly tracker
        weekday_names = cls.WEEKDAY_LABELS.get(locale, cls.WEEKDAY_LABELS["en"])
        weekly_days = []
        for i in reversed(range(7)):
            d = today - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            cnt = day_map.get(d_str, 0)
            weekly_days.append({
                "date": d_str,
                "day_name": weekday_names[d.weekday()],
                "count": cnt,
                "is_active": cnt > 0,
                "is_today": (i == 0),
            })

        # 4. Contextual status message
        message = cls._build_status_message(is_active_today, current_streak, locale)

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
    def _build_status_message(cls, is_active_today: bool, current_streak: int, locale: str) -> str:
        if is_active_today:
            return "Ofensiva mantida! Chama acesa hoje" if locale == "pt" else "Streak active! Flame is burning today"
        if current_streak > 0:
            return "Chama apagada • Faça um commit hoje!" if locale == "pt" else "Flame unlit • Commit today to keep your streak!"
        return "Chama apagada • Faça um commit para iniciar!" if locale == "pt" else "Flame unlit • Commit to start your streak!"


def calculate_streak_from_days(
    all_days: list[dict],
    user_date: Optional[date] = None,
    locale: str = "en",
) -> dict:
    """Functional shortcut for StreakCalculator.calculate."""
    return StreakCalculator.calculate(all_days, user_date=user_date, locale=locale)
