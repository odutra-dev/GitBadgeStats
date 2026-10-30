"""Error SVG card renderer.

Adheres to Single Responsibility Principle (SRP): responsible solely for rendering a small
themed card with an alert icon, a title and an optional hint. Badges are consumed by <img>
tags, so errors must be images too, otherwise READMEs show a broken image with no explanation.
"""

from typing import Optional
from src.common.themes import themes
from src.common.utils import (
    format_color,
    parse_background,
    escape_text,
    sanitize_color,
    sanitize_background,
)


class ErrorCardRenderer:
    """Renderer for the error SVG card."""

    CARD_WIDTH = 400
    CARD_HEIGHT = 100
    CARD_RADIUS = 4.5
    MAX_TITLE_CHARS = 34
    MAX_HINT_CHARS = 52

    def __init__(
        self,
        title: str,
        hint: str = "",
        theme_name: str = "default",
        title_color_override: Optional[str] = None,
        text_color_override: Optional[str] = None,
        icon_color_override: Optional[str] = None,
        bg_color_override: Optional[str] = None,
        border_color_override: Optional[str] = None,
    ):
        self.title = escape_text(self._truncate(title, self.MAX_TITLE_CHARS))
        self.hint = escape_text(self._truncate(hint, self.MAX_HINT_CHARS))

        # Overrides come straight from the query string: only validated hex colors are used.
        theme = themes.get(theme_name, themes["default"])
        self.title_color = format_color(sanitize_color(title_color_override) or theme.get("title_color", "2f80ed"))
        self.text_color = format_color(sanitize_color(text_color_override) or theme.get("text_color", "333333"))
        self.icon_color = format_color(sanitize_color(icon_color_override) or theme.get("icon_color", "4c71f2"))

        raw_bg = sanitize_background(bg_color_override) or theme.get("bg_color", "fffefe")
        self.bg_defs, self.bg_fill = parse_background(raw_bg)

        raw_border = sanitize_color(border_color_override) or theme.get("border_color")
        self.border_color = format_color(raw_border) if raw_border else self.text_color

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        text = (text or "").strip()
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _render_icon(self) -> str:
        """Render a circled exclamation mark."""
        return f"""
        <g transform="translate(25, 40)">
            <circle cx="12" cy="12" r="10.5" fill="none" stroke="{self.icon_color}" stroke-width="2"/>
            <rect x="11" y="6" width="2" height="7" rx="1" fill="{self.icon_color}"/>
            <circle cx="12" cy="16.5" r="1.3" fill="{self.icon_color}"/>
        </g>
        """

    def render(self) -> str:
        """Render complete SVG error card."""
        title_y = 47 if self.hint else 56
        hint_svg = f'<text x="62" y="69" class="hint">{self.hint}</text>' if self.hint else ""

        return f"""<svg width="{self.CARD_WIDTH}" height="{self.CARD_HEIGHT}" viewBox="0 0 {self.CARD_WIDTH} {self.CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{self.title}">
        <title>{self.title}</title>
        <defs>
            {self.bg_defs}
        </defs>
        <style>
            .title {{ font: bold 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.title_color}; }}
            .hint {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; fill-opacity: 0.8; }}
        </style>

        <rect width="{self.CARD_WIDTH - 1}" height="{self.CARD_HEIGHT - 1}" x="0.5" y="0.5" rx="{self.CARD_RADIUS}" fill="{self.bg_fill}" stroke="{self.border_color}"/>

        {self._render_icon()}

        <text x="62" y="{title_y}" class="title">{self.title}</text>
        {hint_svg}
    </svg>"""


def generate_error_svg(
    title: str,
    hint: str = "",
    theme_name: str = "default",
    title_color_override: Optional[str] = None,
    text_color_override: Optional[str] = None,
    icon_color_override: Optional[str] = None,
    bg_color_override: Optional[str] = None,
    border_color_override: Optional[str] = None,
) -> str:
    """Generate SVG error card."""
    renderer = ErrorCardRenderer(
        title=title,
        hint=hint,
        theme_name=theme_name,
        title_color_override=title_color_override,
        text_color_override=text_color_override,
        icon_color_override=icon_color_override,
        bg_color_override=bg_color_override,
        border_color_override=border_color_override,
    )
    return renderer.render()
