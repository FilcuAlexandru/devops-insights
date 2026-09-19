import pytest

from devops_insights.models import CollectionTrigger
from devops_insights.services.collection import create_run


@pytest.fixture
def executed(monkeypatch) -> list:
    """Replace the real background execution (which would call GitHub)."""

    runs: list = []
    monkeypatch.setattr("devops_insights.api.routes.collection._execute_in_background", runs.append)

    return runs


def test_starting_a_run_returns_it_immediately(client, executed) -> None:
    response = client.post("/api/collection/run")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "running"
    assert body["trigger"] == "manual"
    assert body["total"] > 0
    assert [str(run_id) for run_id in executed] == [body["id"]]


def test_only_one_run_can_be_active(client, session, executed) -> None:
    create_run(session, CollectionTrigger.SCHEDULE)

    response = client.post("/api/collection/run")

    assert response.status_code == 409
    assert executed == []


def test_runs_are_listed_newest_first(client, session) -> None:
    older = create_run(session, CollectionTrigger.SCHEDULE)
    older.status = "succeeded"
    session.commit()
    newer = create_run(session, CollectionTrigger.MANUAL)

    body = client.get("/api/collection/runs").json()

    assert [run["id"] for run in body] == [str(newer.id), str(older.id)]
    assert body[0]["errors"] == []


def test_run_limit_is_validated(client) -> None:
    assert client.get("/api/collection/runs?limit=0").status_code == 422
