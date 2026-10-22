import math
from typing import Optional
from src.themes import themes
from src.icons import icons
from src.rank import calculate_rank
from src.utils import format_color, parse_background, escape_text


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
    theme = themes.get(theme_name, themes["default"])

    title_color = format_color(title_color_override or theme.get("title_color", "2f80ed"))
    text_color = format_color(text_color_override or theme.get("text_color", "333333"))
    icon_color = format_color(icon_color_override or theme.get("icon_color", "4c71f2"))

    raw_bg = bg_color_override or theme.get("bg_color", "fffefe")
    bg_defs, bg_fill = parse_background(raw_bg)

    raw_border = border_color_override or theme.get("border_color")
    border_color = format_color(raw_border) if raw_border else text_color

    # Escaped display name safe against XML/SVG injections
    display_name = escape_text(stats.get("name", "User"))

    # Helper to render icons with theme color
    def render_icon(icon_name: str, y_pos: int) -> str:
        path = icons.get(icon_name, "")
        return f"""
        <svg x="25" y="{y_pos}" width="16" height="16" viewBox="0 0 16 16" fill="{icon_color}">
            {path}
        </svg>
        """

    # Optional dynamic rank component
    rank_svg = ""
    card_width = 400
    if not hide_rank:
        rank_letter, global_percentile = calculate_rank(stats)
        progress_percentage = 100 - global_percentile
        circle_radius = 30
        circumference = 2 * math.pi * circle_radius
        stroke_dashoffset = circumference - (progress_percentage / 100) * circumference

        rank_svg = f"""
        <g transform="translate(0, 0)">
            <text x="320" y="75" class="rank-title">GitHub Rank</text>
            <circle cx="320" cy="125" r="{circle_radius}" class="rank-circle-bg" />
            <circle cx="320" cy="125" r="{circle_radius}" class="rank-circle-progress"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{stroke_dashoffset}" />
            <text x="320" y="125" class="rank-letter">{escape_text(rank_letter)}</text>
        </g>
        """
    else:
        card_width = 330

    return f"""<svg width="{card_width}" height="230" viewBox="0 0 {card_width} 230" xmlns="http://www.w3.org/2000/svg">
        <defs>
            {bg_defs}
        </defs>
        <style>
            .header {{ font: bold 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; }}
            .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
            .bold {{ font-weight: bold; }}
            
            /* Dynamic Rank component classes */
            .rank-title {{ font: bold 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; text-anchor: middle; }}
            .rank-letter {{ font: bold 24px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; text-anchor: middle; dominant-baseline: central; }}
            .rank-circle-bg {{ fill: none; stroke: {text_color}; stroke-opacity: 0.1; stroke-width: 4.5; }}
            .rank-circle-progress {{ fill: none; stroke: {icon_color}; stroke-width: 4.5; stroke-linecap: round; transform: rotate(-90deg); transform-origin: 320px 125px; }}
        </style>
        
        <rect width="{card_width - 1}" height="229" x="0.5" y="0.5" rx="4.5" fill="{bg_fill}" stroke="{border_color}"/>
        
        <text x="25" y="35" class="header">{display_name}'s GitHub Stats</text>
        
        {render_icon("commits", 61)}
        <text x="50" y="75" class="stat">Total Commits: <tspan class="bold" x="190">{stats.get('total_commits', 0)}</tspan></text>
        
        {render_icon("star", 91)}
        <text x="50" y="105" class="stat">Stars Received: <tspan class="bold" x="190">{stats.get('stars', 0)}</tspan></text>
        
        {render_icon("prs", 121)}
        <text x="50" y="135" class="stat">Total PRs: <tspan class="bold" x="190">{stats.get('total_prs', 0)}</tspan></text>
        
        {render_icon("issues", 151)}
        <text x="50" y="165" class="stat">Total Issues: <tspan class="bold" x="190">{stats.get('total_issues', 0)}</tspan></text>
        
        {render_icon("contribs", 181)}
        <text x="50" y="195" class="stat">Contributed to: <tspan class="bold" x="190">{stats.get('contributed_to', 0)}</tspan></text>
        
        {rank_svg}
    </svg>"""
