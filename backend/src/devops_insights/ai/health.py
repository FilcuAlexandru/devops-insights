from dataclasses import dataclass

from devops_insights.ai.ollama import OLLAMA_ERRORS, create_ollama_client
from devops_insights.core.config import get_settings


@dataclass(frozen=True)
class OllamaHealth:
    """The health status of the Ollama service."""

    available: bool
    model_available: bool
    model: str
    error: str | None = None

    @property
    def ready(self) -> bool:
        """Return whether Ollama is ready for AI requests."""

        return self.available and self.model_available


def check_ollama_health() -> OllamaHealth:
    """Check Ollama availability and whether the configured model is installed."""

    model = get_settings().ollama_model

    try:
        installed = create_ollama_client().list().models
    except OLLAMA_ERRORS as exc:
        return OllamaHealth(available=False, model_available=False, model=model, error=str(exc))

    if not any(installed_model.model == model for installed_model in installed):
        return OllamaHealth(
            available=True,
            model_available=False,
            model=model,
            error=f"Model '{model}' is not installed. Run: ollama pull {model}",
        )

    return OllamaHealth(available=True, model_available=True, model=model)
