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
from bot.services.export import build_stats_csv
from bot.states import CreateLectureState

router = Router(name="admin")


def _is_admin(user_id: int | None, settings: Settings) -> bool:
    return user_id is not None and user_id in settings.admin_ids


def _display_nickname(username: str | None) -> str:
    return f"@{username}" if username else "-"


async def _ensure_admin(message: Message, settings: Settings) -> bool:
    user_id = message.from_user.id if message.from_user else None
    if not _is_admin(user_id, settings):
        await message.answer("Команда доступна только администраторам.")
        return False
    return True


@router.message(Command("admin"))
async def admin_help_handler(message: Message, settings: Settings) -> None:
    if not await _ensure_admin(message, settings):
        return
    await message.answer(
        "Админ-команды:\n"
        "/create_lecture - создать лекцию через FSM\n"
        "/lectures - список лекций\n"
        "/delete_lecture <lecture_id>\n"
        "/open_registration <lecture_id>\n"
        "/close_registration <lecture_id>\n"
        "/set_stream <lecture_id> <url>\n"
        "/set_materials <lecture_id> <url>\n"
        "/lecture_registrations <lecture_id> - список регистраций\n"
        "/stats - краткая статистика\n"
        "/export_csv - выгрузка статистики"
    )


@router.message(Command("lectures"))
async def list_lectures_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    lectures = await repo.list_lectures()
    if not lectures:
        await message.answer("Лекций пока нет.")
        return

    lines = ["Список лекций:"]
    for lecture in lectures:
        lines.append(
            f"[id={lecture.id}] №{lecture.number} {lecture.title} | "
            f"{lecture.scheduled_at.strftime('%d.%m.%Y %H:%M')} | "
            f"format={lecture.format.value} | reg_open={lecture.registration_open}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("lecture_registrations"))
async def lecture_registrations_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /lecture_registrations <lecture_id>")
        return

    lecture_id = int(parts[1])
    rows = await repo.list_lecture_registration_rows(lecture_id)
    if not rows:
        await message.answer("Регистраций нет.")
        return

    lines = [
        (
            f"[id={row.tg_user_id}] {_display_nickname(row.username)} | "
            f"{row.full_name} | "
            f"{row.registered_at.strftime('%d.%m.%Y %H:%M')} | "
            f"clicks={row.clicks_count}"
        )
        for row in rows
    ]
    chunk_size = 50
    for index in range(0, len(lines), chunk_size):
        header = f"Регистрации (snapshot профиля) для lecture_id={lecture_id}:\n" if index == 0 else ""
        await message.answer(header + "\n".join(lines[index : index + chunk_size]))


@router.message(Command("delete_lecture"))
async def delete_lecture_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /delete_lecture <lecture_id>")
        return
    ok = await repo.delete_lecture(int(parts[1]))
    await message.answer("Лекция удалена." if ok else "Лекция не найдена.")


async def _set_registration(message: Message, settings: Settings, repo: Repository, value: bool) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].isdigit():
        cmd = "/open_registration" if value else "/close_registration"
        await message.answer(f"Использование: {cmd} <lecture_id>")
        return
    ok = await repo.set_registration_open(int(parts[1]), value)
    if not ok:
        await message.answer("Лекция не найдена.")
        return
    await message.answer("Готово.")


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
        await message.answer("Использование: /set_stream <lecture_id> <url>")
        return
    ok = await repo.set_stream_url(int(parts[1]), parts[2])
    await message.answer("Ссылка обновлена." if ok else "Лекция не найдена.")


@router.message(Command("set_materials"))
async def set_materials_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Использование: /set_materials <lecture_id> <url>")
        return
    ok = await repo.set_materials_url(int(parts[1]), parts[2])
    await message.answer("Ссылка обновлена." if ok else "Лекция не найдена.")


@router.message(Command("stats"))
async def stats_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    rows = await repo.get_stats()
    if not rows:
        await message.answer("Статистики пока нет.")
        return
    lines = ["Статистика по лекциям:"]
    for row in rows:
        lines.append(
            f"№{row.lecture_number} {row.lecture_title}\n"
            f"  зарегистрировано: {row.registrations_count}\n"
            f"  уникальных кликов: {row.unique_clicks_count}\n"
            f"  всего кликов: {row.total_clicks_count}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("export_csv"))
async def export_csv_handler(message: Message, settings: Settings, repo: Repository) -> None:
    if not await _ensure_admin(message, settings):
        return
    rows = await repo.get_export_rows()
    csv_bytes = build_stats_csv(rows)
    file = BufferedInputFile(csv_bytes, filename="stats.csv")
    await message.answer_document(file, caption="Экспорт статистики по лекциям")


@router.message(Command("create_lecture"))
async def create_lecture_start_handler(message: Message, settings: Settings, state: FSMContext) -> None:
    if not await _ensure_admin(message, settings):
        return
    await state.clear()
    await state.set_state(CreateLectureState.waiting_number)
    await message.answer("Введите номер лекции (целое число):")


@router.message(CreateLectureState.waiting_number)
async def create_lecture_number_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Номер должен быть целым числом. Попробуйте снова:")
        return
    await state.update_data(number=int(text))
    await state.set_state(CreateLectureState.waiting_title)
    await message.answer("Введите название лекции:")


@router.message(CreateLectureState.waiting_title)
async def create_lecture_title_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(CreateLectureState.waiting_description)
    await message.answer("Введите описание лекции:")


@router.message(CreateLectureState.waiting_description)
async def create_lecture_description_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(CreateLectureState.waiting_datetime)
    await message.answer("Введите дату и время в формате YYYY-MM-DD HH:MM:")


@router.message(CreateLectureState.waiting_datetime)
async def create_lecture_datetime_handler(message: Message, state: FSMContext, settings: Settings) -> None:
    text = (message.text or "").strip()
    try:
        dt_naive = datetime.strptime(text, "%Y-%m-%d %H:%M")
        dt = dt_naive.replace(tzinfo=ZoneInfo(settings.tz))
    except ValueError:
        await message.answer("Неверный формат. Используйте YYYY-MM-DD HH:MM:")
        return

    await state.update_data(scheduled_at=dt)
    await state.set_state(CreateLectureState.waiting_format)
    await message.answer("Введите формат: online или offline")


@router.message(CreateLectureState.waiting_format)
async def create_lecture_format_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().lower()
    if text not in {LectureFormat.ONLINE.value, LectureFormat.OFFLINE.value}:
        await message.answer("Введите online или offline")
        return
    await state.update_data(lecture_format=text)
    await state.set_state(CreateLectureState.waiting_stream_url)
    await message.answer("Введите stream_url (или '-' если нет):")


@router.message(CreateLectureState.waiting_stream_url)
async def create_lecture_stream_handler(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    await state.update_data(stream_url=None if text == "-" else text)
    await state.set_state(CreateLectureState.waiting_materials_url)
    await message.answer("Введите materials_url (или '-' если нет):")


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
        f"Лекция создана: id={lecture.id}, №{lecture.number} {lecture.title} "
        f"({lecture.scheduled_at.strftime('%d.%m.%Y %H:%M')})"
    )
