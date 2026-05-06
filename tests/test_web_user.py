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
from bot.db.models import LectureFormat
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


@pytest.mark.asyncio
async def test_user_api_flow() -> None:
    bot_token = "test_bot_token"
    settings = Settings(
        BOT_TOKEN=bot_token,
        DB_DSN="sqlite+aiosqlite:///:memory:",
        ADMIN_IDS="111",
        WEB_PUBLIC_URL="https://example.com",
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app = create_app(settings=settings, session_factory=session_factory)

    async with session_factory() as session:
        repo = Repository(session)
        await repo.set_general_materials_url("https://example.com/general")
        await repo.upsert_user(222, "student", "Student User")

        open_lecture = await repo.create_lecture(
            number=501,
            title="Open user lecture",
            description="for user api",
            topics="1. Тема из БД\n2. Еще тема",
            scheduled_at=datetime(2026, 12, 2, 10, 0, tzinfo=timezone.utc),
            lecture_format=LectureFormat.ONLINE,
            stream_url="https://telemost.yandex.ru/j/user-open",
            materials_url="https://example.com/materials-open",
            registration_open=True,
        )
        closed_lecture = await repo.create_lecture(
            number=502,
            title="Closed user lecture",
            description="closed but with materials",
            topics="1. Закрытая тема",
            scheduled_at=datetime(2026, 12, 3, 10, 0, tzinfo=timezone.utc),
            lecture_format=LectureFormat.ONLINE,
            stream_url="https://telemost.yandex.ru/j/user-closed",
            materials_url="https://example.com/materials-closed",
            registration_open=True,
        )
        await repo.register_user_for_lecture(
            222,
            closed_lecture.id,
            username="student",
            full_name="Student User",
        )
        await repo.set_registration_open(closed_lecture.id, False)

    user_header = {
        "Authorization": f"tma {build_init_data(bot_token=bot_token, user_id=222, username='student')}"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        me = await client.get("/api/me", headers=user_header)
        assert me.status_code == 200
        assert me.json()["is_admin"] is False

        lectures = await client.get("/api/user/lectures", headers=user_header)
        assert lectures.status_code == 200
        assert lectures.json()
        assert len(lectures.json()) == 1
        lecture_id = lectures.json()[0]["lecture_id"]
        assert lectures.json()[0]["lecture_title"] == "Open user lecture"

        registered = await client.post(f"/api/user/lectures/{lecture_id}/register", headers=user_header)
        assert registered.status_code == 200
        assert registered.json()["status"] == "ok"

        stream = await client.get(f"/api/user/lectures/{lecture_id}/stream", headers=user_header)
        assert stream.status_code == 200
        assert stream.json()["status"] == "ok"
        assert stream.json()["url"]

        materials = await client.get(f"/api/user/lectures/{lecture_id}/materials", headers=user_header)
        assert materials.status_code == 200
        assert materials.json()["status"] == "ok"

        materials_list = await client.get("/api/user/materials/lectures", headers=user_header)
        assert materials_list.status_code == 200
        assert len(materials_list.json()) == 2
        material_lecture_ids = {row["lecture_id"] for row in materials_list.json()}
        assert lecture_id in material_lecture_ids

        closed_lecture_id = next(
            row["lecture_id"]
            for row in materials_list.json()
            if row["lecture_title"] == "Closed user lecture"
        )
        closed_materials = await client.get(
            f"/api/user/lectures/{closed_lecture_id}/materials",
            headers=user_header,
        )
        assert closed_materials.status_code == 200
        assert closed_materials.json()["status"] == "ok"

        general_materials = await client.get("/api/user/materials/general", headers=user_header)
        assert general_materials.status_code == 200
        assert general_materials.json()["status"] == "ok"

        registrations = await client.get("/api/user/registrations", headers=user_header)
        assert registrations.status_code == 200
        assert registrations.json()

        static_content = await client.get("/api/user/static", headers=user_header)
        assert static_content.status_code == 200
        payload = static_content.json()
        assert payload["program_header"]
        assert "contact_text" in payload
        assert payload["program_lectures"]
        assert payload["program_lectures"][0]["topics"] == ["1. Тема из БД", "2. Еще тема"]

    await engine.dispose()
