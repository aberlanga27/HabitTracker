"""habit schedules: schedule with a daily row for every existing habit

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-26
"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

from app.core.ids import new_id

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    schedule = op.create_table(
        "schedule",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "habit_id", sa.String(), sa.ForeignKey("habit.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("weekdays", sa.Integer(), nullable=False),
        sa.Column("times_per_week", sa.Integer(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.UniqueConstraint("habit_id", "effective_from", name="uq_schedule_habit_effective_from"),
    )
    op.create_index("ix_schedule_habit_id", "schedule", ["habit_id"])

    habits = op.get_bind().execute(sa.text("SELECT id, date(created_at) FROM habit")).all()
    if habits:
        op.bulk_insert(
            schedule,
            [
                {
                    "id": new_id(),
                    "habit_id": habit_id,
                    "type": "daily",
                    "weekdays": 0,
                    "times_per_week": None,
                    "effective_from": date.fromisoformat(created),
                }
                for habit_id, created in habits
            ],
        )


def downgrade() -> None:
    op.drop_table("schedule")
