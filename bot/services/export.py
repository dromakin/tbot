from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime

from bot.db.models import Lecture
from bot.db.repository import (
    AttendanceMatrixRow,
    ClickEventRawRow,
    ClicksPerUserRow,
    ExportRow,
    LectureClickStatsRow,
    LectureFunnelRow,
    UserExportRow,
)


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


def _build_click_events_csv(rows: list[ClickEventRawRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "event_id",
            "tg_user_id",
            "username",
            "username_at",
            "full_name",
            "lecture_id",
            "lecture_number",
            "lecture_title",
            "event_type",
            "created_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.event_id,
                row.tg_user_id,
                row.username or "",
                _format_username_at(row.username),
                row.full_name,
                row.lecture_id if row.lecture_id is not None else "",
                row.lecture_number if row.lecture_number is not None else "",
                row.lecture_title or "",
                row.event_type.value,
                _format_dt(row.created_at),
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _build_clicks_per_lecture_csv(rows: list[LectureClickStatsRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "lecture_id",
            "lecture_number",
            "lecture_title",
            "stream_link_clicks",
            "materials_lecture_clicks",
            "registration_clicks",
            "total_clicks",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.lecture_id,
                row.lecture_number,
                row.lecture_title,
                row.stream_link_clicks,
                row.materials_lecture_clicks,
                row.registration_clicks,
                row.total_clicks,
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _build_clicks_per_user_csv(rows: list[ClicksPerUserRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "tg_user_id",
            "username",
            "username_at",
            "full_name",
            "stream_link_clicks",
            "materials_general_clicks",
            "materials_lecture_clicks",
            "registration_clicks",
            "total_clicks",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.tg_user_id,
                row.username or "",
                _format_username_at(row.username),
                row.full_name,
                row.stream_link_clicks,
                row.materials_general_clicks,
                row.materials_lecture_clicks,
                row.registration_clicks,
                row.total_clicks,
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _build_attendance_matrix_csv(lectures: list[Lecture], rows: list[AttendanceMatrixRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    lecture_columns = [f"lecture_{lecture.number}_{lecture.id}" for lecture in lectures]
    writer.writerow(["tg_user_id", "username", "username_at", "full_name", *lecture_columns])
    for row in rows:
        writer.writerow(
            [
                row.tg_user_id,
                row.username or "",
                _format_username_at(row.username),
                row.full_name,
                *[row.by_lecture_id.get(lecture.id, 0) for lecture in lectures],
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _build_funnel_per_lecture_csv(rows: list[tuple[LectureClickStatsRow, LectureFunnelRow]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "lecture_id",
            "lecture_number",
            "lecture_title",
            "registration_clicks",
            "registrations",
            "stream_link_unique",
            "materials_lecture_unique",
            "total_clicks",
        ]
    )
    for click_row, funnel_row in rows:
        writer.writerow(
            [
                click_row.lecture_id,
                click_row.lecture_number,
                click_row.lecture_title,
                funnel_row.registration_clicks,
                funnel_row.registrations,
                funnel_row.stream_link_unique,
                funnel_row.materials_lecture_unique,
                click_row.total_clicks,
            ]
        )
    return buffer.getvalue().encode("utf-8")


def _build_users_csv(rows: list[UserExportRow]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["tg_user_id", "username", "username_at", "full_name", "first_seen_at", "last_seen_at"])
    for row in rows:
        writer.writerow(
            [
                row.tg_user_id,
                row.username or "",
                _format_username_at(row.username),
                row.full_name,
                _format_dt(row.first_seen_at),
                _format_dt(row.last_seen_at),
            ]
        )
    return buffer.getvalue().encode("utf-8")


def build_export_zip(
    *,
    registrations: list[ExportRow],
    click_events: list[ClickEventRawRow],
    clicks_per_lecture: list[LectureClickStatsRow],
    clicks_per_user: list[ClicksPerUserRow],
    attendance_lectures: list[Lecture],
    attendance_rows: list[AttendanceMatrixRow],
    funnel_per_lecture: list[tuple[LectureClickStatsRow, LectureFunnelRow]],
    users: list[UserExportRow],
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("registrations.csv", build_stats_csv(registrations))
        archive.writestr("click_events.csv", _build_click_events_csv(click_events))
        archive.writestr("clicks_per_lecture.csv", _build_clicks_per_lecture_csv(clicks_per_lecture))
        archive.writestr("clicks_per_user.csv", _build_clicks_per_user_csv(clicks_per_user))
        archive.writestr(
            "attendance_matrix.csv",
            _build_attendance_matrix_csv(attendance_lectures, attendance_rows),
        )
        archive.writestr("funnel_per_lecture.csv", _build_funnel_per_lecture_csv(funnel_per_lecture))
        archive.writestr("users.csv", _build_users_csv(users))
    return buffer.getvalue()
