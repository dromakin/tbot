from __future__ import annotations

import asyncio
from contextlib import suppress

import uvicorn
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
from bot.web.app import create_app


async def run() -> None:
    settings = get_settings()
    if settings.web_dev_auth_bypass:
        logger.warning("DEV AUTH BYPASS ENABLED - never use in production")
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

    poll_task: asyncio.Task[None] | None = None
    web_task: asyncio.Task[None] | None = None
    web_server: uvicorn.Server | None = None

    try:
        if settings.web_enabled:
            web_app = create_app(settings=settings, session_factory=session_factory, bot=bot)
            web_config = uvicorn.Config(
                app=web_app,
                host=settings.web_host,
                port=settings.web_port,
                log_level="info",
            )
            web_server = uvicorn.Server(web_config)
            web_task = asyncio.create_task(web_server.serve(), name="fastapi")
            logger.info("Web server started on {}:{}", settings.web_host, settings.web_port)

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling started")
        poll_task = asyncio.create_task(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            name="polling",
        )

        running_tasks = [task for task in (poll_task, web_task) if task is not None]
        await asyncio.gather(*running_tasks)
    finally:
        if web_server is not None:
            web_server.should_exit = True

        for task in (poll_task, web_task):
            if task is not None and not task.done():
                task.cancel()

        for task in (poll_task, web_task):
            if task is not None:
                with suppress(Exception):
                    await task

        scheduler.shutdown(wait=False)
        await engine.dispose()
        await bot.session.close()
        logger.info("Bot stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
