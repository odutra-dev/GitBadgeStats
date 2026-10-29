import logging
from pathlib import Path
from typing import Any
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi import HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.common.themes import themes
from src.renderers.languages_card import generate_languages_svg
from src.renderers.profile_card import generate_profile_svg
from src.renderers.stats_card import generate_svg
from src.renderers.streak_card import generate_streak_svg
from src.services.error_cards import build_error_card
from src.services.github_service import (
    fetch_github_profile,
    fetch_github_stats,
    fetch_github_streak,
    fetch_github_top_languages,
)

load_dotenv()

SUPPORTED_LOCALES = ("en", "pt")

def _validate_theme(theme: str) -> None:
    if theme not in themes:
        available = ", ".join(sorted(themes))
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid theme '{theme}'. "
                f"Available themes: {available}"
            ),
        )

def _validate_locale(locale: str) -> None:
    if locale not in SUPPORTED_LOCALES:
        available = ", ".join(SUPPORTED_LOCALES)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid locale '{locale}'. "
                f"Supported locales: {available}"
            ),
        )

def _validate_timezone(timezone_name: str) -> None:
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid timezone '{timezone_name}'. "
                "Use a valid IANA timezone, such as UTC, "
                "America/Sao_Paulo or America/New_York."
            ),
        )

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Custom GitHub Stats & Streak",
    description="Dynamic GitHub README badges: General statistics, Duolingo-style commit streak, and Top Languages cards.",
    version="2.0.0",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

CACHE_HEADERS = {
    "Cache-Control": "public, max-age=14400, s-maxage=14400, stale-while-revalidate=86400",
    "Content-Type": "image/svg+xml; charset=utf-8",
}

logger = logging.getLogger("gitbadgestats")

# Endpoints consumed by <img> tags. Errors on these are returned as SVG cards.
BADGE_PATHS = frozenset({
    "/api",
    "/api/stats",
    "/api/streak",
    "/api/ofensiva",
    "/api/top-langs",
    "/api/languages",
    "/api/profile",
})


@app.exception_handler(StarletteHTTPException)
async def render_badge_error_as_svg(request: Request, exc: StarletteHTTPException):
    """Return failed badge requests as an SVG card instead of a JSON error.

    Badges are embedded with <img>, where a JSON body is just a broken image. The card is sent
    with HTTP 200 on purpose: GitHub serves README images through its Camo proxy, which answers
    404 for any upstream status other than 200/30x, so an error status would still show a broken
    image. The cache lifetime is short so the card disappears once the problem is fixed.
    Anything that is not a badge request keeps the default JSON error response.
    """
    if request.method != "GET" or request.url.path not in BADGE_PATHS:
        return await http_exception_handler(request, exc)

    if exc.status_code == 401 or exc.status_code >= 500:
        # The card stays generic on purpose; keep the real cause in the server logs.
        logger.error("GitHub error on %s: HTTP %s - %s", request.url.path, exc.status_code, exc.detail)

    card = build_error_card(exc.status_code, getattr(exc, "headers", None), request.query_params)
    headers = {
        "Cache-Control": f"public, max-age={card.cache_seconds}, s-maxage={card.cache_seconds}",
        "Content-Type": "image/svg+xml; charset=utf-8",
    }
    return Response(content=card.svg, media_type="image/svg+xml", headers=headers)

@app.get("/", response_class=FileResponse)
async def serve_home():
    """Serve the interactive home generator page."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Homepage not found")
    return FileResponse(index_file)


@app.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "ok"}


@app.get("/api/themes")
async def get_themes():
    """List all available theme names sorted alphabetically."""
    return {"themes": sorted(themes.keys())}


@app.get("/api/locales")
async def get_locales():
    """List all supported locale codes."""
    return {"locales": list(SUPPORTED_LOCALES)}


@app.get("/api")
@app.get("/api/stats")
async def get_repo_stats(
    username: str,
    theme: str = "default",
    hide_rank: bool = False,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    icon_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    border_color: Optional[str] = None,
):
    """Generate dynamic SVG badge with general user GitHub statistics and rank."""
    _validate_theme(theme)

    stats: dict[Any, Any] = await fetch_github_stats(username)

    svg_content: str = generate_svg(
        stats,
        theme_name=theme,
        hide_rank=hide_rank,
        title_color_override=title_color,
        text_color_override=text_color,
        icon_color_override=icon_color,
        bg_color_override=bg_color,
        border_color_override=border_color,
    )

    return Response(content=svg_content, media_type="image/svg+xml", headers=CACHE_HEADERS)


@app.get("/api/streak")
@app.get("/api/ofensiva")
async def get_streak_stats(
    username: str,
    theme: str = "default",
    timezone: str = "UTC",
    locale: str = "en",
    hide_days: bool = False,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    icon_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    border_color: Optional[str] = None,
):
    """Generate Duolingo-style GitHub streak SVG badge based on user commits.

    - Lit flame if user committed today.
    - Unlit flame if no commits yet today.
    - Streak resets to 0 if a full day is missed.
    - 7-day weekly tracker displaying lit flames for active days.
    """

    _validate_theme(theme)
    _validate_locale(locale)
    _validate_timezone(timezone)

    streak_data: dict[Any, Any] = await fetch_github_streak(username, timezone_name=timezone, locale=locale)

    svg_content = generate_streak_svg(
        streak_data,
        theme_name=theme,
        locale=locale,
        hide_days=hide_days,
        title_color_override=title_color,
        text_color_override=text_color,
        icon_color_override=icon_color,
        bg_color_override=bg_color,
        border_color_override=border_color,
    )

    return Response(content=svg_content, media_type="image/svg+xml", headers=CACHE_HEADERS)


@app.get("/api/top-langs")
@app.get("/api/languages")
async def get_top_languages(
    username: str,
    theme: str = "default",
    hide: Optional[str] = None,
    exclude_repo: Optional[str] = None,
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    border_color: Optional[str] = None,
    card_title: Optional[str] = None,
):
    _validate_theme(theme)

    """Generate dynamic SVG badge displaying user's top 5 most used languages."""
    langs_data: dict[Any, Any] = await fetch_github_top_languages(
        username=username,
        exclude_languages=hide,
        exclude_repos=exclude_repo,
        top_n=5,
    )

    svg_content: str = generate_languages_svg(
        langs_data,
        theme_name=theme,
        title_color_override=title_color,
        text_color_override=text_color,
        bg_color_override=bg_color,
        border_color_override=border_color,
        custom_title=card_title,
    )

    return Response(content=svg_content, media_type="image/svg+xml", headers=CACHE_HEADERS)



@app.get("/api/profile")
async def get_profile(
    username: str,
    theme: str = "default",
    locale: str = "en",
    title_color: Optional[str] = None,
    text_color: Optional[str] = None,
    icon_color: Optional[str] = None,
    bg_color: Optional[str] = None,
    border_color: Optional[str] = None,
    card_title: Optional[str] = None,
):
    """Generate a profile summary SVG badge: followers, following, repositories, stars, account age."""
    _validate_theme(theme)
    _validate_locale(locale)

    profile_data: dict[Any, Any] = await fetch_github_profile(username)

    svg_content: str = generate_profile_svg(
        profile_data,
        theme_name=theme,
        locale=locale,
        title_color_override=title_color,
        text_color_override=text_color,
        icon_color_override=icon_color,
        bg_color_override=bg_color,
        border_color_override=border_color,
        custom_title=card_title,
    )

    return Response(content=svg_content, media_type="image/svg+xml", headers=CACHE_HEADERS)