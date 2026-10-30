"""User-facing descriptions of API errors shown on SVG error cards.

Adheres to Single Responsibility Principle (SRP): pure mapping from an HTTP status code
to the text and cache lifetime of an error card. Internal error details are intentionally
never part of the text, because the card is embedded in public READMEs.
"""

import math
from dataclasses import dataclass
from typing import Optional

DEFAULT_LOCALE = "en"

NOT_FOUND_CACHE_SECONDS = 300
GENERIC_CACHE_SECONDS = 60
RATE_LIMIT_MIN_CACHE_SECONDS = 60
RATE_LIMIT_MAX_CACHE_SECONDS = 900

_TEXTS = {
    "en": {
        "not_found": ("User not found", "Check the username in the URL."),
        "rate_limit": ("GitHub rate limit reached", "Try again in {wait}."),
        "rate_limit_unknown_wait": "Try again in a few minutes.",
        "unavailable": ("Could not load GitHub data", "Please try again later."),
    },
    "pt": {
        "not_found": ("Usuário não encontrado", "Confira o username na URL."),
        "rate_limit": ("Limite do GitHub atingido", "Tente novamente em {wait}."),
        "rate_limit_unknown_wait": "Tente novamente em alguns minutos.",
        "unavailable": ("Falha ao carregar dados do GitHub", "Tente novamente mais tarde."),
    },
    "es": {
        "not_found": ("Usuario no encontrado", "Comprueba el nombre de usuario en la URL."),
        "rate_limit": ("Límite de solicitudes de GitHub alcanzado", "Inténtalo de nuevo en {wait}."),
        "rate_limit_unknown_wait": "Inténtalo de nuevo en unos minutos.",
        "unavailable": ("No se pudieron cargar los datos de GitHub", "Inténtalo de nuevo más tarde."),
    },
    "fr": {
        "not_found": ("Utilisateur introuvable", "Vérifiez le nom d'utilisateur dans l'URL."),
        "rate_limit": ("Limite de requêtes GitHub atteinte", "Réessayez dans {wait}."),
        "rate_limit_unknown_wait": "Réessayez dans quelques minutes.",
        "unavailable": ("Impossible de charger les données GitHub", "Veuillez réessayer plus tard."),
    },
    "de": {
        "not_found": ("Benutzer nicht gefunden", "Überprüfe den Benutzernamen in der URL."),
        "rate_limit": ("GitHub-Anfragelimit erreicht", "Versuche es in {wait} erneut."),
        "rate_limit_unknown_wait": "Versuche es in ein paar Minuten erneut.",
        "unavailable": ("GitHub-Daten konnten nicht geladen werden", "Bitte versuche es später erneut."),
    },
}

@dataclass(frozen=True)
class ErrorInfo:
    """Text and cache lifetime for an error card."""

    title: str
    hint: str
    cache_seconds: int


def format_wait(seconds: int) -> str:
    """Format a wait time as '45s' or '3 min'."""
    if seconds < 60:
        return f"{seconds}s"
    return f"{math.ceil(seconds / 60)} min"


def build_error_info(
    status_code: int,
    retry_after: Optional[int] = None,
    locale: str = DEFAULT_LOCALE,
) -> ErrorInfo:
    """Describe an API error for display: 404 and 429 get specific text, the rest is generic."""
    texts = _TEXTS.get(locale, _TEXTS[DEFAULT_LOCALE])

    if status_code == 404:
        title, hint = texts["not_found"]
        return ErrorInfo(title, hint, NOT_FOUND_CACHE_SECONDS)

    if status_code == 429:
        title, hint_template = texts["rate_limit"]
        if retry_after is None:
            hint = texts["rate_limit_unknown_wait"]
            cache_seconds = RATE_LIMIT_MIN_CACHE_SECONDS
        else:
            hint = hint_template.format(wait=format_wait(retry_after))
            cache_seconds = min(
                max(retry_after, RATE_LIMIT_MIN_CACHE_SECONDS),
                RATE_LIMIT_MAX_CACHE_SECONDS,
            )
        return ErrorInfo(title, hint, cache_seconds)

    title, hint = texts["unavailable"]
    return ErrorInfo(title, hint, GENERIC_CACHE_SECONDS)
