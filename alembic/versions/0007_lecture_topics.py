"""add lecture topics field

Revision ID: 0007_lecture_topics
Revises: 0006_app_settings
Create Date: 2026-05-05 23:58:00.000000
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_lecture_topics"
down_revision: str | None = "0006_app_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lectures", sa.Column("topics", sa.Text(), nullable=True))

    lectures = sa.table(
        "lectures",
        sa.column("number", sa.Integer),
        sa.column("topics", sa.Text),
    )
    topics_by_number = {
        1: "1. Безопасность WEB приложений\n2. Проблемы использования LLM и безопасность кода",
        2: "3. Безопасность Linux\n4. Безопасная настройка Docker",
        3: (
            "5. Анализ исходного кода и сборки\n"
            "6. Secure Coding Guidelines\n"
            "7. Безопасность цепочек поставок ПО\n"
            "8. Семейство уязвимостей и угроз"
        ),
        4: "9. Как работать с фреймворками для РБПО\n10. Безопасность многопоточных приложений",
        5: "13. Архитектурные концепции ИБ систем\n14. Секретная лекция от Дмитрия про архитектуру",
        6: "15. Безопасность микросервисной архитектуры",
        7: "16. Безопасность в брокерах сообщений",
        8: "17. BYOD проблемы ИБ\n18. Управление персоналом и социальная инженерия",
        9: "19. Управление доступом, IAM\n20.Телеметрия и мониторинг ИБ",
    }
    for number, topics in topics_by_number.items():
        op.execute(lectures.update().where(lectures.c.number == number).values(topics=topics))


def downgrade() -> None:
    op.drop_column("lectures", "topics")
