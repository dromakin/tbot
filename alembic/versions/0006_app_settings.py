"""add app settings key-value storage

Revision ID: 0006_app_settings
Revises: 0005_questions_moderation_fields
Create Date: 2026-05-05 20:55:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_app_settings"
down_revision: str | None = "0005_questions_moderation_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    settings_table = sa.table(
        "app_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
    )
    op.bulk_insert(
        settings_table,
        [{"key": "general_materials_url", "value": "https://example.com/general-materials"}],
    )


def downgrade() -> None:
    op.drop_table("app_settings")
