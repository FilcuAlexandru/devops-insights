from tests.factories import make_repository, make_technology


def test_list_is_empty_without_data(client) -> None:
    assert client.get("/api/technologies").json() == []


def test_list_includes_repository_aggregates(client, session) -> None:
    kubernetes = make_technology(
        session, "kubernetes", name="Kubernetes", description="Orchestration."
    )
    make_technology(session, "docker", name="Docker")
    make_repository(session, kubernetes, "k/one", stars=10)
    make_repository(session, kubernetes, "k/two", stars=5)

    body = client.get("/api/technologies").json()

    assert [item["slug"] for item in body] == ["docker", "kubernetes"]
    assert (body[0]["repository_count"], body[0]["total_stars"]) == (0, 0)
    assert (body[1]["repository_count"], body[1]["total_stars"]) == (2, 15)
    assert body[1]["description"] == "Orchestration."


def test_get_returns_the_technology_with_its_repositories(client, session) -> None:
    kubernetes = make_technology(session, "kubernetes", name="Kubernetes")
    make_repository(session, kubernetes, "k/small", stars=1)
    make_repository(session, kubernetes, "k/big", stars=9)
    make_repository(session, make_technology(session), "other/repo")

    body = client.get("/api/technologies/kubernetes").json()

    assert body["name"] == "Kubernetes"
    assert [repo["full_name"] for repo in body["repositories"]] == ["k/big", "k/small"]
    assert body["repositories"][0]["technology_slug"] == "kubernetes"


def test_get_unknown_technology_is_404(client) -> None:
    response = client.get("/api/technologies/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Technology not found."
