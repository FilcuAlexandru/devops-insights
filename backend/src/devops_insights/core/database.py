from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from devops_insights.core.config import get_settings
from devops_insights.observability.metrics import instrument_database_engine

engine = create_engine(get_settings().database_url, pool_pre_ping=True)

instrument_database_engine(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it after use."""

    with SessionLocal() as session:
        yield session
