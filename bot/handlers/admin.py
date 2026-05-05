from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from bot.config import Settings
from bot.db.models import LectureFormat
from bot.db.repository import Repository
from bot.services.export import build_export_zip, build_stats_csv
from bot.states import CreateLectureState
from bot.text_store import t

router = Router(name="admin")


def _is_admin(user_id: int | None, settings: Settings) -> bool:
    return user_id is not None and user_id in settings.admin_ids


def _display_nickname(username: str | None) -> str:
    return f"@{username}" if username else "-"


async def _ensure_admin(message: Message, settings: Settings) -> bool:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id, settings):
        await message.answer(t("admin", "admin_only"))
        return False
    return True


@router.message(Command("admin"))
async def admin_help_handler(message: Message, settings: Settings) -> None:
    if not await _ensure_admin(message, settings):
        return
    await message.answer(t("admin", "help"))


@router.message(Command("lectures"))
async def list_lectures_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    lectures = await repo.list_lectures()
    if not lectures:
        await message.answer(t("admin", "lectures_empty"))
        return

    lines = [t("admin", "lectures_header")]
    for lecture in lectures:
        lines.append(
            t(
                "admin",
                "lectures_item",
                lecture_id=lecture.id,
                lecture_number=lecture.number,
                lecture_title=lecture.title,
                scheduled_at=lecture.scheduled_at.strftime("%d.%m.%Y %H:%M"),
                lecture_format=lecture.format.value,
                registration_open=lecture.registration_open,
            )
        )
    await message.answer("\n".join(lines))


@router.message(Command("lecture_registrations"))
async def lecture_registrations_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(t("admin", "lecture_registrations_usage"))
        return

    lecture_id = int(parts[1])
    rows = await repo.list_lecture_registration_rows(lecture_id)
    if not rows:
        await message.answer(t("admin", "lecture_registrations_empty"))
        return

    lines = [
        t(
            "admin",
            "lecture_registrations_item",
            tg_user_id=row.tg_user_id,
            nickname=_display_nickname(row.username),
            full_name=row.full_name,
            registered_at=row.registered_at.strftime("%d.%m.%Y %H:%M"),
            clicks_count=row.clicks_count,
        )
        for row in rows
    ]
    chunk_size = 50
    for index in range(0, len(lines), chunk_size):
        header = (
            t("admin", "lecture_registrations_header", lecture_id=lecture_id) + "\n"
            if index == 0
            else ""
        )
        await message.answer(header + "\n".join(lines[index : index + chunk_size]))


@router.message(Command("delete_lecture"))
async def delete_lecture_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(t("admin", "delete_lecture_usage"))
        return
    ok = await repo.delete_lecture(int(parts[1]))
    await message.answer(t("admin", "lecture_deleted") if ok else t("admin", "lecture_not_found"))


async def _set_registration(message: Message, settings: Settings, repo: Repository, value: bool) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(
            t("admin", "open_registration_usage" if value else "close_registration_usage")
        )
        return
    ok = await repo.set_registration_open(int(parts[1]), value)
    if not ok:
        await message.answer(t("admin", "lecture_not_found"))
        return
    await message.answer(t("admin", "done"))


@router.message(Command("open_registration"))
async def open_registration_handler(message: Message, settings: Settings, repo: Repository) -> None:
    await _set_registration(message, settings, repo, True)


@router.message(Command("close_registration"))
async def close_registration_handler(message: Message, settings: Settings, repo: Repository) -> None:
    await _set_registration(message, settings, repo, False)


@router.message(Command("set_stream"))
async def set_stream_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer(t("admin", "set_stream_usage"))
        return
    ok = await repo.set_stream_url(int(parts[1]), parts[2])
    await message.answer(t("admin", "link_updated") if ok else t("admin", "lecture_not_found"))


@router.message(Command("set_materials"))
async def set_materials_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer(t("admin", "set_materials_usage"))
        return
    ok = await repo.set_materials_url(int(parts[1]), parts[2])
    await message.answer(t("admin", "link_updated") if ok else t("admin", "lecture_not_found"))


@router.message(Command("stats"))
async def stats_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    rows = await repo.get_stats()
    if not rows:
        await message.answer(t("admin", "stats_empty"))
        return
    lines = [t("admin", "stats_header")]
    for row in rows:
        lines.append(
            t(
                "admin",
                "stats_item",
                lecture_number=row.lecture_number,
                lecture_title=row.lecture_title,
                registrations_count=row.registrations_count,
                unique_clicks_count=row.unique_clicks_count,
                total_clicks_count=row.total_clicks_count,
            )
        )
    await message.answer("\n".join(lines))


@router.message(Command("export_csv"))
async def export_csv_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    rows = await repo.get_export_rows()
    csv_bytes = build_stats_csv(rows)
    file = BufferedInputFile(csv_bytes, filename="stats.csv")
    await message.answer_document(file, caption=t("admin", "export_csv_caption"))


@router.message(Command("export_zip"))
async def export_zip_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return

    registrations = await repo.get_export_rows()
    click_events = await repo.iter_click_events_raw()
    clicks_per_lecture = await repo.get_lecture_click_stats()
    clicks_per_user = await repo.get_clicks_per_user()
    attendance_lectures, attendance_rows = await repo.get_attendance_matrix()
    users = await repo.list_users()

    funnel_per_lecture = []
    for lecture_row in clicks_per_lecture:
        funnel_row = await repo.get_lecture_funnel(lecture_row.lecture_id)
        funnel_per_lecture.append((lecture_row, funnel_row))

    zip_bytes = build_export_zip(
        registrations=registrations,
        click_events=click_events,
        clicks_per_lecture=clicks_per_lecture,
        clicks_per_user=clicks_per_user,
        attendance_lectures=attendance_lectures,
        attendance_rows=attendance_rows,
        funnel_per_lecture=funnel_per_lecture,
        users=users,
    )
    file = BufferedInputFile(zip_bytes, filename="stats_bundle.zip")
    await message.answer_document(file, caption=t("admin", "export_zip_caption"))


@router.message(Command("create_lecture"))
async def create_lecture_start_handler(message: Message, settings: Settings, state: FSMContext) -> None:
    if not await _ensure_admin(message, settings):
        return
    await state.clear()
    await state.set_state(CreateLectureState.waiting_number)
    await message.answer(t("admin", "create_lecture.ask_number"))


@router.message(CreateLectureState.waiting_number)
async def create_lecture_number_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(t("admin", "create_lecture.invalid_number"))
        return
    await state.update_data(number=int(text))
    await state.set_state(CreateLectureState.waiting_title)
    await message.answer(t("admin", "create_lecture.ask_title"))


@router.message(CreateLectureState.waiting_title)
async def create_lecture_title_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(CreateLectureState.waiting_description)
    await message.answer(t("admin", "create_lecture.ask_description"))


@router.message(CreateLectureState.waiting_description)
async def create_lecture_description_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(CreateLectureState.waiting_datetime)
    await message.answer(t("admin", "create_lecture.ask_datetime"))


@router.message(CreateLectureState.waiting_datetime)
async def create_lecture_datetime_handler(message: Message, state: FSMContext, settings: Settings) -> None:
    text = (message.text or "").strip()
    try:
        dt_naive = datetime.strptime(text, "%Y-%m-%d %H:%M")
        dt = dt_naive.replace(tzinfo=ZoneInfo(settings.tz))
    except ValueError:
        await message.answer(t("admin", "create_lecture.invalid_datetime"))
        return

    await state.update_data(scheduled_at=dt)
    await state.set_state(CreateLectureState.waiting_format)
    await message.answer(t("admin", "create_lecture.ask_format"))


@router.message(CreateLectureState.waiting_format)
async def create_lecture_format_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().lower()
    if text not in {LectureFormat.ONLINE.value, LectureFormat.OFFLINE.value}:
        await message.answer(t("admin", "create_lecture.invalid_format"))
        return
    await state.update_data(lecture_format=text)
    await state.set_state(CreateLectureState.waiting_stream_url)
    await message.answer(t("admin", "create_lecture.ask_stream_url"))


@router.message(CreateLectureState.waiting_stream_url)
async def create_lecture_stream_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    await state.update_data(stream_url=None if text == "-" else text)
    await state.set_state(CreateLectureState.waiting_materials_url)
    await message.answer(t("admin", "create_lecture.ask_materials_url"))


@router.message(CreateLectureState.waiting_materials_url)
async def create_lecture_materials_handler(
    message: Message,
    state: FSMContext,
    repo: Repository,
) -> None:
    text = (message.text or "").strip()
    data = await state.get_data()
    lecture_format = LectureFormat(data["lecture_format"])
    lecture = await repo.create_lecture(
        number=data["number"],
        title=data["title"],
        description=data["description"],
        scheduled_at=data["scheduled_at"],
        lecture_format=lecture_format,
        stream_url=data["stream_url"],
        materials_url=None if text == "-" else text,
        registration_open=True,
    )
    await state.clear()
    await message.answer(
        t(
            "admin",
            "create_lecture.created",
            lecture_id=lecture.id,
            lecture_number=lecture.number,
            lecture_title=lecture.title,
            scheduled_at=lecture.scheduled_at.strftime("%d.%m.%Y %H:%M"),
        )
    )
