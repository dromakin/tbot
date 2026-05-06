"""add configurable auto-close registration window

Revision ID: 0008_auto_close_registration
Revises: 0007_lecture_topics
Create Date: 2026-05-06 10:45:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_auto_close_registration"
down_revision: str | None = "0007_lecture_topics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lectures", sa.Column("registration_opened_at", sa.DateTime(timezone=True), nullable=True))

    lectures = sa.table(
        "lectures",
        sa.column("registration_open", sa.Boolean),
        sa.column("registration_opened_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        lectures.update()
        .where(lectures.c.registration_open.is_(True))
        .values(registration_opened_at=sa.text("CURRENT_TIMESTAMP"))
    )

    settings_table = sa.table(
        "app_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
    )
    op.bulk_insert(
        settings_table,
        [{"key": "auto_close_registration_hours", "value": "24"}],
    )


def downgrade() -> None:
    settings_table = sa.table(
        "app_settings",
        sa.column("key", sa.String),
    )
    op.execute(settings_table.delete().where(settings_table.c.key == "auto_close_registration_hours"))
    op.drop_column("lectures", "registration_opened_at")
