"""Helpers that create persisted test data."""

import itertools
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from devops_insights.models import Repository, RepositorySnapshot, Technology

_counter = itertools.count(1)

BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def make_technology(session: Session, slug: str | None = None, **overrides) -> Technology:
    number = next(_counter)
    slug = slug or f"technology-{number}"

    technology = Technology(
        slug=slug,
        name=overrides.pop("name", slug.replace("-", " ").title()),
        category=overrides.pop("category", "testing"),
        **overrides,
    )
    session.add(technology)
    session.flush()

    return technology


def make_repository(
    session: Session,
    technology: Technology,
    full_name: str | None = None,
    **overrides,
) -> Repository:
    number = next(_counter)
    full_name = full_name or f"owner/repo-{number}"
    name = full_name.split("/")[1]

    values = {
        "name": name,
        "description": f"Description of {name}",
        "url": f"https://github.com/{full_name}",
        "default_branch": "main",
        "primary_language": "Go",
        "license_name": "Apache License 2.0",
        "archived": False,
        "stars": 100,
        "forks": 10,
        "open_issues": 5,
        "created_at": BASE_TIME,
        "updated_at": BASE_TIME,
        "pushed_at": BASE_TIME,
        "last_collected_at": BASE_TIME,
    } | overrides

    repository = Repository(technology_id=technology.id, full_name=full_name, **values)
    session.add(repository)
    session.flush()

    return repository


def add_snapshot(
    session: Session,
    repository: Repository,
    days: int,
    stars: int,
    forks: int = 10,
    open_issues: int = 5,
) -> RepositorySnapshot:
    snapshot = RepositorySnapshot(
        repository_id=repository.id,
        stars=stars,
        forks=forks,
        open_issues=open_issues,
        collected_at=BASE_TIME + timedelta(days=days),
    )
    session.add(snapshot)
    session.flush()

    return snapshot
