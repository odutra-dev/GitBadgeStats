"""Common utilities, theme palettes, and SVG icons."""

from src.common.icons import icons
from src.common.themes import themes
from src.common.utils import format_color, parse_background, escape_text
from src.common.achievement_assets import (
    get_achievement_badge_data_uri,
    get_tier_style,
    TIER_COLORS,
)

__all__ = [
    "icons",
    "themes",
    "format_color",
    "parse_background",
    "escape_text",
    "get_achievement_badge_data_uri",
    "get_tier_style",
    "TIER_COLORS",
]
