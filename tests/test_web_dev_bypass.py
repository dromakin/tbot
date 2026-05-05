from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import Settings
from bot.db.base import Base
from bot.web.app import create_app


@pytest.mark.asyncio
async def test_web_dev_bypass_allows_local_request_without_init_data() -> None:
    settings = Settings(
        BOT_TOKEN="test_bot_token",
        DB_DSN="sqlite+aiosqlite:///:memory:",
        ADMIN_IDS="111",
        WEB_PUBLIC_URL="https://example.com",
        WEB_DEV_AUTH_BYPASS=True,
        WEB_DEV_USER_ID=111,
        WEB_DEV_USER_USERNAME="dev_admin",
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app = create_app(settings=settings, session_factory=session_factory)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["is_admin"] is True
        assert response.json()["tg_user_id"] == 111

    await engine.dispose()


@pytest.mark.asyncio
async def test_web_dev_bypass_disabled_keeps_auth_required() -> None:
    settings = Settings(
        BOT_TOKEN="test_bot_token",
        DB_DSN="sqlite+aiosqlite:///:memory:",
        ADMIN_IDS="111",
        WEB_PUBLIC_URL="https://example.com",
        WEB_DEV_AUTH_BYPASS=False,
        WEB_DEV_USER_ID=111,
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app = create_app(settings=settings, session_factory=session_factory)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing Telegram Mini App authorization"

    await engine.dispose()
