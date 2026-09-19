"""create ai analyses table

Revision ID: c48d19760b59
Revises: e9d090b436f9
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c48d19760b59"
down_revision: str | None = "e9d090b436f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the ai_analyses table."""

    op.create_table(
        "ai_analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "model",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "prompt",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "context",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "response",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ai_analyses_repository_id",
        "ai_analyses",
        ["repository_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the ai_analyses table."""

    op.drop_index(
        "ix_ai_analyses_repository_id",
        table_name="ai_analyses",
    )

    op.drop_table("ai_analyses")
