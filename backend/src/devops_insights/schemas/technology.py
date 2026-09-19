from uuid import UUID

from pydantic import BaseModel

from devops_insights.schemas.repository import RepositoryRead
from devops_insights.services.technologies import TechnologyStats


class TechnologyRead(BaseModel):
    """A technology with aggregates over its repositories."""

    id: UUID
    slug: str
    name: str
    category: str
    description: str | None
    website_url: str | None
    repository_count: int
    total_stars: int

    @classmethod
    def from_stats(cls, stats: TechnologyStats) -> "TechnologyRead":
        """Build the API representation from technology statistics."""

        technology = stats.technology

        return cls(
            id=technology.id,
            slug=technology.slug,
            name=technology.name,
            category=technology.category,
            description=technology.description,
            website_url=technology.website_url,
            repository_count=stats.repository_count,
            total_stars=stats.total_stars,
        )


class TechnologyDetailRead(TechnologyRead):
    """A technology together with its repositories."""

    repositories: list[RepositoryRead]
