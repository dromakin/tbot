from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.db.repository import Repository
from bot.services.reminders import build_reminder_text


def _to_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def reminder_job(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    lecture_id: int,
) -> None:
    async with session_factory() as session:
        repo = Repository(session)
        lecture = await repo.get_lecture(lecture_id)
        if lecture is None:
            return
        user_ids = await repo.list_registered_users_for_lecture(lecture_id)

    text = build_reminder_text(lecture, stream_url=lecture.stream_url)

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
        except Exception:  # pragma: no cover - network side effects
            logger.exception("Failed to send reminder to user_id=%s lecture_id=%s", user_id, lecture_id)


async def close_registration_job(
    session_factory: async_sessionmaker[AsyncSession],
    lecture_id: int,
) -> None:
    async with session_factory() as session:
        repo = Repository(session)
        lecture = await repo.get_lecture(lecture_id)
        if lecture is None:
            return
        if lecture.registration_open:
            await repo.set_registration_open(lecture_id, False)
            logger.info("Registration closed for lecture_id={}", lecture_id)


async def sync_lecture_jobs(
    scheduler: AsyncIOScheduler,
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    now = datetime.now(timezone.utc)

    async with session_factory() as session:
        repo = Repository(session)
        auto_close_hours = await repo.get_auto_close_hours()
        await repo.close_expired_registrations(auto_close_hours)
        lectures = await repo.list_lectures()

    for lecture in lectures:
        scheduled_at = _to_aware(lecture.scheduled_at)
        reminder_time = scheduled_at - timedelta(minutes=settings.remind_before_min)
        if reminder_time.astimezone(timezone.utc) > now:
            scheduler.add_job(
                reminder_job,
                trigger="date",
                run_date=reminder_time,
                args=[bot, session_factory, lecture.id],
                id=f"lecture_reminder_{lecture.id}",
                replace_existing=True,
            )

        opened_at = lecture.registration_opened_at
        if auto_close_hours > 0 and lecture.registration_open and opened_at is not None:
            close_at = _to_aware(opened_at) + timedelta(hours=auto_close_hours)
            if close_at.astimezone(timezone.utc) <= now:
                continue
            scheduler.add_job(
                close_registration_job,
                trigger="date",
                run_date=close_at,
                args=[session_factory, lecture.id],
                id=f"lecture_close_registration_{lecture.id}",
                replace_existing=True,
            )


def build_scheduler(
    bot: Bot,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.tz))
    scheduler.add_job(
        sync_lecture_jobs,
        trigger="interval",
        minutes=5,
        args=[scheduler, bot, session_factory, settings],
        id="sync_lecture_jobs",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_lecture_jobs,
        trigger="date",
        run_date=datetime.now(ZoneInfo(settings.tz)),
        args=[scheduler, bot, session_factory, settings],
        id="sync_lecture_jobs_initial",
        replace_existing=True,
    )
    return scheduler
