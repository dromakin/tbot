from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.models import Lecture, LectureFormat
from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, lecture_schedule_keyboard
from bot.text_store import t

router = Router(name="schedule")


def format_lecture(lecture: Lecture) -> str:
    dt = lecture.scheduled_at.strftime("%d.%m.%Y %H:%M")
    format_label = (
        t("schedule", "format_online")
        if lecture.format == LectureFormat.ONLINE
        else t("schedule", "format_offline")
    )
    body = t(
        "schedule",
        "lecture_card",
        lecture_number=lecture.number,
        lecture_title=lecture.title,
        scheduled_at=dt,
        format_label=format_label,
        lecture_description=lecture.description or "",
    )
    if lecture.format != LectureFormat.ONLINE:
        return body

    stream_line = t("schedule", "link_later")
    if lecture.stream_url:
        stream_line = t("schedule", "link_available")
    return t("schedule", "lecture_card_stream", lecture_card=body, stream_line=stream_line)


@router.callback_query(MenuCallback.filter(F.action == "schedule"))
async def schedule_handler(callback: CallbackQuery, repo: Repository) -> None:
    lectures = await repo.list_open_lectures()
    if callback.message is None:
        await callback.answer()
        return

    if not lectures:
        await callback.message.answer(t("schedule", "empty"))
        await callback.answer()
        return

    await callback.message.answer(t("schedule", "header"))
    for lecture in lectures:
        await callback.message.answer(
            format_lecture(lecture),
            reply_markup=lecture_schedule_keyboard(lecture),
        )
    await callback.answer()
