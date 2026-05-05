from __future__ import annotations

from datetime import datetime, timezone

from bot.db.repository import ExportRow
from bot.services.export import build_stats_csv


def test_build_stats_csv_contains_expected_columns_and_row() -> None:
    rows = [
        ExportRow(
            tg_user_id=123,
            username="student",
            full_name="Student Name",
            lecture_number=7,
            lecture_title="Broker security",
            registered_at=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
            clicks_count=3,
            first_click_at=datetime(2026, 5, 1, 10, 30, tzinfo=timezone.utc),
            last_click_at=datetime(2026, 5, 1, 10, 45, tzinfo=timezone.utc),
        )
    ]

    content = build_stats_csv(rows).decode("utf-8")
    assert (
        "tg_user_id,username,username_at,full_name,lecture_number,lecture_title,registered_at,clicks_count,first_click_at,last_click_at"
        in content
    )
    assert "123,student,@student,Student Name,7,Broker security,2026-05-01T10:00:00+00:00,3,2026-05-01T10:30:00+00:00,2026-05-01T10:45:00+00:00" in content
