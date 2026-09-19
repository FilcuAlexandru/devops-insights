from uuid import UUID

from sqlalchemy.orm import Session

from devops_insights.analytics.trends import MetricPoint, calculate_trend
from devops_insights.services.repositories import get_repository
from devops_insights.services.snapshots import load_metric_points


def _snapshot_to_dict(point: MetricPoint) -> dict:
    return {
        "collected_at": point.collected_at.isoformat(),
        "stars": point.stars,
        "forks": point.forks,
        "open_issues": point.open_issues,
    }


def build_repository_context(session: Session, repository_id: UUID) -> dict | None:
    """Build the structured context sent to the model, or ``None`` if the repository is unknown.

    Every number the model may mention is calculated here, in Python.
    """

    repository = get_repository(session, repository_id)

    if repository is None:
        return None

    points = load_metric_points(session, [repository_id])[repository_id]
    trend = calculate_trend(points)
    snapshots = [_snapshot_to_dict(point) for point in points]

    return {
        "technology": {
            "name": repository.technology.name,
            "slug": repository.technology.slug,
            "category": repository.technology.category,
        },
        "repository": {
            "name": repository.name,
            "full_name": repository.full_name,
            "description": repository.description,
            "url": repository.url,
            "default_branch": repository.default_branch,
            "primary_language": repository.primary_language,
            "license": repository.license_name,
            "archived": repository.archived,
            "stars": repository.stars,
            "forks": repository.forks,
            "open_issues": repository.open_issues,
            "created_at": repository.created_at.isoformat(),
            "updated_at": repository.updated_at.isoformat(),
            "pushed_at": repository.pushed_at.isoformat() if repository.pushed_at else None,
        },
        "historical_metrics": {
            "snapshot_count": trend.snapshot_count,
            "oldest": snapshots[0] if snapshots else None,
            "newest": snapshots[-1] if snapshots else None,
            "changes": {
                "stars": trend.change.stars,
                "forks": trend.change.forks,
                "open_issues": trend.change.open_issues,
            },
        },
        "snapshots": snapshots,
    }
