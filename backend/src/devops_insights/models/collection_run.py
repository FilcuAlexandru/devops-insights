import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from devops_insights.models.base import Base, utc_now


class CollectionStatus(StrEnum):
    """Lifecycle states of a collection run."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class CollectionTrigger(StrEnum):
    """What started a collection run."""

    SCHEDULE = "schedule"
    MANUAL = "manual"
    CLI = "cli"


class CollectionRun(Base):
    """One execution of the data collection pipeline across the catalog."""

    __tablename__ = "collection_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trigger: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CollectionStatus.RUNNING
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    errors: Mapped[list[dict[str, str]]] = mapped_column(JSONB, nullable=False, default=list)
