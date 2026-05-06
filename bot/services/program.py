from __future__ import annotations

from html import escape

from bot.db.models import Lecture
from bot.web.schemas import ProgramLectureOut


def parse_topics(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def build_program_payload(header: str, lectures: list[Lecture]) -> tuple[str, list[ProgramLectureOut]]:
    rows = [
        ProgramLectureOut(
            number=lecture.number,
            title=lecture.title,
            topics=parse_topics(lecture.topics),
        )
        for lecture in sorted(lectures, key=lambda row: row.number)
    ]
    return header, rows


def build_program_html(header: str, lectures: list[Lecture]) -> str:
    header_text = header.strip() or "Программа курса"
    lines: list[str] = [f"<b>{escape(header_text)}</b>"]

    for lecture in sorted(lectures, key=lambda row: row.number):
        lines.append("")
        lines.append(f"<b>Лекция №{lecture.number}. {escape(lecture.title)}</b>")
        topics = parse_topics(lecture.topics)
        if topics:
            lines.extend(f"• {escape(topic)}" for topic in topics)
        else:
            lines.append("Темы будут опубликованы позже.")

    return "\n".join(lines)
