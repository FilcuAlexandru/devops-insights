from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from devops_insights.models import RepositorySnapshot
from devops_insights.pipelines.github import collect_repository
from devops_insights.pipelines.normalize import normalize_repository
from devops_insights.pipelines.store import store_repository
from devops_insights.schemas.github import GitHubRepositoryData
from tests.factories import make_technology

GITHUB_CREATED = datetime(2014, 6, 6, 22, 56, 4, tzinfo=UTC)
GITHUB_UPDATED = datetime(2026, 9, 1, 10, 0, 0, tzinfo=UTC)
GITHUB_PUSHED = datetime(2026, 9, 1, 9, 0, 0, tzinfo=UTC)


def make_data(**overrides) -> GitHubRepositoryData:
    values = {
        "name": "kubernetes",
        "full_name": "kubernetes/kubernetes",
        "description": "Container orchestration.",
        "url": "https://github.com/kubernetes/kubernetes",
        "default_branch": "master",
        "primary_language": "Go",
        "license_name": "Apache License 2.0",
        "archived": False,
        "stars": 100,
        "forks": 10,
        "open_issues": 5,
        "created_at": GITHUB_CREATED,
        "updated_at": GITHUB_UPDATED,
        "pushed_at": GITHUB_PUSHED,
    } | overrides

    return GitHubRepositoryData(**values)


def test_normalize_strips_whitespace_and_blank_values() -> None:
    data = make_data(
        name=" kubernetes ",
        description="   ",
        primary_language=" Go ",
        default_branch=" master ",
        license_name="",
    )

    normalized = normalize_repository(data)

    assert normalized.name == "kubernetes"
    assert normalized.description is None
    assert normalized.primary_language == "Go"
    assert normalized.default_branch == "master"
    assert normalized.license_name is None


def test_store_keeps_the_timestamps_reported_by_github(session) -> None:
    """Regression: created_at/updated_at used to be replaced by the local write time."""

    repository = store_repository(session, make_data(), make_technology(session))

    assert repository.created_at == GITHUB_CREATED
    assert repository.updated_at == GITHUB_UPDATED
    assert repository.pushed_at == GITHUB_PUSHED
    assert repository.last_collected_at is not None
    assert repository.last_collected_at > GITHUB_UPDATED


def test_store_creates_repository_and_first_snapshot(session) -> None:
    technology = make_technology(session)

    repository = store_repository(session, make_data(), technology)

    assert repository.technology_id == technology.id
    assert repository.license_name == "Apache License 2.0"
    snapshots = session.scalars(select(RepositorySnapshot)).all()
    assert [(s.stars, s.forks, s.open_issues) for s in snapshots] == [(100, 10, 5)]


def test_store_updates_the_repository_and_appends_snapshots(session) -> None:
    technology = make_technology(session)

    first = store_repository(session, make_data(), technology)
    second = store_repository(session, make_data(stars=150, open_issues=3), technology)

    assert second.id == first.id
    assert (second.stars, second.open_issues) == (150, 3)
    stars = [
        snapshot.stars
        for snapshot in session.scalars(
            select(RepositorySnapshot).order_by(RepositorySnapshot.collected_at)
        )
    ]
    assert stars == [100, 150]


def test_collect_repository_runs_the_full_pipeline(session) -> None:
    class FakeClient:
        def fetch_repository(self, full_name: str) -> GitHubRepositoryData:
            assert full_name == "kubernetes/kubernetes"
            return make_data(description="  padded  ")

    repository = collect_repository(
        session, FakeClient(), make_technology(session), "kubernetes/kubernetes"
    )

    assert repository.description == "padded"


def test_collect_repository_propagates_failures(session) -> None:
    class FailingClient:
        def fetch_repository(self, full_name: str):
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        collect_repository(session, FailingClient(), make_technology(session), "a/b")
