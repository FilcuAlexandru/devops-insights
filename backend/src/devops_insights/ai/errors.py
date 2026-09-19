class AIServiceError(RuntimeError):
    """The Ollama service could not be reached or rejected the request."""


class InvalidAIResponseError(ValueError):
    """The model answered, but not in the required format."""
