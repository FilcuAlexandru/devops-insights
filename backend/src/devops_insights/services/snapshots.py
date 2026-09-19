import uuid
from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from devops_insights.analytics.trends import MetricPoint
from devops_insights.models import RepositorySnapshot


def load_metric_points(
    session: Session,
    repository_ids: Iterable[uuid.UUID],
) -> dict[uuid.UUID, list[MetricPoint]]:
    """Load ordered metric points (oldest first) for each of the given repositories."""

    repository_ids = list(repository_ids)
    points: dict[uuid.UUID, list[MetricPoint]] = defaultdict(list)

    if not repository_ids:
        return points

    rows = session.execute(
        select(
            RepositorySnapshot.repository_id,
            RepositorySnapshot.collected_at,
            RepositorySnapshot.stars,
            RepositorySnapshot.forks,
            RepositorySnapshot.open_issues,
        )
        .where(RepositorySnapshot.repository_id.in_(repository_ids))
        .order_by(RepositorySnapshot.repository_id, RepositorySnapshot.collected_at)
    )

    for repository_id, collected_at, stars, forks, open_issues in rows:
        points[repository_id].append(MetricPoint(collected_at, stars, forks, open_issues))

    return points
