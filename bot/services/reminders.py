from __future__ import annotations

from bot.db.models import Lecture


def build_reminder_text(lecture: Lecture) -> str:
    return (
        f"⏰ Напоминание о лекции №{lecture.number}\n"
        f"<b>{lecture.title}</b>\n\n"
        f"Начало: {lecture.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
        "Проверьте регистрацию и подключение заранее."
    )
