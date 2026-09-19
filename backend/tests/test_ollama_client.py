import pytest

from devops_insights.ai import ollama
from devops_insights.ai.errors import AIServiceError


class FakeClient:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict = {}

    def chat(self, **kwargs):
        self.kwargs = kwargs

        if self.error:
            raise self.error

        return self.response


def test_generate_response_disables_thinking_and_returns_the_content(monkeypatch) -> None:
    client = FakeClient({"message": {"content": "hello"}})
    monkeypatch.setattr(ollama, "create_ollama_client", lambda: client)

    assert ollama.generate_response("prompt") == "hello"
    assert client.kwargs["think"] is False
    assert client.kwargs["model"] == "qwen3:1.7b"
    assert client.kwargs["messages"] == [{"role": "user", "content": "prompt"}]


def test_generate_response_wraps_ollama_failures(monkeypatch) -> None:
    monkeypatch.setattr(ollama, "create_ollama_client", lambda: FakeClient(error=OSError("down")))

    with pytest.raises(AIServiceError, match="Ollama request failed: down"):
        ollama.generate_response("prompt")
