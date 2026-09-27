"""daily check-in: check_in

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.db import UTCDateTime

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "check_in",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "habit_id", sa.String(), sa.ForeignKey("habit.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("completed_at", UTCDateTime(), nullable=False),
        sa.Column("note", sa.String(length=280), nullable=True),
        sa.UniqueConstraint("habit_id", "local_date", name="uq_check_in_habit_date"),
    )


def downgrade() -> None:
    op.drop_table("check_in")
