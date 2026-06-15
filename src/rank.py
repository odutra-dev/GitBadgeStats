import math


def calculate_exponential_cdf(x: float, lmbda: float) -> float:
    """Função de distribuição acumulada exponencial."""
    return 1 - math.exp(-lmbda * x)


def calculate_rank(stats: dict) -> tuple[str, float]:
    """Calcula o Rank (S, A+, etc.) e o percentil global com base nas estatísticas.

    Espera um dicionário contendo: total_commits, stars, total_prs,
    total_issues,
    contributed_to (ou reviews se preferir mapear 1:1) e followers.
    """
    # 1. Recuperar valores com fallbacks seguros
    commits = stats.get("total_commits", 0)
    stars = stats.get("stars", 0)
    prs = stats.get("total_prs", 0)
    issues = stats.get("total_issues", 0)
    # Se não tiver a chave exata do original, usamos o que temos disponível
    reviews = stats.get("reviews", stats.get("contributed_to", 0))
    followers = stats.get("followers", 0)

    # 2. Constantes aproximadas do github-readme-stats para a distribuição
    # COMMITS: sigma total acumulado
    commits_p = calculate_exponential_cdf(commits, 0.0002) * 100
    # STARS: log-normal aproximada
    stars_p = (
        calculate_exponential_cdf(stars, 0.002) * 100
        if stars > 0
        else 0
    )
    # PRS
    prs_p = calculate_exponential_cdf(prs, 0.015) * 100
    # ISSUES
    issues_p = calculate_exponential_cdf(issues, 0.02) * 100
    # REVIEWS / CONTRIPUTED TO
    reviews_p = calculate_exponential_cdf(reviews, 0.015) * 100
    # FOLLOWERS
    followers_p = (
        calculate_exponential_cdf(followers, 0.005) * 100
        if followers > 0
        else 0
    )

    # 3. Pesos oficiais do algoritmo original
    # Commits: 4x, Stars: 3x, PRs: 2x, Issues: 1x, Contribs/Reviews: 1x, Followers: 1x
    weighted_sum = (
        (100 - commits_p) * 4
        + (100 - stars_p) * 3
        + (100 - prs_p) * 2
        + (100 - issues_p) * 1
        + (100 - reviews_p) * 1
        + (100 - followers_p) * 1
    )

    total_weight = 4 + 3 + 2 + 1 + 1 + 1

    # Percentil Global (0% significa o topo absoluto, 100% a base total)
    global_percentile = weighted_sum / total_weight

    # 4. Determinar o Rank com base no percentil global (Top X%)
    if global_percentile <= 1.0:
        rank_letter = "S"
    elif global_percentile <= 12.5:
        rank_letter = "A+"
    elif global_percentile <= 25.0:
        rank_letter = "A"
    elif global_percentile <= 37.5:
        rank_letter = "A-"
    elif global_percentile <= 50.0:
        rank_letter = "B+"
    elif global_percentile <= 62.5:
        rank_letter = "B"
    elif global_percentile <= 75.0:
        rank_letter = "B-"
    elif global_percentile <= 87.5:
        rank_letter = "C+"
    else:
        rank_letter = "C"

    return rank_letter, global_percentile
