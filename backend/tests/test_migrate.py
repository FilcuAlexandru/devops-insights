import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from devops_insights.core.database import engine
from devops_insights.migrate import wait_for_database


def test_returns_immediately_when_the_database_is_reachable() -> None:
    wait_for_database(engine, timeout=5, interval=0.01)


def test_gives_up_after_the_timeout() -> None:
    unreachable = create_engine("postgresql+psycopg://admin:admin@127.0.0.1:1/none")

    with pytest.raises(TimeoutError, match="not reachable"):
        wait_for_database(unreachable, timeout=0.2, interval=0.05)


def test_retries_until_the_database_appears(monkeypatch) -> None:
    attempts = 0
    real_connect = engine.connect

    def flaky_connect():
        nonlocal attempts
        attempts += 1

        if attempts < 3:
            raise OperationalError("SELECT 1", {}, Exception("starting up"))

        return real_connect()

    monkeypatch.setattr(engine, "connect", flaky_connect)

    wait_for_database(engine, timeout=5, interval=0.01)

    assert attempts == 3
