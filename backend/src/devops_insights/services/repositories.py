import uuid
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from devops_insights.models import Repository, RepositorySnapshot, Technology


class RepositorySort(StrEnum):
    """Fields a repository list can be sorted by."""

    STARS = "stars"
    FORKS = "forks"
    ISSUES = "issues"
    NAME = "name"
    ACTIVITY = "activity"


class SortOrder(StrEnum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


_SORT_COLUMNS = {
    RepositorySort.STARS: Repository.stars,
    RepositorySort.FORKS: Repository.forks,
    RepositorySort.ISSUES: Repository.open_issues,
    RepositorySort.NAME: Repository.full_name,
    RepositorySort.ACTIVITY: Repository.pushed_at,
}


def list_repositories(
    session: Session,
    technology_slug: str | None = None,
    search: str | None = None,
    sort: RepositorySort = RepositorySort.STARS,
    order: SortOrder = SortOrder.DESC,
) -> list[Repository]:
    """Return repositories matching the filters, with their technology loaded."""

    statement = select(Repository).join(Technology).options(joinedload(Repository.technology))

    if technology_slug:
        statement = statement.where(Technology.slug == technology_slug)

    if search and search.strip():
        term = search.strip()
        statement = statement.where(
            Repository.full_name.icontains(term, autoescape=True)
            | Repository.description.icontains(term, autoescape=True)
        )

    column = _SORT_COLUMNS[sort]
    ordering = column.asc() if order is SortOrder.ASC else column.desc()

    return list(
        session.scalars(statement.order_by(ordering.nulls_last(), Repository.full_name)).unique()
    )


def get_repository(session: Session, repository_id: uuid.UUID) -> Repository | None:
    """Return a repository with its technology loaded, or ``None``."""

    return session.scalar(
        select(Repository)
        .options(joinedload(Repository.technology))
        .where(Repository.id == repository_id)
    )


def list_snapshots(session: Session, repository_id: uuid.UUID) -> list[RepositorySnapshot]:
    """Return every snapshot of a repository, oldest first."""

    return list(
        session.scalars(
            select(RepositorySnapshot)
            .where(RepositorySnapshot.repository_id == repository_id)
            .order_by(RepositorySnapshot.collected_at)
        )
    )
