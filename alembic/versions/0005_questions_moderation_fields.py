"""add moderation fields to questions

Revision ID: 0005_questions_moderation_fields
Revises: 0004_click_events_unified
Create Date: 2026-05-05 14:35:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_questions_moderation_fields"
down_revision: str | None = "0004_click_events_unified"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    question_status = sa.Enum("pending", "ignored", "answered", name="question_status", native_enum=False)
    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                question_status,
                nullable=False,
                server_default=sa.text("'pending'"),
            )
        )
        batch_op.add_column(sa.Column("answer_text", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("answered_by_admin_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("answered_by_admin_username", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )

    op.execute("UPDATE questions SET status = 'pending' WHERE status IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("answered_by_admin_username")
        batch_op.drop_column("answered_by_admin_id")
        batch_op.drop_column("answer_text")
        batch_op.drop_column("status")
