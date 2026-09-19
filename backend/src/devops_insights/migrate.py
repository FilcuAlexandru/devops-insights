"""Apply database migrations, waiting for PostgreSQL to accept connections first.

    python -m devops_insights.migrate

Used by Docker Compose, Kubernetes (init container) and OpenShift. Several processes may run
it at the same time: migrations take a PostgreSQL advisory lock (see migrations/env.py).
"""

import logging
import time

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError

from devops_insights.core.database import engine
from devops_insights.core.logging import configure_logging

logger = logging.getLogger("devops_insights.migrate")

DEFAULT_TIMEOUT_SECONDS = 180
RETRY_INTERVAL_SECONDS = 2


def wait_for_database(
    database: Engine = engine,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    interval: float = RETRY_INTERVAL_SECONDS,
) -> None:
    """Block until the database accepts connections, or raise after ``timeout`` seconds."""

    deadline = time.monotonic() + timeout

    while True:
        try:
            with database.connect() as connection:
                connection.execute(text("SELECT 1"))
        except OperationalError as exc:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Database not reachable after {timeout:.0f}s.") from exc

            logger.info("Waiting for the database...")
            time.sleep(interval)
        else:
            return


def main() -> int:
    """Wait for the database, then upgrade it to the latest revision."""

    configure_logging()
    wait_for_database()
    command.upgrade(Config("alembic.ini"), "head")
    logger.info("Database is up to date.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
