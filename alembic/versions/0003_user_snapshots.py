"""add username/full_name snapshots to registrations and questions

Revision ID: 0003_snapshot_user_in_reg_questions
Revises: 0002_seed_lectures
Create Date: 2026-05-05 13:55:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_user_snapshots"
down_revision: str | None = "0002_seed_lectures"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("registrations") as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column("full_name", sa.String(length=256), nullable=False, server_default=sa.text("''"))
        )

    with op.batch_alter_table("questions") as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column("full_name", sa.String(length=256), nullable=False, server_default=sa.text("''"))
        )

    op.execute(
        """
        UPDATE registrations
        SET username = (
                SELECT users.username
                FROM users
                WHERE users.tg_user_id = registrations.user_id
            ),
            full_name = COALESCE(
                (
                    SELECT users.full_name
                    FROM users
                    WHERE users.tg_user_id = registrations.user_id
                ),
                ''
            )
        """
    )
    op.execute(
        """
        UPDATE questions
        SET username = (
                SELECT users.username
                FROM users
                WHERE users.tg_user_id = questions.user_id
            ),
            full_name = COALESCE(
                (
                    SELECT users.full_name
                    FROM users
                    WHERE users.tg_user_id = questions.user_id
                ),
                ''
            )
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.drop_column("full_name")
        batch_op.drop_column("username")

    with op.batch_alter_table("registrations") as batch_op:
        batch_op.drop_column("full_name")
        batch_op.drop_column("username")
