from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.models import Lecture, LectureFormat
from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, lecture_schedule_keyboard

router = Router(name="schedule")


def format_lecture(lecture: Lecture) -> str:
    dt = lecture.scheduled_at.strftime("%d.%m.%Y %H:%M")
    format_label = "Онлайн" if lecture.format == LectureFormat.ONLINE else "Очно"
    body = (
        f"<b>Лекция №{lecture.number}: {lecture.title}</b>\n\n"
        f"📅 <b>Дата:</b> {dt}\n"
        f"💻 <b>Формат:</b> {format_label}\n\n"
        f"{lecture.description or ''}"
    )
    if lecture.format != LectureFormat.ONLINE:
        return body

    stream_line = "Будет позже."
    if lecture.stream_url:
        stream_line = "Доступна по кнопке ниже."
    return f"{body}\n\n🔗 <b>Ссылка для подключения:</b>\n{stream_line}"


@router.callback_query(MenuCallback.filter(F.action == "schedule"))
async def schedule_handler(callback: CallbackQuery, repo: Repository) -> None:
    lectures = await repo.list_open_lectures()
    if callback.message is None:
        await callback.answer()
        return

    if not lectures:
        await callback.message.answer("Сейчас нет открытых лекций для регистрации.")
        await callback.answer()
        return

    await callback.message.answer("<b>📅 Расписание лекций</b>")
    for lecture in lectures:
        await callback.message.answer(
            format_lecture(lecture),
            reply_markup=lecture_schedule_keyboard(lecture),
        )
    await callback.answer()
