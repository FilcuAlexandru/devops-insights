from fastapi import APIRouter, HTTPException, status

from devops_insights.api.dependencies import DbSession
from devops_insights.schemas.repository import RepositoryRead
from devops_insights.schemas.technology import TechnologyDetailRead, TechnologyRead
from devops_insights.services.repositories import list_repositories
from devops_insights.services.technologies import get_technology, list_technologies

router = APIRouter(prefix="/api/technologies", tags=["technologies"])


@router.get("", response_model=list[TechnologyRead])
def list_technologies_endpoint(session: DbSession) -> list[TechnologyRead]:
    """Return all tracked technologies with repository aggregates."""

    return [TechnologyRead.from_stats(stats) for stats in list_technologies(session)]


@router.get("/{slug}", response_model=TechnologyDetailRead)
def get_technology_endpoint(slug: str, session: DbSession) -> TechnologyDetailRead:
    """Return a technology and its repositories."""

    stats = get_technology(session, slug)

    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology not found.")

    repositories = [
        RepositoryRead.from_model(repository)
        for repository in list_repositories(session, technology_slug=slug)
    ]

    return TechnologyDetailRead(
        **TechnologyRead.from_stats(stats).model_dump(),
        repositories=repositories,
    )
