"""unified click events and click type settings

Revision ID: 0004_click_events_unified
Revises: 0003_user_snapshots
Create Date: 2026-05-05 14:30:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_click_events_unified"
down_revision: str | None = "0003_user_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CLICK_EVENT_VALUES = (
    "stream_link",
    "materials_general",
    "materials_lecture",
    "registration_click",
)


def upgrade() -> None:
    click_event_type = sa.Enum(*CLICK_EVENT_VALUES, name="click_event_type", native_enum=False)

    op.create_table(
        "click_event_settings",
        sa.Column("event_type", click_event_type, primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "click_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.tg_user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("lecture_id", sa.Integer(), sa.ForeignKey("lectures.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", click_event_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    settings_table = sa.table(
        "click_event_settings",
        sa.column("event_type", click_event_type),
        sa.column("enabled", sa.Boolean),
    )
    op.bulk_insert(
        settings_table,
        [{"event_type": event_type, "enabled": True} for event_type in CLICK_EVENT_VALUES],
    )

    op.execute(
        """
        INSERT INTO click_events (user_id, lecture_id, event_type, created_at)
        SELECT user_id, lecture_id, 'stream_link', clicked_at
        FROM link_clicks
        """
    )


def downgrade() -> None:
    op.drop_table("click_events")
    op.drop_table("click_event_settings")
