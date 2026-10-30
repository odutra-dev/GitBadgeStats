"""Builds the SVG error card returned in place of a failed badge.

Coordinates error descriptions (domain) and the card renderer, reading the same theme,
color and locale query parameters the badge itself would have used.
"""

from dataclasses import dataclass
from typing import Mapping, Optional

from src.domain.error_info import DEFAULT_LOCALE, build_error_info
from src.renderers.error_card import generate_error_svg


@dataclass(frozen=True)
class ErrorCard:
    """A rendered error card and how long clients may cache it."""

    svg: str
    cache_seconds: int


def parse_retry_after(headers: Optional[Mapping[str, str]]) -> Optional[int]:
    """Read a Retry-After value (in seconds) from error headers, if present and valid."""
    for key, value in (headers or {}).items():
        if key.lower() == "retry-after" and str(value).strip().isdigit():
            return int(str(value).strip())
    return None


def build_error_card(
    status_code: int,
    headers: Optional[Mapping[str, str]],
    query_params: Mapping[str, str],
) -> ErrorCard:
    """Render the error card for a failed badge request."""
    info = build_error_info(
        status_code,
        retry_after=parse_retry_after(headers),
        locale=query_params.get("locale") or DEFAULT_LOCALE,
    )
    svg = generate_error_svg(
        info.title,
        info.hint,
        theme_name=query_params.get("theme") or "default",
        title_color_override=query_params.get("title_color"),
        text_color_override=query_params.get("text_color"),
        icon_color_override=query_params.get("icon_color"),
        bg_color_override=query_params.get("bg_color"),
        border_color_override=query_params.get("border_color"),
    )
    return ErrorCard(svg=svg, cache_seconds=info.cache_seconds)
