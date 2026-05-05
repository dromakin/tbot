from __future__ import annotations

from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.models import Lecture


class MenuCallback(CallbackData, prefix="menu"):
    action: str


class LectureCallback(CallbackData, prefix="lecture"):
    action: str
    lecture_id: int


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Программа курса", callback_data=MenuCallback(action="program"))
    builder.button(text="Материалы курса", callback_data=MenuCallback(action="materials"))
    builder.button(text="Расписание лекций", callback_data=MenuCallback(action="schedule"))
    builder.button(text="Регистрация на лекции", callback_data=MenuCallback(action="register"))
    builder.button(text="Проверить статус регистрации", callback_data=MenuCallback(action="status"))
    builder.button(text="Задать вопрос", callback_data=MenuCallback(action="question"))
    builder.button(text="Связаться с организаторами", callback_data=MenuCallback(action="contact"))
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data=MenuCallback(action="main"))
    return builder.as_markup()


def open_lectures_keyboard(lectures: Sequence[Lecture], action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lecture in lectures:
        builder.button(
            text=f"Лекция №{lecture.number}: {lecture.title}",
            callback_data=LectureCallback(action=action, lecture_id=lecture.id),
        )
    builder.button(text="Назад", callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def materials_keyboard(lectures: Sequence[Lecture], general_materials_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Основные материалы", callback_data=MenuCallback(action="materials_general"))
    for lecture in lectures:
        if lecture.materials_url:
            builder.button(
                text=f"Доп. материалы {lecture.number} лекции",
                callback_data=LectureCallback(action="materials", lecture_id=lecture.id),
            )
    builder.button(text="Назад", callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def lecture_schedule_keyboard(lecture: Lecture) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lecture.registration_open:
        builder.button(
            text="Зарегистрироваться",
            callback_data=LectureCallback(action="register", lecture_id=lecture.id),
        )
    if lecture.stream_url:
        builder.button(
            text="Получить ссылку для подключения",
            callback_data=LectureCallback(action="stream", lecture_id=lecture.id),
        )
    builder.button(text="Назад", callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()
