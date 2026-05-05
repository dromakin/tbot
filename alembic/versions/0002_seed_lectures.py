"""seed lectures

Revision ID: 0002_seed_lectures
Revises: 0001_initial_schema
Create Date: 2026-05-04 20:20:00.000000
"""

from datetime import datetime, timedelta, timezone
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_seed_lectures"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    msk = timezone(timedelta(hours=3))
    lectures = sa.table(
        "lectures",
        sa.column("number", sa.Integer),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("scheduled_at", sa.DateTime(timezone=True)),
        sa.column("format", sa.String),
        sa.column("stream_url", sa.String),
        sa.column("materials_url", sa.String),
        sa.column("registration_open", sa.Boolean),
    )

    op.bulk_insert(
        lectures,
        [
            {
                "number": 1,
                "title": "Безопасность WEB приложений",
                "description": "Очная лекция в МТУСИ. Дополнительно: Проблемы использования LLM и безопасность кода.",
                "scheduled_at": datetime(2026, 3, 14, 12, 10, tzinfo=msk),
                "format": "offline",
                "stream_url": None,
                "materials_url": "https://example.com/lecture-1-materials",
                "registration_open": False,
            },
            {
                "number": 2,
                "title": "Безопасность Linux и безопасная настройка Docker",
                "description": "Дополнительные материалы доступны зарегистрированным.",
                "scheduled_at": datetime(2026, 3, 21, 12, 10, tzinfo=msk),
                "format": "online",
                "stream_url": None,
                "materials_url": "https://example.com/lecture-2-materials",
                "registration_open": False,
            },
            {
                "number": 3,
                "title": "Анализ исходного кода и сборки",
                "description": "Secure Coding Guidelines, цепочки поставок ПО, семейства уязвимостей и угроз.",
                "scheduled_at": datetime(2026, 3, 28, 12, 10, tzinfo=msk),
                "format": "online",
                "stream_url": None,
                "materials_url": "https://example.com/lecture-3-materials",
                "registration_open": False,
            },
            {
                "number": 4,
                "title": "Как работать с фреймворками для РБПО",
                "description": "Безопасность многопоточных приложений.",
                "scheduled_at": datetime(2026, 4, 4, 12, 10, tzinfo=msk),
                "format": "online",
                "stream_url": None,
                "materials_url": "https://example.com/lecture-4-materials",
                "registration_open": False,
            },
            {
                "number": 5,
                "title": "Архитектурные концепции ИБ систем",
                "description": "Секретная лекция от Дмитрия про архитектуру.",
                "scheduled_at": datetime(2026, 4, 11, 12, 10, tzinfo=msk),
                "format": "online",
                "stream_url": None,
                "materials_url": "https://example.com/lecture-5-materials",
                "registration_open": False,
            },
            {
                "number": 6,
                "title": "Безопасность микросервисной архитектуры",
                "description": "Безопасность в брокерах сообщений, IAM, телеметрия и мониторинг.",
                "scheduled_at": datetime(2026, 4, 18, 12, 10, tzinfo=msk),
                "format": "online",
                "stream_url": None,
                "materials_url": "https://example.com/lecture-6-materials",
                "registration_open": False,
            },
            {
                "number": 7,
                "title": "Безопасность в брокерах сообщений",
                "description": "Следующая лекция онлайн. Ссылка на Яндекс.Телемост выдаётся по кнопке зарегистрированным.",
                "scheduled_at": datetime(2026, 5, 20, 19, 0, tzinfo=msk),
                "format": "online",
                "stream_url": "https://example.com/lecture-7-stream",
                "materials_url": None,
                "registration_open": True,
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM lectures WHERE number BETWEEN 1 AND 7")
