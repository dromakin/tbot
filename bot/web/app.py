from __future__ import annotations

from pathlib import Path

from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.web.routers.admin import router as admin_router
from bot.web.routers.health import router as health_router
from bot.web.routers.user import router as user_router


def create_app(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    bot: Bot | None = None,
) -> FastAPI:
    app = FastAPI(title="tbot mini app api")
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.bot = bot

    extra_origins = (
        ["http://localhost:5173", "http://127.0.0.1:5173"] if settings.web_dev_auth_bypass else []
    )
    allow_origins = [origin for origin in [settings.web_public_url, *extra_origins] if origin]
    if allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router)
    app.include_router(admin_router)
    app.include_router(user_router)

    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/", StaticFiles(directory=str(static_dir), html=True, check_dir=False), name="static")
    return app
