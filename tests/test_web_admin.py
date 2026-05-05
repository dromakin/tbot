from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import Settings
from bot.db.base import Base
from bot.db.models import ClickEventType, LectureFormat
from bot.db.repository import Repository
from bot.web.app import create_app


def build_init_data(bot_token: str, user_id: int, username: str | None) -> str:
    payload = {
        "query_id": "AAEAAAE",
        "auth_date": str(int(time.time())),
        "user": json.dumps(
            {
                "id": user_id,
                "username": username,
                "first_name": "Web",
                "last_name": "User",
            },
            separators=(",", ":"),
        ),
    }
    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items(), key=lambda x: x[0]))
    digest = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode({**payload, "hash": digest})


class DummyBot:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent_messages.append((chat_id, text))


@pytest.mark.asyncio
async def test_web_api_me_and_lectures_flow() -> None:
    bot_token = "test_bot_token"
    settings = Settings(
        BOT_TOKEN=bot_token,
        DB_DSN="sqlite+aiosqlite:///:memory:",
        ADMIN_IDS="111",
        ORG_CONTACT_TEXT="contact",
        GENERAL_MATERIALS_URL="https://example.com",
        WEB_PUBLIC_URL="https://example.com",
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app = create_app(settings=settings, session_factory=session_factory)

    admin_header = {
        "Authorization": f"tma {build_init_data(bot_token=bot_token, user_id=111, username='admin_user')}"
    }
    user_header = {
        "Authorization": f"tma {build_init_data(bot_token=bot_token, user_id=222, username='student')}"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        me_admin = await client.get("/api/me", headers=admin_header)
        assert me_admin.status_code == 200
        assert me_admin.json()["is_admin"] is True

        me_user = await client.get("/api/me", headers=user_header)
        assert me_user.status_code == 200
        assert me_user.json()["is_admin"] is False

        lectures_empty = await client.get("/api/lectures", headers=admin_header)
        assert lectures_empty.status_code == 200
        assert lectures_empty.json() == []

        create_payload = {
            "number": 999,
            "title": "Mini App Lecture",
            "description": "Created from API",
            "scheduled_at": "2026-12-01T10:00:00+00:00",
            "format": "online",
            "stream_url": "https://telemost.yandex.ru/j/example",
            "materials_url": None,
            "registration_open": True,
        }
        created = await client.post("/api/lectures", headers=admin_header, json=create_payload)
        assert created.status_code == 201
        assert created.json()["number"] == 999

        lectures_after = await client.get("/api/lectures", headers=admin_header)
        assert lectures_after.status_code == 200
        assert len(lectures_after.json()) == 1

        forbidden = await client.get("/api/lectures", headers=user_header)
        assert forbidden.status_code == 403

    await engine.dispose()


@pytest.mark.asyncio
async def test_web_api_click_settings_and_question_moderation() -> None:
    bot_token = "test_bot_token"
    settings = Settings(
        BOT_TOKEN=bot_token,
        DB_DSN="sqlite+aiosqlite:///:memory:",
        ADMIN_IDS="111",
        ORG_CONTACT_TEXT="contact",
        GENERAL_MATERIALS_URL="https://example.com",
        WEB_PUBLIC_URL="https://example.com",
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    dummy_bot = DummyBot()
    app = create_app(settings=settings, session_factory=session_factory, bot=dummy_bot)

    async with session_factory() as session:
        repo = Repository(session)
        await repo.upsert_user(222, "student", "Student User")
        lecture = await repo.create_lecture(
            number=1001,
            title="Click dashboard lecture",
            description="for stats api",
            scheduled_at=datetime(2026, 12, 2, 10, 0, tzinfo=timezone.utc),
            lecture_format=LectureFormat.ONLINE,
            stream_url="https://telemost.yandex.ru/j/dashboard",
            registration_open=True,
        )
        await repo.register_user_for_lecture(
            222,
            lecture.id,
            username="student",
            full_name="Student User",
        )
        await repo.create_click_event(
            user_id=222,
            lecture_id=lecture.id,
            event_type=ClickEventType.REGISTRATION_CLICK,
        )
        await repo.create_click_event(
            user_id=222,
            lecture_id=lecture.id,
            event_type=ClickEventType.STREAM_LINK,
        )
        await repo.create_click_event(
            user_id=222,
            lecture_id=lecture.id,
            event_type=ClickEventType.MATERIALS_LECTURE,
        )
        await repo.create_question(
            user_id=222,
            text="Когда будет запись?",
            username="student",
            full_name="Student User",
        )

    admin_header = {
        "Authorization": f"tma {build_init_data(bot_token=bot_token, user_id=111, username='admin_user')}"
    }
    user_header = {
        "Authorization": f"tma {build_init_data(bot_token=bot_token, user_id=222, username='student')}"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        click_types = await client.get("/api/click-types", headers=admin_header)
        assert click_types.status_code == 200
        assert any(item["event_type"] == "stream_link" for item in click_types.json())

        patch_click_type = await client.patch(
            "/api/click-types/materials_general",
            headers=admin_header,
            json={"enabled": False},
        )
        assert patch_click_type.status_code == 200
        assert patch_click_type.json()["enabled"] is False

        summary = await client.get("/api/click-stats/summary", headers=admin_header)
        assert summary.status_code == 200
        assert summary.json()["totals"]["all_time"] >= 1

        course_overview = await client.get("/api/course-overview?days=7", headers=admin_header)
        assert course_overview.status_code == 200
        assert course_overview.json()["lectures_total"] >= 1

        course_lectures = await client.get("/api/course-overview/lectures?days=7", headers=admin_header)
        assert course_lectures.status_code == 200
        assert isinstance(course_lectures.json(), list)
        assert course_lectures.json()
        assert "sparkline" in course_lectures.json()[0]

        timeseries = await client.get("/api/click-stats/timeseries?days=7", headers=admin_header)
        assert timeseries.status_code == 200
        assert isinstance(timeseries.json(), list)

        top_users = await client.get("/api/click-stats/top-users", headers=admin_header)
        assert top_users.status_code == 200
        assert top_users.json()

        funnel = await client.get(
            f"/api/click-stats/funnel?lecture_id={lecture.id}",
            headers=admin_header,
        )
        assert funnel.status_code == 200
        assert funnel.json()["lecture_id"] == lecture.id

        by_hour = await client.get(
            f"/api/click-stats/lecture/{lecture.id}/by-hour",
            headers=admin_header,
        )
        assert by_hour.status_code == 200
        assert isinstance(by_hour.json(), list)

        export_zip = await client.get("/api/export.zip", headers=admin_header)
        assert export_zip.status_code == 200
        assert export_zip.headers["content-type"].startswith("application/zip")
        assert len(export_zip.content) > 0

        forbidden_summary = await client.get("/api/click-stats/summary", headers=user_header)
        assert forbidden_summary.status_code == 403
        forbidden_course_overview = await client.get("/api/course-overview", headers=user_header)
        assert forbidden_course_overview.status_code == 403

        questions = await client.get("/api/questions", headers=admin_header)
        assert questions.status_code == 200
        question_id = questions.json()[0]["id"]

        answered = await client.patch(
            f"/api/questions/{question_id}",
            headers=admin_header,
            json={"status": "answered", "answer_text": "Запись появится после лекции."},
        )
        assert answered.status_code == 200
        assert answered.json()["status"] == "answered"
        assert dummy_bot.sent_messages
        assert dummy_bot.sent_messages[-1][0] == 222

        ignored = await client.patch(
            f"/api/questions/{question_id}",
            headers=admin_header,
            json={"status": "ignored"},
        )
        assert ignored.status_code == 200
        assert ignored.json()["status"] == "ignored"

    await engine.dispose()
