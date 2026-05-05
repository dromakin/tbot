from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone

from bot.db.models import ClickEventType, Lecture, LectureFormat
from bot.db.repository import (
    AttendanceMatrixRow,
    ClickEventRawRow,
    ClicksPerUserRow,
    ExportRow,
    LectureClickStatsRow,
    LectureFunnelRow,
    UserExportRow,
)
from bot.services.export import build_export_zip, build_stats_csv


def test_build_export_zip_contains_expected_csv_files() -> None:
    now = datetime.now(timezone.utc)
    lecture = Lecture(
        id=10,
        number=1,
        title="Test lecture",
        description="desc",
        scheduled_at=now,
        format=LectureFormat.ONLINE,
        stream_url="https://example.com/stream",
        materials_url="https://example.com/materials",
        registration_open=True,
    )
    zip_bytes = build_export_zip(
        registrations=[
            ExportRow(
                tg_user_id=1,
                username="student",
                full_name="Student User",
                lecture_number=1,
                lecture_title="Test lecture",
                registered_at=now,
                clicks_count=2,
                first_click_at=now,
                last_click_at=now,
            )
        ],
        click_events=[
            ClickEventRawRow(
                event_id=100,
                tg_user_id=1,
                username="student",
                full_name="Student User",
                lecture_id=10,
                lecture_number=1,
                lecture_title="Test lecture",
                event_type=ClickEventType.STREAM_LINK,
                created_at=now,
            )
        ],
        clicks_per_lecture=[
            LectureClickStatsRow(
                lecture_id=10,
                lecture_number=1,
                lecture_title="Test lecture",
                stream_link_clicks=2,
                materials_lecture_clicks=1,
                registration_clicks=1,
                total_clicks=4,
            )
        ],
        clicks_per_user=[
            ClicksPerUserRow(
                tg_user_id=1,
                username="student",
                full_name="Student User",
                stream_link_clicks=2,
                materials_general_clicks=0,
                materials_lecture_clicks=1,
                registration_clicks=1,
                total_clicks=4,
            )
        ],
        attendance_lectures=[lecture],
        attendance_rows=[
            AttendanceMatrixRow(
                tg_user_id=1,
                username="student",
                full_name="Student User",
                by_lecture_id={10: 1},
            )
        ],
        funnel_per_lecture=[
            (
                LectureClickStatsRow(
                    lecture_id=10,
                    lecture_number=1,
                    lecture_title="Test lecture",
                    stream_link_clicks=2,
                    materials_lecture_clicks=1,
                    registration_clicks=1,
                    total_clicks=4,
                ),
                LectureFunnelRow(
                    lecture_id=10,
                    registration_clicks=1,
                    registrations=1,
                    stream_link_unique=1,
                    materials_lecture_unique=1,
                ),
            )
        ],
        users=[
            UserExportRow(
                tg_user_id=1,
                username="student",
                full_name="Student User",
                first_seen_at=now,
                last_seen_at=now,
            )
        ],
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as archive:
        names = set(archive.namelist())
        assert names == {
            "registrations.csv",
            "click_events.csv",
            "clicks_per_lecture.csv",
            "clicks_per_user.csv",
            "attendance_matrix.csv",
            "funnel_per_lecture.csv",
            "users.csv",
        }

        registrations_csv = archive.read("registrations.csv").decode("utf-8")
        click_events_csv = archive.read("click_events.csv").decode("utf-8")
        attendance_csv = archive.read("attendance_matrix.csv").decode("utf-8")

        assert registrations_csv.splitlines()[0].startswith("tg_user_id,username,username_at")
        assert click_events_csv.splitlines()[0].startswith("event_id,tg_user_id,username")
        assert "lecture_1_10" in attendance_csv.splitlines()[0]


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
