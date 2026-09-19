from datetime import timedelta

import pytest
from sqlalchemy import func, select

from devops_insights.catalog import TechnologyDefinition
from devops_insights.collectors.github import GitHubError, GitHubRateLimitError
from devops_insights.models import (
    CollectionRun,
    CollectionStatus,
    CollectionTrigger,
    Repository,
)
from devops_insights.models.base import utc_now
from devops_insights.services.collection import (
    create_run,
    execute_run,
    get_active_run,
    run_collection,
)
from tests.test_pipeline import make_data

CATALOG = (
    TechnologyDefinition("alpha", "Alpha", "testing", "A.", "https://a.test", ("o/one", "o/two")),
    TechnologyDefinition("beta", "Beta", "testing", "B.", "https://b.test", ("o/three",)),
)


class FakeClient:
    """Returns data for every repository except those listed in ``failures``."""

    def __init__(self, failures: dict[str, Exception] | None = None) -> None:
        self.failures = failures or {}
        self.requested: list[str] = []

    def fetch_repository(self, full_name: str):
        self.requested.append(full_name)

        if full_name in self.failures:
            raise self.failures[full_name]

        return make_data(name=full_name.split("/")[1], full_name=full_name)


def run(session, session_factory, client, catalog=CATALOG):
    created = create_run(session, CollectionTrigger.MANUAL, catalog)

    return execute_run(created.id, client, session_factory, catalog)


def test_successful_run_collects_every_repository(session, session_factory) -> None:
    client = FakeClient()

    summary = run(session, session_factory, client)

    assert summary.status is CollectionStatus.SUCCEEDED
    assert (summary.total, summary.succeeded, summary.failed) == (3, 3, 0)
    assert client.requested == ["o/one", "o/two", "o/three"]
    assert session.scalar(select(func.count(Repository.id))) == 3


def test_run_is_recorded_with_its_outcome(session, session_factory) -> None:
    summary = run(session, session_factory, FakeClient())

    stored = session.get(CollectionRun, summary.run_id)
    assert stored.trigger == CollectionTrigger.MANUAL
    assert stored.status == CollectionStatus.SUCCEEDED
    assert stored.finished_at is not None
    assert stored.errors == []


def test_a_failing_repository_does_not_stop_the_others(session, session_factory) -> None:
    client = FakeClient({"o/two": GitHubError("Repository 'o/two' was not found on GitHub.")})

    summary = run(session, session_factory, client)

    assert summary.status is CollectionStatus.PARTIAL
    assert (summary.succeeded, summary.failed) == (2, 1)
    assert client.requested == ["o/one", "o/two", "o/three"]
    stored = session.get(CollectionRun, summary.run_id)
    assert stored.errors == [
        {"repository": "o/two", "error": "Repository 'o/two' was not found on GitHub."}
    ]


def test_run_fails_when_every_repository_fails(session, session_factory) -> None:
    client = FakeClient({name: GitHubError("boom") for name in ("o/one", "o/two", "o/three")})

    summary = run(session, session_factory, client)

    assert summary.status is CollectionStatus.FAILED
    assert (summary.succeeded, summary.failed) == (0, 3)


def test_rate_limit_stops_the_run_and_reports_the_remaining_repositories(
    session, session_factory
) -> None:
    client = FakeClient({"o/two": GitHubRateLimitError("rate limit exceeded")})

    summary = run(session, session_factory, client)

    assert summary.status is CollectionStatus.PARTIAL
    assert client.requested == ["o/one", "o/two"]
    stored = session.get(CollectionRun, summary.run_id)
    assert [error["repository"] for error in stored.errors] == ["o/two", "o/three"]


def test_run_collection_creates_and_executes_a_run(session, session_factory) -> None:
    summary = run_collection(CollectionTrigger.CLI, FakeClient(), session_factory, CATALOG)

    assert summary.status is CollectionStatus.SUCCEEDED
    assert session.get(CollectionRun, summary.run_id).trigger == CollectionTrigger.CLI


def test_get_active_run_returns_a_run_in_progress(session) -> None:
    created = create_run(session, CollectionTrigger.MANUAL)

    assert get_active_run(session).id == created.id


def test_get_active_run_ignores_finished_runs(session, session_factory) -> None:
    run(session, session_factory, FakeClient())

    assert get_active_run(session) is None


def test_stale_runs_are_marked_as_failed(session) -> None:
    stale = create_run(session, CollectionTrigger.MANUAL)
    stale.started_at = utc_now() - timedelta(hours=2)
    session.commit()

    assert get_active_run(session) is None
    session.refresh(stale)
    assert stale.status == CollectionStatus.FAILED
    assert stale.finished_at is not None
    assert stale.errors[0]["error"] == "Run was interrupted."


@pytest.mark.parametrize(
    ("succeeded", "failed", "expected"),
    [
        (3, 0, CollectionStatus.SUCCEEDED),
        (2, 1, CollectionStatus.PARTIAL),
        (0, 3, CollectionStatus.FAILED),
    ],
)
def test_status_resolution(succeeded, failed, expected) -> None:
    from devops_insights.services.collection import _resolve_status

    assert _resolve_status(succeeded, failed) is expected


def test_unexpected_errors_mark_the_run_as_failed(session, session_factory, monkeypatch) -> None:
    created = create_run(session, CollectionTrigger.MANUAL, CATALOG)

    def broken_sync(*args, **kwargs):
        raise RuntimeError("database went away")

    monkeypatch.setattr("devops_insights.services.collection.sync_catalog", broken_sync)

    with pytest.raises(RuntimeError, match="database went away"):
        execute_run(created.id, FakeClient(), session_factory, CATALOG)

    stored = session.get(CollectionRun, created.id)
    assert stored.status == CollectionStatus.FAILED
    assert stored.finished_at is not None
    assert stored.errors == [{"repository": "*", "error": "database went away"}]
