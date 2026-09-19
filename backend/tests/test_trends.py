from datetime import UTC, datetime, timedelta

from devops_insights.analytics.trends import MetricPoint, calculate_trend

START = datetime(2026, 1, 1, tzinfo=UTC)


def point(days: float, stars: int, forks: int = 0, open_issues: int = 0) -> MetricPoint:
    return MetricPoint(START + timedelta(days=days), stars, forks, open_issues)


def test_no_points_yield_an_empty_trend() -> None:
    trend = calculate_trend([])

    assert trend.snapshot_count == 0
    assert trend.first_collected_at is None
    assert trend.stars_per_day is None


def test_a_single_point_has_no_change_and_no_rate() -> None:
    trend = calculate_trend([point(0, 100)])

    assert trend.snapshot_count == 1
    assert (trend.change.stars, trend.change.forks, trend.change.open_issues) == (0, 0, 0)
    assert trend.stars_per_day is None


def test_change_is_newest_minus_oldest() -> None:
    trend = calculate_trend([point(0, 100, 10, 5), point(1, 130, 12, 9), point(2, 160, 11, 4)])

    assert trend.snapshot_count == 3
    assert trend.change.stars == 60
    assert trend.change.forks == 1
    assert trend.change.open_issues == -1


def test_stars_per_day_uses_elapsed_time() -> None:
    trend = calculate_trend([point(0, 100), point(4, 140)])

    assert trend.stars_per_day == 10.0


def test_points_at_the_same_instant_have_no_rate() -> None:
    trend = calculate_trend([point(0, 100), point(0, 120)])

    assert trend.change.stars == 20
    assert trend.stars_per_day is None
