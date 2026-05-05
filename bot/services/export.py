from __future__ import annotations

import csv
import io
from datetime import datetime

from bot.db.repository import ExportRow


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _format_username_at(value: str | None) -> str:
    if not value:
        return ""
    return f"@{value}"


def build_stats_csv(rows: list[ExportRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "tg_user_id",
            "username",
            "username_at",
            "full_name",
            "lecture_number",
            "lecture_title",
            "registered_at",
            "clicks_count",
            "first_click_at",
            "last_click_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.tg_user_id,
                row.username or "",
                _format_username_at(row.username),
                row.full_name,
                row.lecture_number,
                row.lecture_title,
                _format_dt(row.registered_at),
                row.clicks_count,
                _format_dt(row.first_click_at),
                _format_dt(row.last_click_at),
            ]
        )
    return buffer.getvalue().encode("utf-8")
