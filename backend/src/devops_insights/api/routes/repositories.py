from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from devops_insights.analytics.trends import calculate_trend
from devops_insights.api.dependencies import DbSession
from devops_insights.schemas.repository import RepositoryRead, SnapshotRead, TrendRead
from devops_insights.services.repositories import (
    RepositorySort,
    SortOrder,
    get_repository,
    list_repositories,
    list_snapshots,
)
from devops_insights.services.snapshots import load_metric_points

router = APIRouter(prefix="/api/repositories", tags=["repositories"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")


@router.get("", response_model=list[RepositoryRead])
def list_repositories_endpoint(
    session: DbSession,
    technology: str | None = Query(None, description="Filter by technology slug."),
    search: str | None = Query(None, max_length=100, description="Match name or description."),
    sort: RepositorySort = RepositorySort.STARS,
    order: SortOrder = SortOrder.DESC,
) -> list[RepositoryRead]:
    """Return tracked repositories, optionally filtered and sorted."""

    repositories = list_repositories(
        session,
        technology_slug=technology,
        search=search,
        sort=sort,
        order=order,
    )

    return [RepositoryRead.from_model(repository) for repository in repositories]


@router.get("/{repository_id}", response_model=RepositoryRead)
def get_repository_endpoint(repository_id: UUID, session: DbSession) -> RepositoryRead:
    """Return a repository by its ID."""

    repository = get_repository(session, repository_id)

    if repository is None:
        raise _NOT_FOUND

    return RepositoryRead.from_model(repository)


@router.get("/{repository_id}/snapshots", response_model=list[SnapshotRead])
def list_snapshots_endpoint(repository_id: UUID, session: DbSession) -> list[SnapshotRead]:
    """Return all statistics snapshots of a repository, oldest first."""

    if get_repository(session, repository_id) is None:
        raise _NOT_FOUND

    return [
        SnapshotRead.from_model(snapshot) for snapshot in list_snapshots(session, repository_id)
    ]


@router.get("/{repository_id}/trend", response_model=TrendRead)
def get_trend_endpoint(repository_id: UUID, session: DbSession) -> TrendRead:
    """Return the deterministic trend of a repository across its snapshots."""

    if get_repository(session, repository_id) is None:
        raise _NOT_FOUND

    points = load_metric_points(session, [repository_id])[repository_id]

    return TrendRead.from_trend(calculate_trend(points))
