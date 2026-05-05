from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.base import Base
from bot.db.models import LectureFormat
from bot.db.repository import Repository


@pytest.fixture()
async def repo() -> Repository:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        repository = Repository(session)
        yield repository

    await engine.dispose()


@pytest.mark.asyncio
async def test_registration_is_idempotent(repo: Repository) -> None:
    await repo.upsert_user(101, "student_1", "Student One")
    lecture = await repo.create_lecture(
        number=77,
        title="Test lecture",
        description="desc",
        scheduled_at=datetime(2026, 5, 30, 19, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        stream_url="https://telemost.yandex.ru/j/demo",
        registration_open=True,
    )

    created_first, _ = await repo.register_user_for_lecture(101, lecture.id)
    created_second, _ = await repo.register_user_for_lecture(101, lecture.id)

    assert created_first is True
    assert created_second is False

    registrations = await repo.get_user_registrations(101)
    assert len(registrations) == 1


@pytest.mark.asyncio
async def test_click_stats_and_export(repo: Repository) -> None:
    await repo.upsert_user(201, "student_2", "Student Two")
    lecture = await repo.create_lecture(
        number=78,
        title="Online lecture",
        description="desc",
        scheduled_at=datetime(2026, 6, 1, 19, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        stream_url="https://telemost.yandex.ru/j/demo2",
        registration_open=True,
    )
    await repo.register_user_for_lecture(201, lecture.id)
    await repo.create_link_click(201, lecture.id)
    await repo.create_link_click(201, lecture.id)

    stats = await repo.get_stats()
    stats_for_lecture = [row for row in stats if row.lecture_id == lecture.id][0]
    assert stats_for_lecture.registrations_count == 1
    assert stats_for_lecture.unique_clicks_count == 1
    assert stats_for_lecture.total_clicks_count == 2

    rows = await repo.get_export_rows()
    export_row = [row for row in rows if row.lecture_number == 78][0]
    assert export_row.tg_user_id == 201
    assert export_row.clicks_count == 2
