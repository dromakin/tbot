from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.base import Base
from bot.db.repository import Repository


@pytest.mark.asyncio
async def test_repository_app_settings_roundtrip() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        repo = Repository(session)

        assert await repo.get_general_materials_url() is None

        await repo.set_general_materials_url("https://example.com/general-materials")
        assert await repo.get_general_materials_url() == "https://example.com/general-materials"

        await repo.set_general_materials_url("   ")
        assert await repo.get_general_materials_url() is None

        assert await repo.get_auto_close_hours() == 24
        await repo.set_auto_close_hours(48)
        assert await repo.get_auto_close_hours() == 48

    await engine.dispose()
