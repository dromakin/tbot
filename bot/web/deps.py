from __future__ import annotations

from collections.abc import AsyncGenerator
from time import time

from aiogram import Bot
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.db.repository import Repository
from bot.web.auth import InitDataError, VerifiedTmaUser, verify_init_data


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_bot(request: Request) -> Bot:
    bot: Bot | None = getattr(request.app.state, "bot", None)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot runtime is unavailable",
        )
    return bot


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session


async def get_repo(session: AsyncSession = Depends(get_session)) -> Repository:
    return Repository(session)


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> VerifiedTmaUser:
    authorization = request.headers.get("Authorization", "")
    raw_init_data = ""

    prefix = "tma "
    if authorization.lower().startswith(prefix):
        raw_init_data = authorization[len(prefix) :].strip()
    else:
        raw_init_data = request.query_params.get("init_data", "").strip()

    if not raw_init_data and settings.web_dev_auth_bypass and settings.web_dev_user_id:
        username = settings.web_dev_user_username.strip() or None
        full_name = username or f"dev_{settings.web_dev_user_id}"
        return VerifiedTmaUser(
            tg_user_id=settings.web_dev_user_id,
            username=username,
            full_name=full_name,
            auth_date=int(time()),
        )

    if not raw_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Telegram Mini App authorization",
        )

    try:
        return verify_init_data(
            raw=raw_init_data,
            bot_token=settings.bot_token,
            max_age_sec=settings.web_init_data_max_age_sec,
        )
    except InitDataError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def require_admin(
    current_user: VerifiedTmaUser = Depends(get_current_user),
    settings: Settings = Depends(get_app_settings),
) -> VerifiedTmaUser:
    if current_user.tg_user_id not in settings.admin_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
