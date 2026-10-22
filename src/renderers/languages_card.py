"""GitHub top languages SVG card renderer.

Adheres to Single Responsibility Principle (SRP): responsible solely for rendering
the top languages badge SVG with a proportional distribution bar and 2-column language list.
"""

from typing import Optional
from src.common.themes import themes
from src.common.utils import format_color, parse_background, escape_text


class LanguagesCardRenderer:
    """Renderer for top languages SVG badge card."""

    CARD_WIDTH = 340
    CARD_HEIGHT = 165
    BAR_X = 25
    BAR_Y = 54
    BAR_WIDTH = 290
    BAR_HEIGHT = 8

    def __init__(
        self,
        data: dict,
        theme_name: str = "default",
        title_color_override: Optional[str] = None,
        text_color_override: Optional[str] = None,
        bg_color_override: Optional[str] = None,
        border_color_override: Optional[str] = None,
        hide_title: bool = False,
        custom_title: Optional[str] = None,
    ):
        self.data = data
        self.languages = data.get("languages", [])
        self.name = escape_text(data.get("name", "User"))
        self.hide_title = hide_title
        self.custom_title = custom_title

        theme = themes.get(theme_name, themes["default"])
        self.title_color = format_color(title_color_override or theme.get("title_color", "2f80ed"))
        self.text_color = format_color(text_color_override or theme.get("text_color", "333333"))

        raw_bg = bg_color_override or theme.get("bg_color", "fffefe")
        self.bg_defs, self.bg_fill = parse_background(raw_bg)

        raw_border = border_color_override or theme.get("border_color")
        self.border_color = format_color(raw_border) if raw_border else self.text_color

    def _render_progress_bar(self) -> str:
        """Render segmented horizontal progress bar clipped to rounded corners."""
        if not self.languages:
            return ""

        segments = []
        current_x = self.BAR_X
        remaining_width = self.BAR_WIDTH

        for i, lang in enumerate(self.languages):
            pct = lang.get("percent", 0.0)
            if i == len(self.languages) - 1:
                seg_w = max(0.0, remaining_width)
            else:
                seg_w = round((pct / 100.0) * self.BAR_WIDTH, 1)
                remaining_width -= seg_w

            color = lang.get("color", "#858585")
            segments.append(
                f'<rect x="{current_x}" y="{self.BAR_Y}" width="{seg_w}" height="{self.BAR_HEIGHT}" fill="{color}"/>'
            )
            current_x += seg_w

        return f"""
        <g clip-path="url(#progress-bar-clip)">
            {''.join(segments)}
        </g>
        """

    def _render_languages_list(self) -> str:
        """Render 2-column language items with colored dots and percentages."""
        if not self.languages:
            return f'<text x="25" y="90" font-family="\'Segoe UI\', Ubuntu, Sans-Serif" font-size="12" fill="{self.text_color}" opacity="0.6">No languages found</text>'

        items = []
        for i, lang in enumerate(self.languages):
            col = i % 2
            row = i // 2

            col_x = 25 if col == 0 else 175
            row_y = 85 + row * 25

            color = lang.get("color", "#858585")
            raw_name = lang.get("name", "Unknown")
            display_name = raw_name if len(raw_name) <= 12 else raw_name[:11] + "…"
            name = escape_text(display_name)
            percent = f"{lang.get('percent', 0.0):.1f}%"

            item = f"""
            <g transform="translate({col_x}, {row_y})">
                <circle cx="5" cy="-4" r="5" fill="{color}"/>
                <text x="16" y="0" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="11" font-weight="600" fill="{self.text_color}">{name} <tspan font-weight="400" fill-opacity="0.75">{percent}</tspan></text>
            </g>
            """
            items.append(item)

        return "".join(items)

    def render(self) -> str:
        """Render complete SVG Top Languages card."""
        card_title = escape_text(self.custom_title) if self.custom_title else "Most Used Languages"
        progress_bar_svg = self._render_progress_bar()
        languages_list_svg = self._render_languages_list()

        return f"""<svg width="{self.CARD_WIDTH}" height="{self.CARD_HEIGHT}" viewBox="0 0 {self.CARD_WIDTH} {self.CARD_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            {self.bg_defs}
            <clipPath id="progress-bar-clip">
                <rect x="{self.BAR_X}" y="{self.BAR_Y}" width="{self.BAR_WIDTH}" height="{self.BAR_HEIGHT}" rx="4"/>
            </clipPath>
        </defs>
        <style>
            .header {{ font: bold 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.title_color}; }}
        </style>
        
        <rect width="{self.CARD_WIDTH - 1}" height="{self.CARD_HEIGHT - 1}" x="0.5" y="0.5" rx="6" fill="{self.bg_fill}" stroke="{self.border_color}"/>
        
        <text x="25" y="34" class="header">{card_title}</text>
        
        {progress_bar_svg}
        
        {languages_list_svg}
    </svg>"""


def generate_languages_svg(
    data: dict,
    theme_name: str = "default",
    title_color_override: Optional[str] = None,
    text_color_override: Optional[str] = None,
    bg_color_override: Optional[str] = None,
    border_color_override: Optional[str] = None,
    hide_title: bool = False,
    custom_title: Optional[str] = None,
) -> str:
    """Generate SVG Top Languages card."""
    renderer = LanguagesCardRenderer(
        data=data,
        theme_name=theme_name,
        title_color_override=title_color_override,
        text_color_override=text_color_override,
        bg_color_override=bg_color_override,
        border_color_override=border_color_override,
        hide_title=hide_title,
        custom_title=custom_title,
    )
    return renderer.render()
