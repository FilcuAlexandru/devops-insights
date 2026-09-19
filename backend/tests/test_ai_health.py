from types import SimpleNamespace

import httpx
from ollama import ResponseError

from devops_insights.ai.health import OllamaHealth, check_ollama_health


def fake_client(models=None, error: Exception | None = None):
    def _list():
        if error:
            raise error

        return SimpleNamespace(models=[SimpleNamespace(model=name) for name in models or []])

    return SimpleNamespace(list=_list)


def patch_client(monkeypatch, client) -> None:
    monkeypatch.setattr("devops_insights.ai.health.create_ollama_client", lambda: client)


def test_ready_when_the_model_is_installed(monkeypatch) -> None:
    patch_client(monkeypatch, fake_client(["other:1b", "qwen3:1.7b"]))

    health = check_ollama_health()

    assert health.ready
    assert health.error is None


def test_model_missing_is_reported_with_the_fix(monkeypatch) -> None:
    patch_client(monkeypatch, fake_client(["other:1b"]))

    health = check_ollama_health()

    assert health.available
    assert not health.model_available
    assert not health.ready
    assert "ollama pull qwen3:1.7b" in health.error


def test_unreachable_service_is_reported(monkeypatch) -> None:
    patch_client(monkeypatch, fake_client(error=ConnectionError("refused")))

    health = check_ollama_health()

    assert not health.available
    assert health.error == "refused"


def test_http_timeouts_are_handled(monkeypatch) -> None:
    """Regression: httpx timeouts used to escape and produce a 500."""

    patch_client(monkeypatch, fake_client(error=httpx.ReadTimeout("slow")))

    assert not check_ollama_health().available


def test_api_errors_are_handled(monkeypatch) -> None:
    patch_client(monkeypatch, fake_client(error=ResponseError("boom", 500)))

    assert not check_ollama_health().available


def test_ready_requires_both_conditions() -> None:
    assert not OllamaHealth(available=True, model_available=False, model="m").ready
    assert not OllamaHealth(available=False, model_available=False, model="m").ready
