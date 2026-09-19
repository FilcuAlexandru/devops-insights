"""add collection runs and repository metadata

Adds the ``collection_runs`` table, the upstream metadata columns of ``repositories``
(license, archived flag, last push, last collection time) and an index for snapshot
history queries. Snapshots are now deleted together with their repository.

Revision ID: 7c1e5a2d9b34
Revises: c48d19760b59
Create Date: 2026-09-19 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7c1e5a2d9b34"
down_revision: str | Sequence[str] | None = "c48d19760b59"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trigger", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("succeeded", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
        sa.Column("errors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_collection_runs_started_at"),
        "collection_runs",
        ["started_at"],
        unique=False,
    )

    op.add_column("repositories", sa.Column("license_name", sa.String(length=200), nullable=True))
    op.add_column(
        "repositories",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("repositories", "archived", server_default=None)
    op.add_column("repositories", sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "repositories", sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        """
        UPDATE repositories
        SET last_collected_at = (
            SELECT max(collected_at)
            FROM repository_snapshots
            WHERE repository_snapshots.repository_id = repositories.id
        )
        """
    )

    op.create_index(
        "ix_repository_snapshots_repository_id_collected_at",
        "repository_snapshots",
        ["repository_id", "collected_at"],
        unique=False,
    )
    op.drop_constraint(
        "repository_snapshots_repository_id_fkey", "repository_snapshots", type_="foreignkey"
    )
    op.create_foreign_key(
        "repository_snapshots_repository_id_fkey",
        "repository_snapshots",
        "repositories",
        ["repository_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "repository_snapshots_repository_id_fkey", "repository_snapshots", type_="foreignkey"
    )
    op.create_foreign_key(
        "repository_snapshots_repository_id_fkey",
        "repository_snapshots",
        "repositories",
        ["repository_id"],
        ["id"],
    )
    op.drop_index(
        "ix_repository_snapshots_repository_id_collected_at", table_name="repository_snapshots"
    )

    op.drop_column("repositories", "last_collected_at")
    op.drop_column("repositories", "pushed_at")
    op.drop_column("repositories", "archived")
    op.drop_column("repositories", "license_name")

    op.drop_index(op.f("ix_collection_runs_started_at"), table_name="collection_runs")
    op.drop_table("collection_runs")
