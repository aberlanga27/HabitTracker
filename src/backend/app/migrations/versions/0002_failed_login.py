"""user accounts: failed_login for sign-in lockout

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.db import UTCDateTime

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "failed_login",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("attempted_at", UTCDateTime(), nullable=False),
    )
    op.create_index("ix_failed_login_email", "failed_login", ["email"])


def downgrade() -> None:
    op.drop_table("failed_login")
