from devops_insights import __version__
from devops_insights.ai.health import OllamaHealth
from devops_insights.models import CollectionTrigger
from devops_insights.services.collection import create_run


def test_status_reports_dependencies(client, session, monkeypatch) -> None:
    monkeypatch.setattr(
        "devops_insights.api.routes.system.check_ollama_health",
        lambda: OllamaHealth(available=False, model_available=False, model="m", error="down"),
    )
    create_run(session, CollectionTrigger.MANUAL)

    body = client.get("/api/status").json()

    assert body["version"] == __version__
    assert body["database_ok"] is True
    assert body["ollama"]["ready"] is False
    assert body["ollama"]["error"] == "down"
    assert body["last_collection"]["trigger"] == "manual"
