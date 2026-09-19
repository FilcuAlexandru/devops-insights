from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

SECONDS_PER_DAY = 86_400


@dataclass(frozen=True)
class MetricPoint:
    """Repository metrics observed at one point in time."""

    collected_at: datetime
    stars: int
    forks: int
    open_issues: int


@dataclass(frozen=True)
class MetricChange:
    """The difference between the newest and the oldest observation."""

    stars: int = 0
    forks: int = 0
    open_issues: int = 0


@dataclass(frozen=True)
class Trend:
    """Deterministic summary of how a repository changed over its snapshots."""

    snapshot_count: int
    first_collected_at: datetime | None
    last_collected_at: datetime | None
    change: MetricChange
    stars_per_day: float | None


def calculate_trend(points: Sequence[MetricPoint]) -> Trend:
    """Summarize ordered metric points into a trend.

    Points must be sorted from oldest to newest. With fewer than two points no change
    can be observed, so all differences are zero and the star rate is undefined.
    """

    if not points:
        return Trend(0, None, None, MetricChange(), None)

    oldest, newest = points[0], points[-1]

    if len(points) < 2:
        return Trend(1, oldest.collected_at, newest.collected_at, MetricChange(), None)

    change = MetricChange(
        stars=newest.stars - oldest.stars,
        forks=newest.forks - oldest.forks,
        open_issues=newest.open_issues - oldest.open_issues,
    )

    elapsed_days = (newest.collected_at - oldest.collected_at).total_seconds() / SECONDS_PER_DAY
    stars_per_day = round(change.stars / elapsed_days, 2) if elapsed_days > 0 else None

    return Trend(len(points), oldest.collected_at, newest.collected_at, change, stars_per_day)
