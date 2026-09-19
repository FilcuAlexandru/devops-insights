import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devops_insights.models.base import Base

if TYPE_CHECKING:
    from devops_insights.models.repository_snapshot import RepositorySnapshot
    from devops_insights.models.technology import Technology


class Repository(Base):
    """The latest known state of a source code repository.

    ``created_at``, ``updated_at`` and ``pushed_at`` are the timestamps reported by the
    upstream platform (GitHub), not the times the row was written. ``last_collected_at``
    records when this platform last refreshed the row.
    """

    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    technology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("technologies.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), nullable=False, default="main")
    primary_language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    stars: Mapped[int] = mapped_column(nullable=False, default=0)
    forks: Mapped[int] = mapped_column(nullable=False, default=0)
    open_issues: Mapped[int] = mapped_column(nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    technology: Mapped["Technology"] = relationship(back_populates="repositories")
    snapshots: Mapped[list["RepositorySnapshot"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
