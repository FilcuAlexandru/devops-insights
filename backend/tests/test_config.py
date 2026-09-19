from devops_insights.core.config import Settings


def test_defaults_use_admin_credentials_and_local_services(monkeypatch) -> None:
    for variable in ("DATABASE_URL", "OLLAMA_BASE_URL", "COLLECTION_INTERVAL_SECONDS"):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert (
        settings.database_url == "postgresql+psycopg://admin:admin@localhost:5432/devops_insights"
    )
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.collection_interval_seconds == 21600


def test_blank_github_token_means_unauthenticated() -> None:
    assert Settings(_env_file=None, github_token="").github_token is None


def test_github_token_is_kept() -> None:
    assert Settings(_env_file=None, github_token="abc").github_token == "abc"
