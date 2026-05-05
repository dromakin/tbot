from __future__ import annotations

from bot.db.models import Lecture
from bot.text_store import t


def build_reminder_text(lecture: Lecture, stream_url: str | None = None) -> str:
    base = t(
        "reminders",
        "base",
        lecture_number=lecture.number,
        lecture_title=lecture.title,
        scheduled_at=lecture.scheduled_at.strftime("%d.%m.%Y %H:%M"),
    )
    if stream_url:
        return t("reminders", "with_link", base_text=base, stream_url=stream_url)
    return base
