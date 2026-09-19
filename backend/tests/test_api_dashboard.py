from tests.factories import make_repository, make_technology


def test_dashboard_is_available_without_data(client) -> None:
    body = client.get("/api/dashboard").json()

    assert body["totals"]["repositories"] == 0
    assert body["last_collection"] is None


def test_dashboard_reports_totals_and_rankings(client, session) -> None:
    technology = make_technology(session, "kubernetes", name="Kubernetes")
    make_repository(session, technology, "k/big", stars=50, forks=5)
    make_repository(session, technology, "k/small", stars=10, forks=1)

    body = client.get("/api/dashboard").json()

    assert body["totals"]["stars"] == 60
    assert [item["full_name"] for item in body["top_repositories"]] == ["k/big", "k/small"]
    assert body["technologies"][0] == {
        "slug": "kubernetes",
        "name": "Kubernetes",
        "repository_count": 2,
        "stars": 60,
    }


def test_dashboard_can_be_limited_to_a_technology(client, session) -> None:
    make_repository(session, make_technology(session, "docker"), "d/one", stars=5)
    make_repository(session, make_technology(session, "helm"), "h/one", stars=7)

    body = client.get("/api/dashboard?technology=helm").json()

    assert body["totals"]["repositories"] == 1
    assert body["top_repositories"][0]["full_name"] == "h/one"


def test_dashboard_for_unknown_technology_is_404(client) -> None:
    assert client.get("/api/dashboard?technology=missing").status_code == 404
