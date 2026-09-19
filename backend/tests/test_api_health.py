def test_liveness(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_the_database(client) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics_endpoint_exposes_custom_metrics(client) -> None:
    client.get("/api/technologies")

    body = client.get("/metrics").text

    assert "devops_insights_application_info" in body
    assert "devops_insights_repositories_collected_total" in body
    assert "devops_insights_ai_analysis_duration_seconds" in body
    assert "devops_insights_database_query_duration_seconds" in body
    assert "http_request_duration_seconds" in body


def test_openapi_documentation_is_served_under_api(client) -> None:
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").json()["info"]["title"] == "DevOps Insights"
