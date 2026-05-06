from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.base import Base
from bot.db.models import ClickEvent, ClickEventType, LectureFormat, QuestionStatus, User
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

    created_first, _ = await repo.register_user_for_lecture(
        101,
        lecture.id,
        username="student_1",
        full_name="Student One",
    )
    created_second, _ = await repo.register_user_for_lecture(
        101,
        lecture.id,
        username="student_1",
        full_name="Student One",
    )

    assert created_first is True
    assert created_second is False

    registrations = await repo.get_user_registrations(101)
    assert len(registrations) == 1


@pytest.mark.asyncio
async def test_upsert_user_updates_profile_fields(repo: Repository) -> None:
    first = await repo.upsert_user(555, "old_username", "Old Name")
    first_seen_at = first.first_seen_at
    first_last_seen_at = first.last_seen_at

    await repo.upsert_user(555, "new_username", "New Name")
    updated = await repo.session.get(User, 555)

    assert updated is not None
    assert updated.username == "new_username"
    assert updated.full_name == "New Name"
    assert updated.first_seen_at == first_seen_at
    assert updated.last_seen_at >= first_last_seen_at


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
    await repo.register_user_for_lecture(
        201,
        lecture.id,
        username="student_2",
        full_name="Student Two",
    )
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


@pytest.mark.asyncio
async def test_click_event_settings_and_aggregates(repo: Repository) -> None:
    await repo.upsert_user(301, "student_3", "Student Three")
    lecture = await repo.create_lecture(
        number=79,
        title="Click test lecture",
        description="desc",
        scheduled_at=datetime(2026, 6, 10, 19, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        stream_url="https://telemost.yandex.ru/j/demo3",
        registration_open=True,
    )

    settings = await repo.list_click_type_settings()
    assert len(settings) == 4
    assert all(row.enabled for row in settings)

    saved_registration = await repo.create_click_event(
        user_id=301,
        lecture_id=lecture.id,
        event_type=ClickEventType.REGISTRATION_CLICK,
    )
    assert saved_registration is True

    await repo.set_click_type_enabled(ClickEventType.MATERIALS_GENERAL, enabled=False)
    saved_general = await repo.create_click_event(
        user_id=301,
        event_type=ClickEventType.MATERIALS_GENERAL,
    )
    assert saved_general is False

    by_type = await repo.get_click_type_stats()
    registration_row = [row for row in by_type if row.event_type == ClickEventType.REGISTRATION_CLICK][0]
    assert registration_row.total_clicks == 1
    assert registration_row.unique_users == 1

    by_lecture = await repo.get_lecture_click_stats()
    lecture_row = [row for row in by_lecture if row.lecture_id == lecture.id][0]
    assert lecture_row.registration_clicks == 1
    assert lecture_row.stream_link_clicks == 0
    assert lecture_row.materials_lecture_clicks == 0


@pytest.mark.asyncio
async def test_question_moderation_flow(repo: Repository) -> None:
    await repo.upsert_user(401, "student_4", "Student Four")
    question = await repo.create_question(
        user_id=401,
        text="Можно запись?",
        username="student_4",
        full_name="Student Four",
    )
    assert question.status == QuestionStatus.PENDING

    ignored = await repo.set_question_ignored(question.id)
    assert ignored is not None
    assert ignored.status == QuestionStatus.IGNORED

    answered = await repo.answer_question(
        question.id,
        answer_text="Да, запись будет позже.",
        admin_id=999,
        admin_username="admin_user",
    )
    assert answered is not None
    assert answered.status == QuestionStatus.ANSWERED
    assert answered.answer_text == "Да, запись будет позже."
    assert answered.answered_by_admin_id == 999

    answered_list = await repo.list_questions(status=QuestionStatus.ANSWERED)
    assert any(item.id == question.id for item in answered_list)


@pytest.mark.asyncio
async def test_click_dashboard_aggregates(repo: Repository) -> None:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)

    await repo.upsert_user(501, "student_5", "Student Five")
    await repo.upsert_user(502, "student_6", "Student Six")
    lecture = await repo.create_lecture(
        number=80,
        title="Dashboard lecture",
        description="desc",
        scheduled_at=datetime(2026, 6, 15, 19, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        stream_url="https://telemost.yandex.ru/j/dashboard",
        registration_open=True,
    )
    await repo.register_user_for_lecture(501, lecture.id, username="student_5", full_name="Student Five")
    await repo.register_user_for_lecture(502, lecture.id, username="student_6", full_name="Student Six")

    repo.session.add_all(
        [
            ClickEvent(
                user_id=501,
                lecture_id=lecture.id,
                event_type=ClickEventType.REGISTRATION_CLICK,
                created_at=now,
            ),
            ClickEvent(
                user_id=501,
                lecture_id=lecture.id,
                event_type=ClickEventType.STREAM_LINK,
                created_at=now,
            ),
            ClickEvent(
                user_id=501,
                lecture_id=lecture.id,
                event_type=ClickEventType.STREAM_LINK,
                created_at=now,
            ),
            ClickEvent(
                user_id=501,
                lecture_id=lecture.id,
                event_type=ClickEventType.MATERIALS_LECTURE,
                created_at=now,
            ),
            ClickEvent(
                user_id=502,
                lecture_id=lecture.id,
                event_type=ClickEventType.REGISTRATION_CLICK,
                created_at=yesterday,
            ),
            ClickEvent(
                user_id=502,
                lecture_id=lecture.id,
                event_type=ClickEventType.STREAM_LINK,
                created_at=yesterday,
            ),
            ClickEvent(
                user_id=502,
                lecture_id=None,
                event_type=ClickEventType.MATERIALS_GENERAL,
                created_at=now,
            ),
        ]
    )
    await repo.session.commit()

    items, totals = await repo.get_click_summary()
    assert len(items) == 4
    assert totals.all_time_count == 7
    assert totals.week_count >= totals.today_count

    timeseries = await repo.get_click_timeseries(days=7)
    assert timeseries
    assert any(point.event_type == ClickEventType.STREAM_LINK for point in timeseries)

    top_users = await repo.get_top_click_users(event_type=ClickEventType.STREAM_LINK, limit=1)
    assert len(top_users) == 1
    assert top_users[0].tg_user_id == 501
    assert top_users[0].clicks_count == 2

    funnel = await repo.get_lecture_funnel(lecture.id)
    assert funnel.registration_clicks == 2
    assert funnel.registrations == 2
    assert funnel.stream_link_unique == 2
    assert funnel.materials_lecture_unique == 1

    hourly = await repo.get_lecture_clicks_by_hour(lecture.id)
    assert hourly
    assert sum(row.clicks_count for row in hourly) == 6


@pytest.mark.asyncio
async def test_course_overview(repo: Repository) -> None:
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    week_ago = now - timedelta(days=7)

    await repo.upsert_user(601, "student_7", "Student Seven")
    await repo.upsert_user(602, "student_8", "Student Eight")

    lecture_open = await repo.create_lecture(
        number=81,
        title="Open lecture",
        description="desc",
        scheduled_at=tomorrow,
        lecture_format=LectureFormat.ONLINE,
        stream_url="https://telemost.yandex.ru/j/open",
        registration_open=True,
    )
    lecture_past = await repo.create_lecture(
        number=82,
        title="Past lecture",
        description="desc",
        scheduled_at=week_ago,
        lecture_format=LectureFormat.ONLINE,
        stream_url="https://telemost.yandex.ru/j/past",
        registration_open=True,
    )

    await repo.register_user_for_lecture(601, lecture_open.id, username="student_7", full_name="Student Seven")
    await repo.register_user_for_lecture(602, lecture_open.id, username="student_8", full_name="Student Eight")
    await repo.register_user_for_lecture(601, lecture_past.id, username="student_7", full_name="Student Seven")
    await repo.set_registration_open(lecture_past.id, False)

    repo.session.add_all(
        [
            ClickEvent(
                user_id=601,
                lecture_id=lecture_open.id,
                event_type=ClickEventType.STREAM_LINK,
                created_at=now,
            ),
            ClickEvent(
                user_id=602,
                lecture_id=lecture_open.id,
                event_type=ClickEventType.STREAM_LINK,
                created_at=now,
            ),
            ClickEvent(
                user_id=601,
                lecture_id=lecture_past.id,
                event_type=ClickEventType.STREAM_LINK,
                created_at=yesterday,
            ),
            ClickEvent(
                user_id=601,
                lecture_id=lecture_open.id,
                event_type=ClickEventType.MATERIALS_LECTURE,
                created_at=now,
            ),
        ]
    )
    await repo.create_question(
        user_id=601,
        text="Вопрос в pending",
        username="student_7",
        full_name="Student Seven",
    )
    await repo.session.commit()

    overview = await repo.get_course_overview(days=7)
    assert overview.lectures_total == 2
    assert overview.lectures_open == 1
    assert overview.lectures_past == 1
    assert overview.registrations_total == 3
    assert overview.unique_students == 2
    assert overview.avg_registrations_per_lecture == 1.5
    assert overview.attendance_rate == 100.0
    assert overview.questions_pending_total == 1
    assert overview.period_clicks_total == 4

    lecture_rows = await repo.get_course_overview_lectures(days=7)
    assert len(lecture_rows) == 2
    assert all(row.sparkline for row in lecture_rows)
    open_row = next(row for row in lecture_rows if row.lecture_id == lecture_open.id)
    past_row = next(row for row in lecture_rows if row.lecture_id == lecture_past.id)
    assert open_row.status == "open"
    assert past_row.status == "past"
    assert open_row.registrations == 2
    assert open_row.stream_link_unique == 2
    assert open_row.attendance_rate == 100.0


@pytest.mark.asyncio
async def test_set_topics_updates_lecture(repo: Repository) -> None:
    lecture = await repo.create_lecture(
        number=91,
        title="Topics lecture",
        description="desc",
        topics=None,
        scheduled_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        registration_open=False,
    )

    ok = await repo.set_topics(
        lecture.id,
        "1. Первая тема\n2. Вторая тема",
    )
    assert ok is True

    updated = await repo.get_lecture(lecture.id)
    assert updated is not None
    assert updated.topics == "1. Первая тема\n2. Вторая тема"


@pytest.mark.asyncio
async def test_registration_open_timestamp_tracking(repo: Repository) -> None:
    lecture = await repo.create_lecture(
        number=92,
        title="Registration timestamp lecture",
        description="desc",
        scheduled_at=datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        registration_open=False,
    )
    assert lecture.registration_opened_at is None

    opened = await repo.set_registration_open(lecture.id, True)
    assert opened is True
    lecture_after_open = await repo.get_lecture(lecture.id)
    assert lecture_after_open is not None
    assert lecture_after_open.registration_opened_at is not None
    opened_at_first = lecture_after_open.registration_opened_at

    closed = await repo.set_registration_open(lecture.id, False)
    assert closed is True
    lecture_after_close = await repo.get_lecture(lecture.id)
    assert lecture_after_close is not None
    assert lecture_after_close.registration_opened_at is None

    reopened = await repo.set_registration_open(lecture.id, True)
    assert reopened is True
    lecture_after_reopen = await repo.get_lecture(lecture.id)
    assert lecture_after_reopen is not None
    assert lecture_after_reopen.registration_opened_at is not None
    assert lecture_after_reopen.registration_opened_at >= opened_at_first


@pytest.mark.asyncio
async def test_close_expired_registrations(repo: Repository) -> None:
    old_lecture = await repo.create_lecture(
        number=93,
        title="Old open lecture",
        description="desc",
        scheduled_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        registration_open=True,
    )
    fresh_lecture = await repo.create_lecture(
        number=94,
        title="Fresh open lecture",
        description="desc",
        scheduled_at=datetime(2026, 7, 4, 10, 0, tzinfo=timezone.utc),
        lecture_format=LectureFormat.ONLINE,
        registration_open=True,
    )

    old_model = await repo.get_lecture(old_lecture.id)
    fresh_model = await repo.get_lecture(fresh_lecture.id)
    assert old_model is not None
    assert fresh_model is not None
    old_model.registration_opened_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await repo.session.commit()

    closed_count = await repo.close_expired_registrations(hours=1)
    assert closed_count == 1

    await repo.session.refresh(old_model)
    await repo.session.refresh(fresh_model)
    assert old_model.registration_open is False
    assert old_model.registration_opened_at is None
    assert fresh_model.registration_open is True
    assert fresh_model.registration_opened_at is not None


@pytest.mark.asyncio
async def test_auto_close_hours_setting_roundtrip(repo: Repository) -> None:
    assert await repo.get_auto_close_hours() == 24

    await repo.set_auto_close_hours(36)
    assert await repo.get_auto_close_hours() == 36

    closed_count = await repo.close_expired_registrations(hours=0)
    assert closed_count == 0

    with pytest.raises(ValueError):
        await repo.set_auto_close_hours(-1)

    with pytest.raises(ValueError):
        await repo.set_auto_close_hours(8761)
