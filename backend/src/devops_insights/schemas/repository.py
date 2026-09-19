from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from devops_insights.analytics.trends import Trend
from devops_insights.models import Repository, RepositorySnapshot


class RepositoryRead(BaseModel):
    """A repository as returned by the API."""

    id: UUID
    technology_slug: str
    technology_name: str
    name: str
    full_name: str
    description: str | None
    url: str
    default_branch: str
    primary_language: str | None
    license_name: str | None
    archived: bool
    stars: int
    forks: int
    open_issues: int
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime | None
    last_collected_at: datetime | None

    @classmethod
    def from_model(cls, repository: Repository) -> "RepositoryRead":
        """Build the API representation from a repository with its technology loaded."""

        return cls(
            id=repository.id,
            technology_slug=repository.technology.slug,
            technology_name=repository.technology.name,
            name=repository.name,
            full_name=repository.full_name,
            description=repository.description,
            url=repository.url,
            default_branch=repository.default_branch,
            primary_language=repository.primary_language,
            license_name=repository.license_name,
            archived=repository.archived,
            stars=repository.stars,
            forks=repository.forks,
            open_issues=repository.open_issues,
            created_at=repository.created_at,
            updated_at=repository.updated_at,
            pushed_at=repository.pushed_at,
            last_collected_at=repository.last_collected_at,
        )


class SnapshotRead(BaseModel):
    """A repository statistics snapshot."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repository_id: UUID
    stars: int
    forks: int
    open_issues: int
    collected_at: datetime

    @classmethod
    def from_model(cls, snapshot: RepositorySnapshot) -> "SnapshotRead":
        """Build the API representation from a snapshot row."""

        return cls.model_validate(snapshot)


class MetricChangeRead(BaseModel):
    """Difference between the newest and oldest snapshot."""

    stars: int
    forks: int
    open_issues: int


class TrendRead(BaseModel):
    """Deterministic trend of a repository over its snapshots."""

    snapshot_count: int
    first_collected_at: datetime | None
    last_collected_at: datetime | None
    change: MetricChangeRead
    stars_per_day: float | None

    @classmethod
    def from_trend(cls, trend: Trend) -> "TrendRead":
        """Build the API representation from an analytics trend."""

        return cls(
            snapshot_count=trend.snapshot_count,
            first_collected_at=trend.first_collected_at,
            last_collected_at=trend.last_collected_at,
            change=MetricChangeRead(
                stars=trend.change.stars,
                forks=trend.change.forks,
                open_issues=trend.change.open_issues,
            ),
            stars_per_day=trend.stars_per_day,
        )
