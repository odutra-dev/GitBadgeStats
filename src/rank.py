import math


def exponential_cdf(x: float) -> float:
    """Calcula o CDF exponencial baseado na lógica do repositório."""
    return 1 - (2**-x)


def log_normal_cdf(x: float) -> float:
    """Calcula a aproximação do CDF log-normal."""
    return x / (1 + x) if x >= 0 else 0


def calculate_rank(stats: dict) -> tuple[str, float]:
    """Calcula o Rank (S, A+, etc.) e o percentil global traduzido do JS oficial.

    Retorna uma tupla: (level, percentile)
    """
    # Recuperando parâmetros com fallback para falso/zero se não existirem
    all_commits = stats.get("all_commits", False)
    commits = stats.get("total_commits", 0)
    prs = stats.get("total_prs", 0)
    issues = stats.get("total_issues", 0)
    # Se 'reviews' não existir, usa 'contributed_to' como plano B
    reviews = stats.get("reviews", stats.get("contributed_to", 0))
    stars = stats.get("stars", 0)
    followers = stats.get("followers", 0)

    # Medianas e Pesos oficiais do arquivo JS
    commits_median = 1000 if all_commits else 250
    commits_weight = 2

    prs_median = 50
    prs_weight = 3

    issues_median = 25
    issues_weight = 1

    reviews_median = 2
    reviews_weight = 1

    stars_median = 50
    stars_weight = 4

    followers_median = 10
    followers_weight = 1

    total_weight = (
        commits_weight
        + prs_weight
        + issues_weight
        + reviews_weight
        + stars_weight
        + followers_weight
    )

    thresholds = [1.0, 12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5, 100.0]
    levels = ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"]

    # Cálculo do Rank (Exatamente a fórmula matemática do JS)
    weighted_sum = (
        commits_weight * exponential_cdf(commits / commits_median)
        + prs_weight * exponential_cdf(prs / prs_median)
        + issues_weight * exponential_cdf(issues / issues_median)
        + reviews_weight * exponential_cdf(reviews / reviews_median)
        + stars_weight * log_normal_cdf(stars / stars_median)
        + followers_weight * log_normal_cdf(followers / followers_median)
    )

    rank_val = 1 - (weighted_sum / total_weight)
    percentile = rank_val * 100

    # Encontra o nível correspondente (Equivalente ao findIndex do JS)
    level = "C"  # Fallback caso passe de 100 por alguma anomalia externa
    for t, lvl in zip(thresholds, levels):
        if percentile <= t:
            level = lvl
            break

    return level, percentile
