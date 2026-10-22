"""Unit tests for GitHub dynamic rank calculation module."""

from src.rank import calculate_rank, exponential_cdf, log_normal_cdf


def test_exponential_cdf():
    """Verify CDF curve bounds."""
    assert exponential_cdf(0) == 0.0
    assert 0.49 < exponential_cdf(1) < 0.51
    assert exponential_cdf(10) > 0.99


def test_log_normal_cdf():
    """Verify log-normal approximation bounds."""
    assert log_normal_cdf(-1) == 0.0
    assert log_normal_cdf(0) == 0.0
    assert log_normal_cdf(1) == 0.5
    assert log_normal_cdf(9) == 0.9


def test_calculate_rank_top_tier():
    """Verify high volume contributions achieve S rank."""
    high_stats = {
        "total_commits": 10000,
        "total_prs": 500,
        "total_issues": 300,
        "reviews": 100,
        "stars": 2000,
        "followers": 500,
    }
    level, percentile = calculate_rank(high_stats)
    assert level in ("S", "A+")
    assert percentile <= 12.5


def test_calculate_rank_novice_tier():
    """Verify minimal activity falls into C rank tier."""
    low_stats = {
        "total_commits": 0,
        "total_prs": 0,
        "total_issues": 0,
        "stars": 0,
        "followers": 0,
    }
    level, percentile = calculate_rank(low_stats)
    assert level == "C"
    assert percentile >= 87.5
