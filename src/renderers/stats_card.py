"""GitHub profile stats SVG card renderer.

Adheres to Single Responsibility Principle (SRP): responsible solely for rendering
the profile statistics badge SVG with dynamic rank gauge, icons, and theme styles.
"""

import math
from typing import Optional
from src.common.themes import themes
from src.common.icons import icons
from src.domain.rank import calculate_rank
from src.common.utils import format_color, parse_background, escape_text


class StatsCardRenderer:
    """Renderer for general GitHub profile statistics SVG card."""

    def __init__(
        self,
        stats: dict,
        theme_name: str = "default",
        hide_rank: bool = False,
        title_color_override: Optional[str] = None,
        text_color_override: Optional[str] = None,
        icon_color_override: Optional[str] = None,
        bg_color_override: Optional[str] = None,
        border_color_override: Optional[str] = None,
    ):
        self.stats = stats
        self.hide_rank = hide_rank

        theme = themes.get(theme_name, themes["default"])
        self.title_color = format_color(title_color_override or theme.get("title_color", "2f80ed"))
        self.text_color = format_color(text_color_override or theme.get("text_color", "333333"))
        self.icon_color = format_color(icon_color_override or theme.get("icon_color", "4c71f2"))

        raw_bg = bg_color_override or theme.get("bg_color", "fffefe")
        self.bg_defs, self.bg_fill = parse_background(raw_bg)

        raw_border = border_color_override or theme.get("border_color")
        self.border_color = format_color(raw_border) if raw_border else self.text_color
        self.display_name = escape_text(stats.get("name", "User"))

    def _render_icon(self, icon_name: str, y_pos: int) -> str:
        """Helper to render an icon with current theme icon color."""
        path = icons.get(icon_name, "")
        return f"""
        <svg x="25" y="{y_pos}" width="16" height="16" viewBox="0 0 16 16" fill="{self.icon_color}">
            {path}
        </svg>
        """

    def _render_rank(self) -> str:
        """Render circular dynamic rank gauge."""
        if self.hide_rank:
            return ""

        rank_letter, global_percentile = calculate_rank(self.stats)
        progress_percentage = 100 - global_percentile
        circle_radius = 30
        circumference = 2 * math.pi * circle_radius
        stroke_dashoffset = circumference - (progress_percentage / 100) * circumference

        return f"""
        <g transform="translate(0, 0)">
            <text x="320" y="75" class="rank-title">GitHub Rank</text>
            <circle cx="320" cy="125" r="{circle_radius}" class="rank-circle-bg" />
            <circle cx="320" cy="125" r="{circle_radius}" class="rank-circle-progress"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{stroke_dashoffset}" />
            <text x="320" y="125" class="rank-letter">{escape_text(rank_letter)}</text>
        </g>
        """

    def render(self) -> str:
        """Render complete SVG stats card."""
        card_width = 330 if self.hide_rank else 400
        rank_svg = self._render_rank()

        return f"""<svg width="{card_width}" height="230" viewBox="0 0 {card_width} 230" xmlns="http://www.w3.org/2000/svg">
        <defs>
            {self.bg_defs}
        </defs>
        <style>
            .header {{ font: bold 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.title_color}; }}
            .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; }}
            .bold {{ font-weight: bold; }}
            
            /* Dynamic Rank component classes */
            .rank-title {{ font: bold 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.title_color}; text-anchor: middle; }}
            .rank-letter {{ font: bold 24px 'Segoe UI', Ubuntu, Sans-Serif; fill: {self.text_color}; text-anchor: middle; dominant-baseline: central; }}
            .rank-circle-bg {{ fill: none; stroke: {self.text_color}; stroke-opacity: 0.1; stroke-width: 4.5; }}
            .rank-circle-progress {{ fill: none; stroke: {self.icon_color}; stroke-width: 4.5; stroke-linecap: round; transform: rotate(-90deg); transform-origin: 320px 125px; }}
        </style>
        
        <rect width="{card_width - 1}" height="229" x="0.5" y="0.5" rx="4.5" fill="{self.bg_fill}" stroke="{self.border_color}"/>
        
        <text x="25" y="35" class="header">{self.display_name}'s GitHub Stats</text>
        
        {self._render_icon("commits", 61)}
        <text x="50" y="75" class="stat">Total Commits: <tspan class="bold" x="190">{self.stats.get('total_commits', 0)}</tspan></text>
        
        {self._render_icon("star", 91)}
        <text x="50" y="105" class="stat">Stars Received: <tspan class="bold" x="190">{self.stats.get('stars', 0)}</tspan></text>
        
        {self._render_icon("prs", 121)}
        <text x="50" y="135" class="stat">Total PRs: <tspan class="bold" x="190">{self.stats.get('total_prs', 0)}</tspan></text>
        
        {self._render_icon("issues", 151)}
        <text x="50" y="165" class="stat">Total Issues: <tspan class="bold" x="190">{self.stats.get('total_issues', 0)}</tspan></text>
        
        {self._render_icon("contribs", 181)}
        <text x="50" y="195" class="stat">Contributed to: <tspan class="bold" x="190">{self.stats.get('contributed_to', 0)}</tspan></text>
        
        {rank_svg}
    </svg>"""


def generate_svg(
    stats: dict,
    theme_name: str = "default",
    hide_rank: bool = False,
    title_color_override: Optional[str] = None,
    text_color_override: Optional[str] = None,
    icon_color_override: Optional[str] = None,
    bg_color_override: Optional[str] = None,
    border_color_override: Optional[str] = None,
) -> str:
    """Generate SVG stats card based on user stats, theme, icons, and dynamic rank."""
    renderer = StatsCardRenderer(
        stats=stats,
        theme_name=theme_name,
        hide_rank=hide_rank,
        title_color_override=title_color_override,
        text_color_override=text_color_override,
        icon_color_override=icon_color_override,
        bg_color_override=bg_color_override,
        border_color_override=border_color_override,
    )
    return renderer.render()
