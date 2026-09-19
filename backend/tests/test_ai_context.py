import uuid

from devops_insights.ai.context import build_repository_context
from tests.factories import add_snapshot, make_repository, make_technology


def test_unknown_repository_has_no_context(session) -> None:
    assert build_repository_context(session, uuid.uuid4()) is None


def test_context_describes_technology_and_repository(session) -> None:
    technology = make_technology(session, "kubernetes", name="Kubernetes", category="orchestration")
    repository = make_repository(
        session, technology, "k/main", stars=42, archived=True, license_name="MIT"
    )

    context = build_repository_context(session, repository.id)

    assert context["technology"] == {
        "name": "Kubernetes",
        "slug": "kubernetes",
        "category": "orchestration",
    }
    assert context["repository"]["full_name"] == "k/main"
    assert context["repository"]["stars"] == 42
    assert context["repository"]["archived"] is True
    assert context["repository"]["license"] == "MIT"
    assert context["repository"]["pushed_at"].startswith("2026-01-01")


def test_context_without_snapshots_has_no_history(session) -> None:
    repository = make_repository(session, make_technology(session))

    metrics = build_repository_context(session, repository.id)["historical_metrics"]

    assert metrics["snapshot_count"] == 0
    assert metrics["oldest"] is None
    assert metrics["newest"] is None
    assert metrics["changes"] == {"stars": 0, "forks": 0, "open_issues": 0}


def test_a_single_snapshot_is_not_a_trend(session) -> None:
    repository = make_repository(session, make_technology(session))
    add_snapshot(session, repository, days=0, stars=100)

    metrics = build_repository_context(session, repository.id)["historical_metrics"]

    assert metrics["snapshot_count"] == 1
    assert metrics["changes"] == {"stars": 0, "forks": 0, "open_issues": 0}


def test_context_calculates_changes_between_oldest_and_newest(session) -> None:
    repository = make_repository(session, make_technology(session))
    add_snapshot(session, repository, days=2, stars=130, forks=14, open_issues=3)
    add_snapshot(session, repository, days=0, stars=100, forks=10, open_issues=5)
    add_snapshot(session, repository, days=1, stars=110, forks=11, open_issues=6)

    context = build_repository_context(session, repository.id)

    metrics = context["historical_metrics"]
    assert metrics["snapshot_count"] == 3
    assert metrics["oldest"]["stars"] == 100
    assert metrics["newest"]["stars"] == 130
    assert metrics["changes"] == {"stars": 30, "forks": 4, "open_issues": -2}
    assert [snapshot["stars"] for snapshot in context["snapshots"]] == [100, 110, 130]
