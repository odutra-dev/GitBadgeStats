import math


def exponential_cdf(x: float) -> float:
    """Calculate exponential CDF matching the official algorithm."""
    return 1 - (2**-x)


def log_normal_cdf(x: float) -> float:
    """Calculate log-normal CDF approximation."""
    return x / (1 + x) if x >= 0 else 0


def calculate_rank(stats: dict) -> tuple[str, float]:
    """Calculate Rank level (S, A+, etc.) and global percentile matching github-readme-stats.

    Returns a tuple: (level, percentile)
    """
    # Retrieve stats parameters with fallbacks
    all_commits = stats.get("all_commits", False)
    commits = stats.get("total_commits", 0)
    prs = stats.get("total_prs", 0)
    issues = stats.get("total_issues", 0)
    reviews = stats.get("reviews", stats.get("contributed_to", 0))
    stars = stats.get("stars", 0)
    followers = stats.get("followers", 0)

    # Medians and weights
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

    # Rank calculation
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

    # Match corresponding tier level
    level = "C"
    for t, lvl in zip(thresholds, levels):
        if percentile <= t:
            level = lvl
            break

    return level, percentile
