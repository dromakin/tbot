from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from bot.config import get_settings
from bot.db.session import create_engine, create_session_factory
from bot.handlers import include_routers
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.user_upsert import UserUpsertMiddleware
from bot.scheduler import build_scheduler


async def run() -> None:
    settings = get_settings()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp["settings"] = settings
    dp["session_factory"] = session_factory

    dp.update.outer_middleware(DbSessionMiddleware(session_factory))
    dp.update.outer_middleware(UserUpsertMiddleware())
    include_routers(dp)

    scheduler = build_scheduler(bot=bot, session_factory=session_factory, settings=settings)
    scheduler.start()
    logger.info("Scheduler started")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await engine.dispose()
        await bot.session.close()
        logger.info("Bot stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
