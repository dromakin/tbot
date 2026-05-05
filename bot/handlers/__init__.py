from aiogram import Dispatcher

from bot.handlers import admin, contact, materials, menu, qa, registration, schedule, start, status, stream


def include_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(materials.router)
    dp.include_router(schedule.router)
    dp.include_router(contact.router)
    dp.include_router(registration.router)
    dp.include_router(status.router)
    dp.include_router(stream.router)
    dp.include_router(qa.router)
    dp.include_router(admin.router)
