import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devops_insights.models.base import Base, utc_now

if TYPE_CHECKING:
    from devops_insights.models.repository import Repository


class RepositorySnapshot(Base):
    """A point-in-time snapshot of repository statistics."""

    __tablename__ = "repository_snapshots"
    __table_args__ = (
        Index(
            "ix_repository_snapshots_repository_id_collected_at", "repository_id", "collected_at"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )

    stars: Mapped[int] = mapped_column(nullable=False, default=0)
    forks: Mapped[int] = mapped_column(nullable=False, default=0)
    open_issues: Mapped[int] = mapped_column(nullable=False, default=0)

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    repository: Mapped["Repository"] = relationship(back_populates="snapshots")
