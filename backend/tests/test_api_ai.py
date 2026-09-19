import uuid
from datetime import timedelta

import pytest

from devops_insights.ai.errors import AIServiceError
from devops_insights.ai.health import OllamaHealth
from devops_insights.models import AIAnalysis
from tests.factories import BASE_TIME, make_repository, make_technology
from tests.test_ai_analysis import VALID_RESPONSE

READY = OllamaHealth(available=True, model_available=True, model="qwen3:1.7b")


@pytest.fixture
def repository(session):
    return make_repository(session, make_technology(session), "k/main")


def patch_health(monkeypatch, health: OllamaHealth) -> None:
    monkeypatch.setattr("devops_insights.api.routes.ai.check_ollama_health", lambda: health)


def patch_model(monkeypatch, response=VALID_RESPONSE, error: Exception | None = None) -> None:
    def fake_generate(prompt: str) -> str:
        if error:
            raise error

        return response

    monkeypatch.setattr("devops_insights.ai.analysis.generate_response", fake_generate)


def test_health_endpoint(client, monkeypatch) -> None:
    patch_health(monkeypatch, READY)

    assert client.get("/api/ai/health").json() == {
        "available": True,
        "model_available": True,
        "ready": True,
        "model": "qwen3:1.7b",
        "error": None,
    }


def test_analyze_persists_and_returns_the_analysis(client, repository, monkeypatch) -> None:
    patch_health(monkeypatch, READY)
    patch_model(monkeypatch)

    response = client.post(f"/api/ai/repositories/{repository.id}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["repository_id"] == str(repository.id)
    assert body["response"].startswith("## Summary")
    assert body["model"] == "qwen3:1.7b"

    history = client.get(f"/api/ai/repositories/{repository.id}/analyses").json()
    assert [item["id"] for item in history] == [body["id"]]


def test_analyze_unknown_repository_is_404(client, monkeypatch) -> None:
    patch_health(monkeypatch, READY)

    assert client.post(f"/api/ai/repositories/{uuid.uuid4()}/analyze").status_code == 404


def test_analyze_needs_a_running_ollama(client, repository, monkeypatch) -> None:
    patch_health(
        monkeypatch,
        OllamaHealth(available=False, model_available=False, model="m", error="refused"),
    )

    response = client.post(f"/api/ai/repositories/{repository.id}/analyze")

    assert response.status_code == 503
    assert response.json()["detail"] == "refused"


def test_analyze_needs_the_model_to_be_installed(client, repository, monkeypatch) -> None:
    patch_health(
        monkeypatch,
        OllamaHealth(available=True, model_available=False, model="m", error="Model 'm' missing"),
    )

    response = client.post(f"/api/ai/repositories/{repository.id}/analyze")

    assert response.status_code == 503
    assert "missing" in response.json()["detail"]


def test_analyze_reports_service_failures_as_503(client, repository, monkeypatch) -> None:
    patch_health(monkeypatch, READY)
    patch_model(monkeypatch, error=AIServiceError("model crashed"))

    response = client.post(f"/api/ai/repositories/{repository.id}/analyze")

    assert response.status_code == 503
    assert response.json()["detail"] == "model crashed"


def test_analyze_reports_unusable_output_as_502(client, repository, monkeypatch) -> None:
    patch_health(monkeypatch, READY)
    patch_model(monkeypatch, response="just chatting")

    response = client.post(f"/api/ai/repositories/{repository.id}/analyze")

    assert response.status_code == 502
    assert "invalid analysis" in response.json()["detail"]


def test_history_is_newest_first(client, session, repository, monkeypatch) -> None:
    patch_health(monkeypatch, READY)
    patch_model(monkeypatch)
    first = client.post(f"/api/ai/repositories/{repository.id}/analyze").json()
    second = client.post(f"/api/ai/repositories/{repository.id}/analyze").json()

    # PostgreSQL's now() is constant within a transaction, and the whole test is one.
    for offset, analysis in enumerate((first, second)):
        session.get(AIAnalysis, uuid.UUID(analysis["id"])).created_at = BASE_TIME + timedelta(
            minutes=offset
        )
    session.flush()

    history = client.get(f"/api/ai/repositories/{repository.id}/analyses").json()

    assert [item["id"] for item in history] == [second["id"], first["id"]]


def test_history_of_unknown_repository_is_404(client) -> None:
    assert client.get(f"/api/ai/repositories/{uuid.uuid4()}/analyses").status_code == 404


def test_dashboard_lists_recent_analyses_with_their_summary(
    client, repository, monkeypatch
) -> None:
    patch_health(monkeypatch, READY)
    patch_model(monkeypatch)
    client.post(f"/api/ai/repositories/{repository.id}/analyze")

    recent = client.get("/api/dashboard").json()["recent_analyses"]

    assert recent[0]["repository_full_name"] == "k/main"
    assert recent[0]["summary"] == "The repository is popular."
