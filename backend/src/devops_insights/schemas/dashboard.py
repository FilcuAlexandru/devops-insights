from uuid import UUID

from pydantic import BaseModel

from devops_insights.schemas.ai import AIAnalysisSummaryRead
from devops_insights.schemas.collection import CollectionRunRead


class DashboardTotals(BaseModel):
    """Headline numbers for the selected scope."""

    technologies: int
    repositories: int
    stars: int
    forks: int
    open_issues: int
    snapshots: int


class TechnologyShare(BaseModel):
    """Repository and star counts of one technology."""

    slug: str
    name: str
    repository_count: int
    stars: int


class LanguageShare(BaseModel):
    """Number of repositories written primarily in one language."""

    language: str
    repository_count: int


class RepositoryHighlight(BaseModel):
    """A repository listed in a ranking."""

    id: UUID
    full_name: str
    technology_name: str
    primary_language: str | None
    stars: int
    forks: int
    open_issues: int


class GrowthHighlight(BaseModel):
    """A repository ranked by stars gained between its first and last snapshot."""

    id: UUID
    full_name: str
    stars: int
    stars_gained: int
    stars_per_day: float | None
    snapshot_count: int


class DashboardRead(BaseModel):
    """Everything the dashboard needs in one response."""

    totals: DashboardTotals
    technologies: list[TechnologyShare]
    languages: list[LanguageShare]
    top_repositories: list[RepositoryHighlight]
    fastest_growing: list[GrowthHighlight]
    recent_analyses: list[AIAnalysisSummaryRead]
    last_collection: CollectionRunRead | None
