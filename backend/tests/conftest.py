"""Shared test fixtures.

Tests run against a dedicated ``<database>_test`` PostgreSQL database that is created and
migrated automatically, so a developer's real data is never touched. Every test runs inside
a transaction that is rolled back afterwards.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

DEFAULT_DATABASE_URL = "postgresql+psycopg://admin:admin@localhost:5432/devops_insights"


def _prepare_test_database() -> str:
    base_url = make_url(os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))
    test_url = base_url.set(database=f"{base_url.database}_test")

    admin_engine = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": test_url.database}
        )

        if not exists:
            connection.execute(text(f'CREATE DATABASE "{test_url.database}"'))

    admin_engine.dispose()

    return test_url.render_as_string(hide_password=False)


os.environ["DATABASE_URL"] = _prepare_test_database()
os.environ.pop("GITHUB_TOKEN", None)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from devops_insights.api.app import create_app  # noqa: E402
from devops_insights.core.database import engine, get_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> None:
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")


@pytest.fixture
def session() -> Iterator[Session]:
    """A session whose work is rolled back at the end of the test."""

    connection = engine.connect()
    transaction = connection.begin()
    test_session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )

    try:
        yield test_session
    finally:
        test_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def session_factory(session: Session):
    """A session factory that always hands out the test session."""

    class _NonClosingSession:
        def __enter__(self) -> Session:
            return session

        def __exit__(self, *exc_info) -> None:
            session.flush()

    return _NonClosingSession


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture
def client(app, session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: session

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
