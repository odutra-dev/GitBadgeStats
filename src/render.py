from src.themes import themes
from src.icons import icons


def generate_svg(stats: dict, theme_name: str = "default") -> str:
    """Gera o SVG baseado nos dados, aplicando o tema e adicionando os ícones."""
    theme = themes.get(theme_name, themes["default"])

    def format_color(color_val):
        if not color_val:
            return ""
        color_str = str(color_val).strip()
        if "," in color_str or color_str.startswith("#"):
            return color_str
        return f"#{color_str}"

    title_color = format_color(theme.get("title_color", "2f80ed"))
    text_color = format_color(theme.get("text_color", "333333"))
    icon_color = format_color(theme.get("icon_color", "4c71f2"))
    bg_color = format_color(theme.get("bg_color", "fffefe"))

    border_color = theme.get("border_color")
    border_color = format_color(border_color) if border_color else text_color

    # Função utilitária para renderizar o ícone com a cor do tema na posição correta
    def render_icon(icon_name: str, y_pos: int) -> str:
        path = icons.get(icon_name, "")
        return f"""
        <svg x="25" y="{y_pos}" width="16" height="16" viewBox="0 0 16 16" fill="{icon_color}">
            {path}
        </svg>
        """

    return f"""<svg width="400" height="230" viewBox="0 0 400 230" xmlns="http://www.w3.org/2000/svg">
        <style>
            .header {{ font: bold 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {title_color}; }}
            .stat {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
            .bold {{ font-weight: bold; }}
        </style>
        
        <rect width="399" height="229" x="0.5" y="0.5" rx="4.5" fill="{bg_color}" stroke="{border_color}"/>
        
        <text x="25" y="35" class="header">{stats['name']}'s GitHub Stats</text>
        
        {render_icon("commits", 61)}
        <text x="50" y="75" class="stat">Total Commits: <tspan class="bold" x="190">{stats['total_commits']}</tspan></text>
        
        {render_icon("star", 91)}
        <text x="50" y="105" class="stat">Stars Received: <tspan class="bold" x="190">{stats['stars']}</tspan></text>
        
        {render_icon("prs", 121)}
        <text x="50" y="135" class="stat">Total PRs: <tspan class="bold" x="190">{stats['total_prs']}</tspan></text>
        
        {render_icon("issues", 151)}
        <text x="50" y="165" class="stat">Total Issues: <tspan class="bold" x="190">{stats['total_issues']}</tspan></text>
        
        {render_icon("contribs", 181)}
        <text x="50" y="195" class="stat">Contributed to: <tspan class="bold" x="190">{stats['contributed_to']}</tspan></text>
    </svg>"""
