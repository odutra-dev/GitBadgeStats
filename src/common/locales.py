"""Translations for the GitHub streak card."""

from typing import TypedDict


class LocaleTranslations(TypedDict):
    """Translation keys required by the streak card."""

    weekdays: list[str]
    status_active: str
    status_pending: str
    status_start: str
    card_title: str
    streak_label: str
    longest_label: str
    commits_label: str
    days_unit: str
    active_pill: str
    inactive_pill: str

TRANSLATIONS: dict[str, LocaleTranslations] = {
    "en": {
        "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "status_active": "Streak active! Flame is burning today",
        "status_pending": "Flame unlit • Commit today to keep your streak!",
        "status_start": "Flame unlit • Commit to start your streak!",
        "card_title": "{name}'s GitHub Streak",
        "streak_label": "DAY STREAK",
        "longest_label": "Longest Streak",
        "commits_label": "Total Commits",
        "days_unit": "days",
        "active_pill": "🔥 STREAK ACTIVE",
        "inactive_pill": "❄️ FLAME UNLIT",
    },
    "pt": {
        "weekdays": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
        "status_active": "Ofensiva mantida! Chama acesa hoje",
        "status_pending": "Chama apagada • Faça um commit hoje!",
        "status_start": "Chama apagada • Faça um commit para iniciar!",
        "card_title": "Ofensiva de {name}",
        "streak_label": "DIAS DE OFENSIVA",
        "longest_label": "Maior Ofensiva",
        "commits_label": "Total de commits",
        "days_unit": "dias",
        "active_pill": "🔥 OFENSIVA ATIVA",
        "inactive_pill": "❄️ CHAMA APAGADA",
    },
    "es": {
        "weekdays": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
        "status_active": "¡Racha activa! La llama sigue encendida hoy",
        "status_pending": "Llama apagada • ¡Haz un commit hoy para mantener tu racha!",
        "status_start": "Llama apagada • ¡Haz un commit para empezar tu racha!",
        "card_title": "Racha de GitHub de {name}",
        "streak_label": "DÍAS DE RACHA",
        "longest_label": "Racha más larga",
        "commits_label": "Commits totales",
        "days_unit": "días",
        "active_pill": "🔥 RACHA ACTIVA",
        "inactive_pill": "❄️ LLAMA APAGADA",
    },
    "fr": {
        "weekdays": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        "status_active": "Série active ! La flamme brûle aujourd'hui",
        "status_pending": "Flamme éteinte • Faites un commit aujourd'hui pour continuer votre série !",
        "status_start": "Flamme éteinte • Faites un commit pour commencer votre série !",
        "card_title": "Série GitHub de {name}",
        "streak_label": "JOURS DE SÉRIE",
        "longest_label": "Plus longue série",
        "commits_label": "Commits au total",
        "days_unit": "jours",
        "active_pill": "🔥 SÉRIE ACTIVE",
        "inactive_pill": "❄️ FLAMME ÉTEINTE",
    },
    "de": {
        "weekdays": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
        "status_active": "Serie aktiv! Die Flamme brennt heute",
        "status_pending": "Flamme aus • Erstelle heute einen Commit, um deine Serie fortzusetzen!",
        "status_start": "Flamme aus • Erstelle einen Commit, um deine Serie zu starten!",
        "card_title": "GitHub-Serie von {name}",
        "streak_label": "TAGE IN FOLGE",
        "longest_label": "Längste Serie",
        "commits_label": "Commits insgesamt",
        "days_unit": "Tage",
        "active_pill": "🔥 SERIE AKTIV",
        "inactive_pill": "❄️ FLAMME AUS",
    },
}

SUPPORTED_LOCALES = tuple(TRANSLATIONS)


def get_translations(locale: str) -> LocaleTranslations:
    """Return translations for a supported locale."""
    try:
        return TRANSLATIONS[locale]
    except KeyError as exc:
        supported = ", ".join(SUPPORTED_LOCALES)
        raise ValueError(
            f"Unsupported locale '{locale}'. Supported locales: {supported}"
        ) from exc
        


class ProfileTranslations(TypedDict):
    """Translation keys required by the profile card."""

    card_title: str
    followers_label: str
    following_label: str
    repositories_label: str
    stars_label: str
    account_age_label: str
    year_one: str
    year_other: str
    month_one: str
    month_other: str
    age_separator: str


PROFILE_TRANSLATIONS: dict[str, ProfileTranslations] = {
    "en": {
        "card_title": "{name}'s GitHub Profile",
        "followers_label": "Followers",
        "following_label": "Following",
        "repositories_label": "Repositories",
        "stars_label": "Stars",
        "account_age_label": "Account age",
        "year_one": "year",
        "year_other": "years",
        "month_one": "month",
        "month_other": "months",
        "age_separator": ", ",
    },
    "pt": {
        "card_title": "Perfil GitHub de {name}",
        "followers_label": "Seguidores",
        "following_label": "Seguindo",
        "repositories_label": "Repositórios",
        "stars_label": "Estrelas",
        "account_age_label": "Tempo de conta",
        "year_one": "ano",
        "year_other": "anos",
        "month_one": "mês",
        "month_other": "meses",
        "age_separator": " e ",
    },
    "es": {
        "card_title": "Perfil de GitHub de {name}",
        "followers_label": "Seguidores",
        "following_label": "Siguiendo",
        "repositories_label": "Repositorios",
        "stars_label": "Estrellas",
        "account_age_label": "Antigüedad",
        "year_one": "año",
        "year_other": "años",
        "month_one": "mes",
        "month_other": "meses",
        "age_separator": " y ",
    },
    "fr": {
        "card_title": "Profil GitHub de {name}",
        "followers_label": "Abonnés",
        "following_label": "Abonnements",
        "repositories_label": "Dépôts",
        "stars_label": "Étoiles",
        "account_age_label": "Ancienneté",
        "year_one": "an",
        "year_other": "ans",
        "month_one": "mois",
        "month_other": "mois",
        "age_separator": " et ",
    },
    "de": {
        "card_title": "GitHub-Profil von {name}",
        "followers_label": "Follower",
        "following_label": "Folge ich",
        "repositories_label": "Repositories",
        "stars_label": "Sterne",
        "account_age_label": "Kontoalter",
        "year_one": "Jahr",
        "year_other": "Jahre",
        "month_one": "Monat",
        "month_other": "Monate",
        "age_separator": " und ",
    },
}


def get_profile_translations(locale: str) -> ProfileTranslations:
    """Return profile card translations for a supported locale."""
    try:
        return PROFILE_TRANSLATIONS[locale]
    except KeyError as exc:
        supported = ", ".join(PROFILE_TRANSLATIONS)
        raise ValueError(
            f"Unsupported locale '{locale}'. Supported locales: {supported}"
        ) from exc


class StatsTranslations(TypedDict):
    """Translation keys required by the stats card."""

    card_title: str
    commits_label: str
    stars_label: str
    prs_label: str
    issues_label: str
    contribs_label: str
    rank_title: str


STATS_TRANSLATIONS: dict[str, StatsTranslations] = {
    "en": {
        "card_title": "{name}'s GitHub Stats",
        "commits_label": "Total Commits",
        "stars_label": "Stars Received",
        "prs_label": "Total PRs",
        "issues_label": "Total Issues",
        "contribs_label": "Contributed to",
        "rank_title": "GitHub Rank",
    },
    "pt": {
        "card_title": "Estatísticas do GitHub de {name}",
        "commits_label": "Total de commits",
        "stars_label": "Estrelas recebidas",
        "prs_label": "Total de PRs",
        "issues_label": "Total de issues",
        "contribs_label": "Contribuiu para",
        "rank_title": "Rank GitHub",
    },
    "es": {
        "card_title": "Estadísticas de GitHub de {name}",
        "commits_label": "Commits totales",
        "stars_label": "Estrellas recibidas",
        "prs_label": "PRs totales",
        "issues_label": "Issues totales",
        "contribs_label": "Contribuido a",
        "rank_title": "Rank GitHub",
    },
    "fr": {
        "card_title": "Statistiques GitHub de {name}",
        "commits_label": "Commits au total",
        "stars_label": "Étoiles reçues",
        "prs_label": "Total des PRs",
        "issues_label": "Total des issues",
        "contribs_label": "A contribué à",
        "rank_title": "Rang GitHub",
    },
    "de": {
        "card_title": "GitHub-Statistiken von {name}",
        "commits_label": "Commits insgesamt",
        "stars_label": "Erhaltene Sterne",
        "prs_label": "PRs insgesamt",
        "issues_label": "Issues insgesamt",
        "contribs_label": "Beigetragen zu",
        "rank_title": "GitHub-Rang",
    },
}


def get_stats_translations(locale: str) -> StatsTranslations:
    """Return stats card translations for a supported locale."""
    try:
        return STATS_TRANSLATIONS[locale]
    except KeyError as exc:
        supported = ", ".join(STATS_TRANSLATIONS)
        raise ValueError(
            f"Unsupported locale '{locale}'. Supported locales: {supported}"
        ) from exc


class LanguagesTranslations(TypedDict):
    """Translation keys required by the top languages card."""

    card_title: str
    empty_text: str


LANGUAGES_TRANSLATIONS: dict[str, LanguagesTranslations] = {
    "en": {
        "card_title": "Most Used Languages",
        "empty_text": "No languages found",
    },
    "pt": {
        "card_title": "Linguagens Mais Usadas",
        "empty_text": "Nenhuma linguagem encontrada",
    },
    "es": {
        "card_title": "Lenguajes Más Usados",
        "empty_text": "No se encontraron lenguajes",
    },
    "fr": {
        "card_title": "Langages les Plus Utilisés",
        "empty_text": "Aucun langage trouvé",
    },
    "de": {
        "card_title": "Meistgenutzte Sprachen",
        "empty_text": "Keine Sprachen gefunden",
    },
}


def get_languages_translations(locale: str) -> LanguagesTranslations:
    """Return top languages card translations for a supported locale."""
    try:
        return LANGUAGES_TRANSLATIONS[locale]
    except KeyError as exc:
        supported = ", ".join(LANGUAGES_TRANSLATIONS)
        raise ValueError(
            f"Unsupported locale '{locale}'. Supported locales: {supported}"
        ) from exc
