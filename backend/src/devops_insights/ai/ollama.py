import httpx
from ollama import Client, ResponseError

from devops_insights.ai.errors import AIServiceError
from devops_insights.core.config import get_settings

OLLAMA_ERRORS = (ResponseError, ConnectionError, TimeoutError, OSError, httpx.HTTPError)


def create_ollama_client() -> Client:
    """Create an Ollama client using application settings."""

    settings = get_settings()

    return Client(host=settings.ollama_base_url, timeout=settings.ollama_timeout)


def generate_response(prompt: str) -> str:
    """Generate a response from the configured Ollama model.

    Reasoning ("thinking") output is disabled: the analysis format is strict and the
    application only stores the final answer.
    """

    settings = get_settings()

    try:
        response = create_ollama_client().chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            think=False,
            options={"temperature": 0.2},
        )
    except OLLAMA_ERRORS as exc:
        raise AIServiceError(f"Ollama request failed: {exc}") from exc

    return response["message"]["content"]
