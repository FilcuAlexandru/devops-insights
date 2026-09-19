from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "DevOps Insights"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://admin:admin@localhost:5432/devops_insights"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:1.7b"
    ollama_timeout: float = 120.0

    github_api_url: str = "https://api.github.com"
    github_token: str | None = None
    github_timeout: float = 15.0

    collection_interval_seconds: int = 21600
    collection_on_startup: bool = True
    collector_metrics_port: int = 9102

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("github_token", mode="before")
    @classmethod
    def _blank_token_means_unauthenticated(cls, value: str | None) -> str | None:
        """Treat an empty GITHUB_TOKEN variable as "no token configured"."""

        return value or None


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
