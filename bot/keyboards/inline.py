from __future__ import annotations

from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.models import Lecture
from bot.text_store import t


class MenuCallback(CallbackData, prefix="menu"):
    action: str


class LectureCallback(CallbackData, prefix="lecture"):
    action: str
    lecture_id: int


def main_menu_keyboard(web_public_url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if web_public_url:
        builder.button(
            text=t("menu", "keyboards.main_menu.miniapp"),
            web_app=WebAppInfo(url=web_public_url),
        )
    builder.button(text=t("menu", "keyboards.main_menu.program"), callback_data=MenuCallback(action="program"))
    builder.button(text=t("menu", "keyboards.main_menu.materials"), callback_data=MenuCallback(action="materials"))
    builder.button(text=t("menu", "keyboards.main_menu.schedule"), callback_data=MenuCallback(action="schedule"))
    builder.button(text=t("menu", "keyboards.main_menu.register"), callback_data=MenuCallback(action="register"))
    builder.button(text=t("menu", "keyboards.main_menu.status"), callback_data=MenuCallback(action="status"))
    builder.button(text=t("menu", "keyboards.main_menu.question"), callback_data=MenuCallback(action="question"))
    builder.button(text=t("menu", "keyboards.main_menu.contact"), callback_data=MenuCallback(action="contact"))
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("menu", "keyboards.back.main"), callback_data=MenuCallback(action="main"))
    return builder.as_markup()


def open_lectures_keyboard(lectures: Sequence[Lecture], action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lecture in lectures:
        builder.button(
            text=t(
                "registration",
                "keyboards.open_lectures.row",
                lecture_number=lecture.number,
                lecture_title=lecture.title,
            ),
            callback_data=LectureCallback(action=action, lecture_id=lecture.id),
        )
    builder.button(text=t("menu", "keyboards.back.main"), callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def materials_keyboard(lectures: Sequence[Lecture]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("materials", "keyboards.materials.general"), callback_data=MenuCallback(action="materials_general"))
    for lecture in lectures:
        if lecture.materials_url:
            builder.button(
                text=t("materials", "keyboards.materials.lecture_row", lecture_number=lecture.number),
                callback_data=LectureCallback(action="materials", lecture_id=lecture.id),
            )
    builder.button(text=t("menu", "keyboards.back.main"), callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()


def lecture_schedule_keyboard(lecture: Lecture) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if lecture.registration_open:
        builder.button(
            text=t("schedule", "keyboards.lecture_actions.register"),
            callback_data=LectureCallback(action="register", lecture_id=lecture.id),
        )
    if lecture.stream_url:
        builder.button(
            text=t("schedule", "keyboards.lecture_actions.stream"),
            callback_data=LectureCallback(action="stream", lecture_id=lecture.id),
        )
    builder.button(text=t("menu", "keyboards.back.main"), callback_data=MenuCallback(action="main"))
    builder.adjust(1)
    return builder.as_markup()
