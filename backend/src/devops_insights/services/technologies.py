from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from devops_insights.models import Repository, Technology


@dataclass(frozen=True)
class TechnologyStats:
    """A technology together with aggregates over its repositories."""

    technology: Technology
    repository_count: int
    total_stars: int


def _stats_statement() -> Select:
    return (
        select(
            Technology,
            func.count(Repository.id),
            func.coalesce(func.sum(Repository.stars), 0),
        )
        .outerjoin(Repository, Repository.technology_id == Technology.id)
        .group_by(Technology.id)
    )


def list_technologies(session: Session) -> list[TechnologyStats]:
    """Return every technology with repository aggregates, ordered by name."""

    rows = session.execute(_stats_statement().order_by(Technology.name))

    return [TechnologyStats(technology, count, int(stars)) for technology, count, stars in rows]


def get_technology(session: Session, slug: str) -> TechnologyStats | None:
    """Return one technology with repository aggregates, or ``None``."""

    row = session.execute(_stats_statement().where(Technology.slug == slug)).first()

    if row is None:
        return None

    technology, count, stars = row

    return TechnologyStats(technology, count, int(stars))
