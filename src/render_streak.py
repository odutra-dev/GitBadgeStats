from typing import Optional
from src.themes import themes
from src.icons import icons, DUO_FLAME_OUTER_PATH, DUO_FLAME_INNER_PATH
from src.utils import format_color, parse_background, escape_text


def _is_dark_background(bg_color_str: str) -> bool:
    """Determine if the background is dark to adjust unlit flame contrast."""
    s = bg_color_str.lstrip("#")
    if "," in s:
        # If gradient, inspect the first color stop
        parts = [p.strip() for p in s.split(",")]
        for p in parts:
            p_clean = p.lstrip("#")
            if len(p_clean) in (3, 6):
                s = p_clean
                break
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) < 6:
        return True
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 140
    except Exception:
        return True


def render_flame_svg(
    x: int,
    y: int,
    width: int,
    height: int,
    is_lit: bool,
    dark_mode: bool = True,
    is_mini: bool = False,
) -> str:
    """Render Duolingo-style flame in either Lit (painted) or Unlit version."""
    if is_lit:
        outer_fill = "url(#flame-gradient-outer)"
        inner_fill = "url(#flame-gradient-inner)"
        filter_attr = 'filter="url(#mini-flame-glow)"' if is_mini else 'filter="url(#flame-glow)"'
        sparks = ""
        if not is_mini:
            sparks = """
            <circle cx="82" cy="18" r="2.5" fill="#FFC800" opacity="0.85"/>
            <circle cx="16" cy="30" r="2" fill="#FF9600" opacity="0.75"/>
            <circle cx="78" cy="4" r="1.5" fill="#FFE600" opacity="0.9"/>
            """
    else:
        # Unlit / desaturated flame
        outer_fill = "#475569" if dark_mode else "#94A3B8"
        inner_fill = "#334155" if dark_mode else "#CBD5E1"
        filter_attr = ""
        sparks = ""

    return f"""
    <g transform="translate({x}, {y})">
        <svg width="{width}" height="{height}" viewBox="0 0 97 118" fill="none">
            {sparks}
            <g {filter_attr}>
                <path fill-rule="evenodd" clip-rule="evenodd" d="{DUO_FLAME_OUTER_PATH}" fill="{outer_fill}"/>
                <path fill-rule="evenodd" clip-rule="evenodd" d="{DUO_FLAME_INNER_PATH}" fill="{inner_fill}"/>
            </g>
        </svg>
    </g>
    """


def generate_streak_svg(
    stats: dict,
    theme_name: str = "default",
    locale: str = "en",
    hide_days: bool = False,
    title_color_override: Optional[str] = None,
    text_color_override: Optional[str] = None,
    icon_color_override: Optional[str] = None,
    bg_color_override: Optional[str] = None,
    border_color_override: Optional[str] = None,
) -> str:
    """Generate Duolingo-style Streak SVG card.

    Features:
    - Hero flame (lit or unlit depending on whether user committed today)
    - Current streak counter
    - 7-day weekly tracker with lit/unlit flames
    - Longest streak and total commits metrics
    - Support for all themes and custom color overrides
    """
    theme = themes.get(theme_name, themes["default"])

    title_color = format_color(title_color_override or theme.get("title_color", "2f80ed"))
    text_color = format_color(text_color_override or theme.get("text_color", "333333"))
    icon_color = format_color(icon_color_override or theme.get("icon_color", "4c71f2"))

    raw_bg = bg_color_override or theme.get("bg_color", "fffefe")
    bg_defs, bg_fill = parse_background(raw_bg)
    dark_mode = _is_dark_background(raw_bg)

    raw_border = border_color_override or theme.get("border_color")
    border_color = format_color(raw_border) if raw_border else text_color

    # Extract streak statistics
    name = escape_text(stats.get("name", "User"))
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    total_commits = stats.get("total_commits", 0)
    is_active_today = stats.get("is_active_today", False)
    weekly_days = stats.get("weekly_days", [])
    streak_msg = escape_text(stats.get("streak_message", ""))

    # Localized texts
    if locale == "pt":
        card_title = f"Ofensiva de {name}"
        streak_label = "DIAS DE OFENSIVA"
        longest_label = "Maior Ofensiva"
        commits_label = "Total Commits"
        days_unit = "dias"
        active_pill = "🔥 OFENSIVA ATIVA"
        inactive_pill = "❄️ CHAMA APAGADA"
    else:
        card_title = f"{name}'s GitHub Streak"
        streak_label = "DAY STREAK"
        longest_label = "Longest Streak"
        commits_label = "Total Commits"
        days_unit = "days"
        active_pill = "🔥 STREAK ACTIVE"
        inactive_pill = "❄️ FLAME UNLIT"

    # Card dimensions
    card_width = 495
    card_height = 145 if hide_days else 228

    # Hero flame
    hero_flame_svg = render_flame_svg(
        x=28,
        y=55,
        width=58,
        height=71,
        is_lit=is_active_today,
        dark_mode=dark_mode,
        is_mini=False,
    )

    # Status pill at top-right
    if is_active_today:
        pill_bg = "#FF9600"
        pill_border = "#FF9600"
        pill_text_color = "#FF9600" if dark_mode else "#D97706"
        pill_text = active_pill
        pill_fill_opacity = "0.14"
    else:
        pill_bg = "#64748B"
        pill_border = "#94A3B8"
        pill_text_color = "#94A3B8" if dark_mode else "#475569"
        pill_text = inactive_pill
        pill_fill_opacity = "0.12"

    pill_svg = f"""
    <g transform="translate(330, 18)">
        <rect width="138" height="24" rx="12" fill="{pill_bg}" fill-opacity="{pill_fill_opacity}" stroke="{pill_border}" stroke-width="1"/>
        <text x="69" y="16" text-anchor="middle" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="10.5" font-weight="700" fill="{pill_text_color}">{pill_text}</text>
    </g>
    """

    # Trophy and commit icons for side blocks
    trophy_path = icons.get("trophy", "")
    commit_path = icons.get("commits", "")

    # Side metric blocks
    metrics_svg = f"""
    <!-- Longest Streak -->
    <g transform="translate(244, 55)">
        <rect width="110" height="68" rx="8" fill="{text_color}" fill-opacity="0.06" stroke="{border_color}" stroke-opacity="0.25"/>
        <svg x="12" y="10" width="16" height="16" viewBox="0 0 16 16" fill="#FFB700">
            {trophy_path}
        </svg>
        <text x="12" y="42" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="10" font-weight="600" fill="{text_color}" fill-opacity="0.75">{longest_label}</text>
        <text x="12" y="58" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="14.5" font-weight="bold" fill="{title_color}">{longest_streak} <tspan font-size="11" font-weight="normal">{days_unit}</tspan></text>
    </g>
    
    <!-- Total Commits -->
    <g transform="translate(362, 55)">
        <rect width="106" height="68" rx="8" fill="{text_color}" fill-opacity="0.06" stroke="{border_color}" stroke-opacity="0.25"/>
        <svg x="12" y="10" width="16" height="16" viewBox="0 0 16 16" fill="{icon_color}">
            {commit_path}
        </svg>
        <text x="12" y="42" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="10" font-weight="600" fill="{text_color}" fill-opacity="0.75">{commits_label}</text>
        <text x="12" y="58" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="14.5" font-weight="bold" fill="{title_color}">{total_commits}</text>
    </g>
    """

    # 7-day Weekly Tracker (Duolingo Style)
    weekly_svg = ""
    if not hide_days and weekly_days:
        day_items = []
        for i, day in enumerate(weekly_days):
            col_x = 28 + i * 63
            is_active = day.get("is_active", False)
            is_today = day.get("is_today", False)
            cnt = day.get("count", 0)
            day_name = escape_text(day.get("day_name", ""))

            # Highlight for today
            if is_today:
                day_border = f'stroke="{title_color}" stroke-width="1.8"'
            else:
                day_border = f'stroke="{border_color}" stroke-opacity="0.25"'

            day_bg_fill = f'fill="{text_color}" fill-opacity="0.05"'
            if is_active:
                day_bg_fill = 'fill="#FF9600" fill-opacity="0.10"'

            # Mini flame for the day
            mini_flame = render_flame_svg(
                x=18,
                y=18,
                width=18,
                height=22,
                is_lit=is_active,
                dark_mode=dark_mode,
                is_mini=True,
            )

            # Daily commit count indicator
            count_label = str(cnt) if is_active else "-"
            count_color = title_color if is_active else text_color
            count_opacity = "1" if is_active else "0.4"

            item = f"""
            <g transform="translate({col_x}, 142)">
                <rect width="55" height="66" rx="9" {day_bg_fill} {day_border}/>
                <text x="27.5" y="13" text-anchor="middle" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="10.5" font-weight="700" fill="{text_color}" fill-opacity="0.9">{day_name}</text>
                {mini_flame}
                <text x="27.5" y="56" text-anchor="middle" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="10" font-weight="700" fill="{count_color}" fill-opacity="{count_opacity}">{count_label}</text>
            </g>
            """
            day_items.append(item)

        weekly_svg = f"""
        <g class="weekly-tracker">
            {''.join(day_items)}
        </g>
        """

    return f"""<svg width="{card_width}" height="{card_height}" viewBox="0 0 {card_width} {card_height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            {bg_defs}
            <!-- Official Duolingo-style flame gradients -->
            <linearGradient id="flame-gradient-outer" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#FF9600"/>
                <stop offset="100%" stop-color="#FF3838"/>
            </linearGradient>
            <linearGradient id="flame-gradient-inner" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#FFF066"/>
                <stop offset="100%" stop-color="#FFC800"/>
            </linearGradient>
            <!-- Warm glow filter for lit flame -->
            <filter id="flame-glow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="2" stdDeviation="4.5" flood-color="#FF9600" flood-opacity="0.45"/>
            </filter>
            <filter id="mini-flame-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#FF9600" flood-opacity="0.35"/>
            </filter>
        </defs>
        
        <style>
            .header {{ font: bold 17px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; }}
            .streak-number {{ font: 800 42px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; }}
            .streak-label {{ font: 800 11px 'Segoe UI', Ubuntu, Sans-Serif; letter-spacing: 1.2px; fill: {text_color}; }}
            .streak-msg {{ font: 600 10px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; opacity: 0.8; }}
        </style>
        
        <!-- Background with rounded corners -->
        <rect width="{card_width - 1}" height="{card_height - 1}" x="0.5" y="0.5" rx="10" fill="{bg_fill}" stroke="{border_color}"/>
        
        <!-- Header -->
        <text x="28" y="35" class="header">{card_title}</text>
        {pill_svg}
        
        <!-- Main Streak Block (Hero Flame + Counter) -->
        {hero_flame_svg}
        <text x="96" y="93" class="streak-number">{current_streak}</text>
        <text x="96" y="110" class="streak-label">{streak_label}</text>
        <text x="96" y="125" class="streak-msg">{streak_msg}</text>
        
        <!-- Additional Metrics -->
        {metrics_svg}
        
        <!-- 7-day Weekly Tracker -->
        {weekly_svg}
    </svg>"""
