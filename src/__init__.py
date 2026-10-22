"""GitBadgeStats package entrypoint."""

from src.common.icons import icons
from src.common.themes import themes
from src.common.utils import format_color, parse_background, escape_text
from src.domain.rank import calculate_rank
from src.domain.streak import StreakCalculator, calculate_streak_from_days
from src.domain.languages import LanguagesCalculator, calculate_top_languages
from src.services.cache import cache, CacheBackend, SimpleTTLCache
from src.services.github_client import GitHubGraphQLClient
from src.services.github_service import (
    fetch_github_stats,
    fetch_github_streak,
    fetch_github_top_languages,
)
from src.renderers.stats_card import StatsCardRenderer, generate_svg
from src.renderers.streak_card import StreakCardRenderer, generate_streak_svg
from src.renderers.languages_card import LanguagesCardRenderer, generate_languages_svg

__all__ = [
    "icons",
    "themes",
    "format_color",
    "parse_background",
    "escape_text",
    "calculate_rank",
    "StreakCalculator",
    "calculate_streak_from_days",
    "LanguagesCalculator",
    "calculate_top_languages",
    "cache",
    "CacheBackend",
    "SimpleTTLCache",
    "GitHubGraphQLClient",
    "fetch_github_stats",
    "fetch_github_streak",
    "fetch_github_top_languages",
    "StatsCardRenderer",
    "generate_svg",
    "StreakCardRenderer",
    "generate_streak_svg",
    "LanguagesCardRenderer",
    "generate_languages_svg",
]
