from sqlalchemy import select
from sqlalchemy.orm import Session

from devops_insights.models import Repository, RepositorySnapshot, Technology
from devops_insights.models.base import utc_now
from devops_insights.schemas.github import GitHubRepositoryData


def store_repository(
    session: Session,
    data: GitHubRepositoryData,
    technology: Technology,
) -> Repository:
    """Create or update a repository and append a statistics snapshot.

    The repository row always holds the latest values, while every call adds one
    snapshot so that history is preserved.
    """

    collected_at = utc_now()

    repository = session.scalar(select(Repository).where(Repository.full_name == data.full_name))

    if repository is None:
        repository = Repository(full_name=data.full_name, technology_id=technology.id)
        session.add(repository)

    repository.technology_id = technology.id
    repository.name = data.name
    repository.description = data.description
    repository.url = str(data.url)
    repository.default_branch = data.default_branch
    repository.primary_language = data.primary_language
    repository.license_name = data.license_name
    repository.archived = data.archived
    repository.stars = data.stars
    repository.forks = data.forks
    repository.open_issues = data.open_issues
    repository.created_at = data.created_at
    repository.updated_at = data.updated_at
    repository.pushed_at = data.pushed_at
    repository.last_collected_at = collected_at

    session.flush()

    session.add(
        RepositorySnapshot(
            repository_id=repository.id,
            stars=data.stars,
            forks=data.forks,
            open_issues=data.open_issues,
            collected_at=collected_at,
        )
    )
    session.commit()
    session.refresh(repository)

    return repository
