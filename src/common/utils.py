import html
import math
from typing import Tuple


def format_color(color_val: str, default: str = "333333") -> str:
    """Format color value, ensuring a '#' prefix when needed."""
    if not color_val:
        return f"#{default}"
    color_str = str(color_val).strip()
    if color_str.startswith("#") or "," in color_str:
        return color_str
    return f"#{color_str}"


def parse_background(bg_color_val: str, default: str = "fffefe") -> Tuple[str, str]:
    """Parse background color, generating an SVG linearGradient definition if a gradient string is provided.

    Example gradient format in themes: '35,4158d0,c850c0,ffcc70'
    Returns a tuple: (defs_xml_string, fill_attribute_value)
    """
    if not bg_color_val:
        return "", f"#{default}"

    s = str(bg_color_val).strip()
    if "," not in s:
        color = s if s.startswith("#") else f"#{s}"
        return "", color

    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts:
        return "", f"#{default}"

    # If the first value is a number, it represents the gradient angle in degrees
    first_clean = parts[0].replace(".", "", 1)
    if first_clean.isdigit() or (first_clean.startswith("-") and first_clean[1:].isdigit()):
        deg = float(parts[0])
        colors = parts[1:]
    else:
        deg = 90.0
        colors = parts

    if not colors:
        return "", f"#{default}"

    # Calculate gradient vector coordinates from angle
    angle_rad = math.radians(deg)
    x1 = round(50 - 50 * math.sin(angle_rad), 2)
    y1 = round(50 + 50 * math.cos(angle_rad), 2)
    x2 = round(50 + 50 * math.sin(angle_rad), 2)
    y2 = round(50 - 50 * math.cos(angle_rad), 2)

    stops = []
    n = len(colors)
    for i, c in enumerate(colors):
        hex_c = c if c.startswith("#") else f"#{c}"
        pct = round((i / (n - 1)) * 100, 1) if n > 1 else 0
        stops.append(f'<stop offset="{pct}%" stop-color="{hex_c}"/>')

    defs = f"""
    <linearGradient id="bg-gradient" x1="{x1}%" y1="{y1}%" x2="{x2}%" y2="{y2}%">
        {''.join(stops)}
    </linearGradient>
    """
    return defs, "url(#bg-gradient)"


def escape_text(text: str) -> str:
    """Escape XML/HTML characters to prevent SVG breakage and injection attacks."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)
