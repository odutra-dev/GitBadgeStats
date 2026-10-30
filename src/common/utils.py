import html
import math
import re
from typing import Optional, Tuple

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


_HEX_COLOR_RE = re.compile(r"#?([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
_ANGLE_RE = re.compile(r"-?\d{1,3}(\.\d+)?")


def sanitize_color(value: Optional[str]) -> Optional[str]:
    """Validate a user-supplied hex color, returning it without '#', or None if invalid.

    Colors from query strings end up inside SVG attributes and <style> blocks, so anything
    that is not a plain 3/4/6/8-digit hex value is rejected instead of being interpolated.
    """
    if not value:
        return None
    match = _HEX_COLOR_RE.fullmatch(str(value).strip())
    return match.group(1) if match else None


def sanitize_background(value: Optional[str]) -> Optional[str]:
    """Validate a user-supplied background: a hex color or 'angle,color,color,...' gradient.

    Returns a normalized string accepted by parse_background(), or None if any part is invalid.
    """
    if not value:
        return None

    parts = [part.strip() for part in str(value).split(",")]
    angle = None
    if len(parts) > 1 and _ANGLE_RE.fullmatch(parts[0]):
        angle, parts = parts[0], parts[1:]

    colors = [sanitize_color(part) for part in parts]
    if not colors or any(color is None for color in colors):
        return None

    if angle is None and len(colors) == 1:
        return colors[0]
    return ",".join(([angle] if angle is not None else []) + colors)
