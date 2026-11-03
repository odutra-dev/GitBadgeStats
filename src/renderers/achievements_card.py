"""GitHub Achievements SVG card renderer.

Adheres to Single Responsibility Principle (SRP): responsible solely for rendering
the user's achievements showcase SVG card with tier badges, theme styles, and locales.
"""

from typing import Any, Optional

from src.common.achievement_assets import (
    get_achievement_badge_data_uri,
    get_tier_style,
)
from src.common.icons import icons
from src.common.locales import get_achievements_translations
from src.common.themes import themes
from src.common.utils import (
    escape_text,
    format_color,
    parse_background,
    sanitize_background,
    sanitize_color,
)
from src.domain.achievements import ACHIEVEMENT_DEFINITIONS


class AchievementsCardRenderer:
    """Renderer for the GitHub achievements showcase SVG card."""

    CARD_WIDTH = 495
    CARD_RADIUS = 4.5
    MAX_TITLE_CHARS = 36
    MIN_NAME_CHARS = 8

    def __init__(
        self,
        data: dict[str, Any],
        theme_name: str = "default",
        locale: str = "en",
        show_locked: bool = True,
        show_progress: bool = False,
        hide: Optional[str] = None,
        title_color_override: Optional[str] = None,
        text_color_override: Optional[str] = None,
        icon_color_override: Optional[str] = None,
        bg_color_override: Optional[str] = None,
        border_color_override: Optional[str] = None,
        custom_title: Optional[str] = None,
    ):
        self.data = data
        self.locale = locale
        self.translations = get_achievements_translations(locale)
        self.show_locked = show_locked
        self.show_progress = show_progress
        self.custom_title = custom_title

        # Parsed exclusion set
        self.hidden_ids = {
            h.strip().lower().replace("_", "-")
            for h in hide.split(",")
            if h.strip()
        } if hide else set()

        # Theme and color overrides
        theme = themes.get(theme_name, themes["default"])
        self.title_color = format_color(
            sanitize_color(title_color_override) or theme.get("title_color", "2f80ed")
        )
        self.text_color = format_color(
            sanitize_color(text_color_override) or theme.get("text_color", "333333")
        )
        self.icon_color = format_color(
            sanitize_color(icon_color_override) or theme.get("icon_color", "4c71f2")
        )

        raw_bg = sanitize_background(bg_color_override) or theme.get("bg_color", "fffefe")
        self.bg_defs, self.bg_fill = parse_background(raw_bg)

        raw_border = sanitize_color(border_color_override) or theme.get("border_color")
        self.border_color = format_color(raw_border) if raw_border else self.text_color

        # Filter items to display
        all_items: list[dict[str, Any]] = self.data.get("achievements") or []
        visible: list[dict[str, Any]] = []
        for item in all_items:
            item_id = item.get("id", "").lower().replace("_", "-")
            if item_id in self.hidden_ids:
                continue
            if not self.show_locked and not item.get("unlocked", False):
                continue
            visible.append(item)

        self.items = visible
        self.total_unlocked = self.data.get("total_unlocked", 0)
        self.total_possible = self.data.get("total_possible", len(all_items))

        # Dynamic height based on row count and show_progress
        if not self.items:
            self.card_height = 140
        elif len(self.items) <= 4:
            self.card_height = 185 if self.show_progress else 150
        else:
            self.card_height = 275 if self.show_progress else 230

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        text = (text or "").strip()
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _title(self) -> str:
        """Build card title respecting custom title and character limits."""
        if self.custom_title and self.custom_title.strip():
            return escape_text(self._truncate(self.custom_title, self.MAX_TITLE_CHARS))

        template = self.translations["card_title"]
        name_limit = max(
            self.MIN_NAME_CHARS,
            self.MAX_TITLE_CHARS - len(template.format(name="")),
        )
        name = self._truncate(str(self.data.get("name") or "User"), name_limit)
        return escape_text(self._truncate(template.format(name=name), self.MAX_TITLE_CHARS))

    def _render_header(self) -> str:
        """Render header with trophy icon, title, and unlocked count pill."""
        title = self._title()
        unlocked_label = self.translations["unlocked_label"].upper()
        pill_text = f"{self.total_unlocked} / {self.total_possible} {unlocked_label}"

        return f"""
        <svg x="25" y="16" width="18" height="18" viewBox="0 0 16 16" fill="{self.icon_color}">
            {icons.get("trophy", "")}
        </svg>
        <text x="50" y="30" class="header">{title}</text>
        <g transform="translate({self.CARD_WIDTH - 150}, 15)">
            <rect width="125" height="20" rx="10" fill="{self.icon_color}" fill-opacity="0.12" stroke="{self.icon_color}" stroke-opacity="0.3" stroke-width="1"/>
            <text x="62.5" y="14" text-anchor="middle" class="pill-text" fill="{self.icon_color}">{escape_text(pill_text)}</text>
        </g>
        """

    def _render_achievement_item(self, item: dict[str, Any], cx: float, cy: float) -> str:
        """Render single circular achievement badge cell with tier overlay and name."""
        ach_id = item.get("id", "")
        unlocked = item.get("unlocked", False)
        tier = item.get("tier", "locked").lower()
        multiplier = item.get("multiplier", "")

        tier_style = get_tier_style(tier if unlocked else "locked")
        badge_uri = get_achievement_badge_data_uri(ach_id)

        # Localized achievement name
        localized_names = self.translations.get("achievements", {})
        display_name = localized_names.get(ach_id, item.get("name", ach_id.title()))
        escaped_name = escape_text(self._truncate(display_name, 15))

        # Tier badge label
        if not unlocked:
            tier_badge_text = self.translations["locked_label"]
            tier_text_color = "#8b949e"
        elif multiplier and multiplier != "x1":
            tier_badge_text = multiplier
            tier_text_color = "#ffffff"
        else:
            tier_key = f"tier_{tier}"
            tier_badge_text = self.translations.get(tier_key, tier.title())
            tier_text_color = "#ffffff"

        escaped_tier_text = escape_text(tier_badge_text)

        clip_id = f"clip-{ach_id}"
        badge_radius = 24
        img_size = badge_radius * 2

        locked_overlay = ""
        if not unlocked:
            locked_overlay = f"""
            <circle cx="{cx}" cy="{cy}" r="{badge_radius - 1}" fill="#0d1117" fill-opacity="0.6"/>
            <g transform="translate({cx - 7}, {cy - 7})" fill="#8b949e">
                <path fill-rule="evenodd" d="M4 4v2h-.5A1.5 1.5 0 002 7.5v6A1.5 1.5 0 003.5 15h9a1.5 1.5 0 001.5-1.5v-6A1.5 1.5 0 0012.5 6H12V4a4 4 0 00-8 0zm6.5 2V4a2.5 2.5 0 00-5 0v2h5z"/>
            </g>
            """

        opacity = "1.0" if unlocked else "0.45"

        progress_markup = ""
        if self.show_progress:
            defn = ACHIEVEMENT_DEFINITIONS.get(ach_id)
            is_max = (tier == "gold") or (defn is not None and len(defn.tiers) == 1 and unlocked)
            target_value = item.get("target_value", 1)
            current_value = item.get("current_value", 0)
            progress_pct = max(0.0, min(100.0, float(item.get("progress_percentage", 0.0))))
            remaining = max(0, target_value - current_value)

            bar_w = 48
            bar_h = 3
            bar_x = cx - bar_w / 2
            bar_y = cy + 49
            fill_w = round((progress_pct / 100.0) * bar_w, 1)

            if is_max:
                progress_label = self.translations.get("max_tier_label", "Max Tier")
            elif remaining == 1:
                progress_label = self.translations.get("remaining_single", "1 left")
            else:
                progress_label = self.translations.get("remaining_multiple", "{count} left").format(count=remaining)

            escaped_progress_label = escape_text(progress_label)
            bar_color = tier_style["border"] if unlocked else "#484f58"

            progress_markup = f"""
            <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="1.5" fill="{self.text_color}" fill-opacity="0.15"/>
            <rect x="{bar_x}" y="{bar_y}" width="{fill_w}" height="{bar_h}" rx="1.5" fill="{bar_color}"/>
            <text x="{cx}" y="{bar_y + 10.5}" text-anchor="middle" class="progress-text">{escaped_progress_label}</text>
            """

        name_y = cy + 40 if self.show_progress else cy + 43

        return f"""
        <g class="achievement-item" opacity="{opacity}">
            <defs>
                <clipPath id="{clip_id}">
                    <circle cx="{cx}" cy="{cy}" r="{badge_radius - 1}"/>
                </clipPath>
            </defs>
            <circle cx="{cx}" cy="{cy}" r="{badge_radius + 1}" fill="{tier_style['bg']}" stroke="{tier_style['border']}" stroke-width="2.5"/>
            <image href="{badge_uri}" x="{cx - badge_radius + 1}" y="{cy - badge_radius + 1}" width="{img_size - 2}" height="{img_size - 2}" clip-path="url(#{clip_id})"/>
            {locked_overlay}
            <g transform="translate({cx - 21}, {cy + 15})">
                <rect width="42" height="15" rx="7.5" fill="{tier_style['badge_bg']}" stroke="{tier_style['border']}" stroke-width="0.8"/>
                <text x="21" y="11" text-anchor="middle" class="tier-pill" fill="{tier_text_color}">{escaped_tier_text}</text>
            </g>
            <text x="{cx}" y="{name_y}" text-anchor="middle" class="ach-name">{escaped_name}</text>
            {progress_markup}
        </g>
        """

    def _render_empty(self) -> str:
        """Render empty state when no achievements match."""
        empty_text = escape_text(self.translations.get("empty_text", "No achievements unlocked yet"))
        cy = 85
        return f"""
        <text x="{self.CARD_WIDTH / 2}" y="{cy}" text-anchor="middle" class="empty-text">
            {empty_text}
        </text>
        """

    def _render_grid(self) -> str:
        """Render achievements in a 1-row or 2-row layout."""
        if not self.items:
            return self._render_empty()

        cells: list[str] = []
        n = len(self.items)

        if n <= 4:
            # Single row layout
            col_width = (self.CARD_WIDTH - 40) / n
            cy = 72 if self.show_progress else 82
            for i, item in enumerate(self.items):
                cx = 20 + col_width * (i + 0.5)
                cells.append(self._render_achievement_item(item, cx, cy))
        else:
            # 2 rows layout: 4 in row 1, rest in row 2 centered
            col_width = (self.CARD_WIDTH - 40) / 4
            cy1 = 66 if self.show_progress else 76
            cy2 = 166 if self.show_progress else 160

            # Row 1 (first 4 items)
            for i in range(4):
                cx = 20 + col_width * (i + 0.5)
                cells.append(self._render_achievement_item(self.items[i], cx, cy1))

            # Row 2 (items 4 to end, centered)
            remaining_count = n - 4
            row2_offset = 20 + ((4 - remaining_count) * col_width) / 2
            for j in range(remaining_count):
                cx = row2_offset + col_width * (j + 0.5)
                cells.append(self._render_achievement_item(self.items[4 + j], cx, cy2))

        return "".join(cells)

    def render(self) -> str:
        """Render complete SVG achievements showcase card."""
        title = self._title()
        header = self._render_header()
        grid = self._render_grid()

        disclaimer = ""
        if self.show_progress:
            disclaimer_text = escape_text(
                self.translations.get(
                    "estimate_disclaimer",
                    "* Progress is an estimate based on public GitHub activity.",
                )
            )
            disclaimer = f"""
        <text x="25" y="{self.card_height - 12}" class="disclaimer-text">{disclaimer_text}</text>
        """

        return f"""<svg width="{self.CARD_WIDTH}" height="{self.card_height}" viewBox="0 0 {self.CARD_WIDTH} {self.card_height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{title}">
        <title>{title}</title>
        <defs>
            {self.bg_defs}
        </defs>
        <style>
            .header {{ font: bold 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.title_color}; }}
            .pill-text {{ font: bold 9.5px 'Segoe UI', Ubuntu, Sans-Serif; letter-spacing: 0.5px; }}
            .ach-name {{ font: 600 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; }}
            .tier-pill {{ font: bold 9px 'Segoe UI', Ubuntu, Sans-Serif; letter-spacing: 0.3px; }}
            .progress-text {{ font: 600 8.5px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; opacity: 0.85; }}
            .disclaimer-text {{ font: 400 9px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; opacity: 0.6; }}
            .empty-text {{ font: 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; opacity: 0.7; }}
        </style>

        <rect width="{self.CARD_WIDTH - 1}" height="{self.card_height - 1}" x="0.5" y="0.5" rx="{self.CARD_RADIUS}" fill="{self.bg_fill}" stroke="{self.border_color}"/>

        {header}
        {grid}
        {disclaimer}
    </svg>"""


def generate_achievements_svg(
    data: dict[str, Any],
    theme_name: str = "default",
    locale: str = "en",
    show_locked: bool = True,
    show_progress: bool = False,
    hide: Optional[str] = None,
    title_color_override: Optional[str] = None,
    text_color_override: Optional[str] = None,
    icon_color_override: Optional[str] = None,
    bg_color_override: Optional[str] = None,
    border_color_override: Optional[str] = None,
    custom_title: Optional[str] = None,
) -> str:
    """Generate SVG achievements card based on data, theme, and parameters."""
    renderer = AchievementsCardRenderer(
        data=data,
        theme_name=theme_name,
        locale=locale,
        show_locked=show_locked,
        show_progress=show_progress,
        hide=hide,
        title_color_override=title_color_override,
        text_color_override=text_color_override,
        icon_color_override=icon_color_override,
        bg_color_override=bg_color_override,
        border_color_override=border_color_override,
        custom_title=custom_title,
    )
    return renderer.render()
