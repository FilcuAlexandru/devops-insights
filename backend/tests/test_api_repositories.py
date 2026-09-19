import uuid

import pytest

from tests.factories import add_snapshot, make_repository, make_technology


@pytest.fixture
def seeded(session):
    kubernetes = make_technology(session, "kubernetes", name="Kubernetes")
    docker = make_technology(session, "docker", name="Docker")

    return {
        "main": make_repository(
            session, kubernetes, "k/main", stars=900, forks=5, description="Orchestrator"
        ),
        "kind": make_repository(
            session, kubernetes, "k/kind", stars=300, forks=50, description="Clusters in Docker"
        ),
        "engine": make_repository(
            session, docker, "d/engine", stars=600, forks=20, description="100% container_engine"
        ),
    }


def names(response) -> list[str]:
    return [item["full_name"] for item in response.json()]


def test_list_defaults_to_most_starred_first(client, seeded) -> None:
    assert names(client.get("/api/repositories")) == ["k/main", "d/engine", "k/kind"]


def test_list_can_be_filtered_by_technology(client, seeded) -> None:
    assert names(client.get("/api/repositories?technology=docker")) == ["d/engine"]


def test_list_can_be_sorted(client, seeded) -> None:
    assert names(client.get("/api/repositories?sort=forks")) == ["k/kind", "d/engine", "k/main"]
    assert names(client.get("/api/repositories?sort=name&order=asc")) == [
        "d/engine",
        "k/kind",
        "k/main",
    ]


def test_search_matches_name_and_description_case_insensitively(client, seeded) -> None:
    assert names(client.get("/api/repositories?search=KIND")) == ["k/kind"]
    assert names(client.get("/api/repositories?search=docker")) == ["k/kind"]


def test_search_treats_wildcards_literally(client, seeded) -> None:
    assert names(client.get("/api/repositories?search=100%25")) == ["d/engine"]
    assert names(client.get("/api/repositories?search=%25")) == ["d/engine"]
    assert names(client.get("/api/repositories?search=container_engine")) == ["d/engine"]
    assert names(client.get("/api/repositories?search=containerXengine")) == []


def test_invalid_sort_is_rejected(client, seeded) -> None:
    assert client.get("/api/repositories?sort=colour").status_code == 422


def test_get_returns_upstream_metadata(client, seeded) -> None:
    body = client.get(f"/api/repositories/{seeded['main'].id}").json()

    assert body["full_name"] == "k/main"
    assert body["technology_name"] == "Kubernetes"
    assert body["license_name"] == "Apache License 2.0"
    assert body["archived"] is False
    assert body["pushed_at"] is not None


def test_get_unknown_repository_is_404(client) -> None:
    assert client.get(f"/api/repositories/{uuid.uuid4()}").status_code == 404


def test_get_with_an_invalid_id_is_rejected(client) -> None:
    assert client.get("/api/repositories/not-a-uuid").status_code == 422


def test_snapshots_are_returned_oldest_first(client, session, seeded) -> None:
    repository = seeded["main"]
    add_snapshot(session, repository, days=2, stars=30)
    add_snapshot(session, repository, days=0, stars=10)
    add_snapshot(session, repository, days=1, stars=20)

    body = client.get(f"/api/repositories/{repository.id}/snapshots").json()

    assert [snapshot["stars"] for snapshot in body] == [10, 20, 30]


def test_snapshots_of_unknown_repository_is_404(client) -> None:
    assert client.get(f"/api/repositories/{uuid.uuid4()}/snapshots").status_code == 404


def test_trend_summarizes_snapshots(client, session, seeded) -> None:
    repository = seeded["main"]
    add_snapshot(session, repository, days=0, stars=100, forks=10, open_issues=5)
    add_snapshot(session, repository, days=10, stars=150, forks=12, open_issues=4)

    body = client.get(f"/api/repositories/{repository.id}/trend").json()

    assert body["snapshot_count"] == 2
    assert body["change"] == {"stars": 50, "forks": 2, "open_issues": -1}
    assert body["stars_per_day"] == 5.0


def test_trend_without_snapshots_is_empty(client, seeded) -> None:
    body = client.get(f"/api/repositories/{seeded['main'].id}/trend").json()

    assert body["snapshot_count"] == 0
    assert body["stars_per_day"] is None
