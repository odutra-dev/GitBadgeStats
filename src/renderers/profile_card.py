"""GitHub profile SVG card renderer.

Adheres to Single Responsibility Principle (SRP): responsible solely for rendering the
profile summary badge (followers, following, repositories, stars and account age).
"""

from datetime import date, datetime, timezone
from typing import Optional

from src.common.icons import icons
from src.common.locales import get_profile_translations
from src.common.themes import themes
from src.common.utils import (
    escape_text,
    format_color,
    parse_background,
    sanitize_background,
    sanitize_color,
)
from src.domain.profile import (
    calculate_account_age,
    format_account_age,
    format_compact_number,
)


class ProfileCardRenderer:
    """Renderer for the GitHub profile summary SVG card."""

    CARD_WIDTH = 400
    CARD_HEIGHT = 230
    CARD_RADIUS = 4.5
    MAX_TITLE_CHARS = 34
    MIN_NAME_CHARS = 8
    EMPTY_VALUE = "—"

    def __init__(
        self,
        data: dict,
        theme_name: str = "default",
        locale: str = "en",
        title_color_override: Optional[str] = None,
        text_color_override: Optional[str] = None,
        icon_color_override: Optional[str] = None,
        bg_color_override: Optional[str] = None,
        border_color_override: Optional[str] = None,
        custom_title: Optional[str] = None,
        today: Optional[date] = None,
    ):
        self.data = data
        self.translations = get_profile_translations(locale)
        self.custom_title = custom_title
        self.today = today or datetime.now(timezone.utc).date()

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

    def _title(self) -> str:
        """Build the escaped card title from the custom title or the localized default.

        The title must fit the card width, so the user's name is shortened to whatever space
        the localized template leaves over.
        """
        if self.custom_title and self.custom_title.strip():
            return escape_text(self._truncate(self.custom_title, self.MAX_TITLE_CHARS))

        template = self.translations["card_title"]
        name_limit = max(self.MIN_NAME_CHARS, self.MAX_TITLE_CHARS - len(template.format(name="")))
        name = self._truncate(str(self.data.get("name") or "User"), name_limit)
        return escape_text(self._truncate(template.format(name=name), self.MAX_TITLE_CHARS))

    def _account_age_text(self) -> str:
        age = calculate_account_age(self.data.get("created_at"), self.today)
        if age is None:
            return self.EMPTY_VALUE
        return escape_text(format_account_age(age, self.translations))

    def _rows(self) -> list[tuple[str, str, str]]:
        """Return (icon name, label, display value) for each metric row."""
        t = self.translations
        return [
            ("followers", t["followers_label"], format_compact_number(self.data.get("followers"))),
            ("following", t["following_label"], format_compact_number(self.data.get("following"))),
            ("repo", t["repositories_label"], format_compact_number(self.data.get("repositories"))),
            ("star", t["stars_label"], format_compact_number(self.data.get("stars"))),
            ("calendar", t["account_age_label"], self._account_age_text()),
        ]

    def _render_row(self, index: int, icon_name: str, label: str, value: str) -> str:
        """Render one icon + label + value row, aligned with the stats card grid."""
        icon_y = 61 + index * 30
        text_y = 75 + index * 30
        return f"""
        <svg x="25" y="{icon_y}" width="16" height="16" viewBox="0 0 16 16" fill="{self.icon_color}">
            {icons.get(icon_name, "")}
        </svg>
        <text x="50" y="{text_y}" class="stat">{escape_text(label)}: <tspan class="bold" x="190">{value}</tspan></text>
        """

    def render(self) -> str:
        """Render complete SVG profile card."""
        title = self._title()
        rows = "".join(
            self._render_row(index, icon_name, label, value)
            for index, (icon_name, label, value) in enumerate(self._rows())
        )

        return f"""<svg width="{self.CARD_WIDTH}" height="{self.CARD_HEIGHT}" viewBox="0 0 {self.CARD_WIDTH} {self.CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">
        <title>{title}</title>
        <defs>
            {self.bg_defs}
        </defs>
        <style>
            .header {{ font: bold 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.title_color}; }}
            .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; }}
            .bold {{ font-weight: bold; }}
        </style>

        <rect width="{self.CARD_WIDTH - 1}" height="{self.CARD_HEIGHT - 1}" x="0.5" y="0.5" rx="{self.CARD_RADIUS}" fill="{self.bg_fill}" stroke="{self.border_color}"/>

        <text x="25" y="35" class="header">{title}</text>
        {rows}
    </svg>"""


def generate_profile_svg(
    data: dict,
    theme_name: str = "default",
    locale: str = "en",
    title_color_override: Optional[str] = None,
    text_color_override: Optional[str] = None,
    icon_color_override: Optional[str] = None,
    bg_color_override: Optional[str] = None,
    border_color_override: Optional[str] = None,
    custom_title: Optional[str] = None,
    today: Optional[date] = None,
) -> str:
    """Generate SVG profile card based on profile data, theme and locale."""
    renderer = ProfileCardRenderer(
        data=data,
        theme_name=theme_name,
        locale=locale,
        title_color_override=title_color_override,
        text_color_override=text_color_override,
        icon_color_override=icon_color_override,
        bg_color_override=bg_color_override,
        border_color_override=border_color_override,
        custom_title=custom_title,
        today=today,
    )
    return renderer.render()