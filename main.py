from typing import Optional
from fastapi import FastAPI, Response, Query
from dotenv import load_dotenv
from src.services.github_service import (
    fetch_github_stats,
    fetch_github_streak,
    fetch_github_top_languages,
)
from src.renderers.stats_card import generate_svg
from src.renderers.streak_card import generate_streak_svg
from src.renderers.languages_card import generate_languages_svg

load_dotenv()

app = FastAPI(
    title="Custom GitHub Stats & Streak",
    description="Dynamic GitHub README badges: General statistics, Duolingo-style commit streak, and Top Languages cards.",
    version="2.0.0",
)

CACHE_HEADERS = {
    "Cache-Control": "public, max-age=14400, s-maxage=14400, stale-while-revalidate=86400",
    "Content-Type": "image/svg+xml; charset=utf-8",
}


@app.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "ok"}


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
    stats = await fetch_github_stats(username)

    svg_content = generate_svg(
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
    streak_data = await fetch_github_streak(username, timezone_name=timezone, locale=locale)

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
    """Generate dynamic SVG badge displaying user's top 5 most used languages."""
    langs_data = await fetch_github_top_languages(
        username=username,
        exclude_languages=hide,
        exclude_repos=exclude_repo,
        top_n=5,
    )

    svg_content = generate_languages_svg(
        langs_data,
        theme_name=theme,
        title_color_override=title_color,
        text_color_override=text_color,
        bg_color_override=bg_color,
        border_color_override=border_color,
        custom_title=card_title,
    )

    return Response(content=svg_content, media_type="image/svg+xml", headers=CACHE_HEADERS)
