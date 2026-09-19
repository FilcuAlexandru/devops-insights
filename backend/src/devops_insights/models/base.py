from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


def utc_now() -> datetime:
    """Return the current UTC datetime."""

    return datetime.now(UTC)
