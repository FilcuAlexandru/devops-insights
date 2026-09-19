import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from devops_insights.models import Repository, RepositorySnapshot, Technology
from tests.factories import add_snapshot, make_repository, make_technology


def test_technology_defaults_are_applied_on_insert(session) -> None:
    technology = make_technology(session, "kubernetes")

    assert technology.id is not None
    assert technology.created_at is not None
    assert technology.updated_at is not None
    assert technology.description is None


def test_technology_slug_is_unique(session) -> None:
    make_technology(session, "docker")

    with pytest.raises(IntegrityError):
        make_technology(session, "docker")


def test_repository_full_name_is_unique(session) -> None:
    technology = make_technology(session)
    make_repository(session, technology, "owner/repo")

    with pytest.raises(IntegrityError):
        make_repository(session, technology, "owner/repo")


def test_technology_and_repository_are_linked(session) -> None:
    technology = make_technology(session)
    repository = make_repository(session, technology)

    assert repository.technology is technology
    assert repository in technology.repositories


def test_deleting_a_repository_deletes_its_snapshots(session) -> None:
    repository = make_repository(session, make_technology(session))
    add_snapshot(session, repository, days=0, stars=1)
    add_snapshot(session, repository, days=1, stars=2)

    session.delete(repository)
    session.flush()

    assert session.scalar(select(func.count(RepositorySnapshot.id))) == 0
    assert session.scalar(select(func.count(Repository.id))) == 0


def test_deleting_a_technology_deletes_its_repositories(session) -> None:
    technology = make_technology(session)
    make_repository(session, technology)

    session.delete(technology)
    session.flush()

    assert session.scalar(select(func.count(Technology.id))) == 0
    assert session.scalar(select(func.count(Repository.id))) == 0
