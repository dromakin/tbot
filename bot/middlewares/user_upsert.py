from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.db.repository import Repository


class UserUpsertMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        repo: Repository | None = data.get("repo")
        if repo is not None:
            user = self._extract_user(event)
            if user is not None:
                await repo.upsert_user(
                    tg_user_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                )
        return await handler(event, data)

    @staticmethod
    def _extract_user(event: TelegramObject) -> Any | None:
        if isinstance(event, Message):
            return event.from_user
        if isinstance(event, CallbackQuery):
            return event.from_user
        return None
