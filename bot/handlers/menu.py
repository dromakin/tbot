from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard, main_menu_keyboard
from bot.services.program import build_program_html
from bot.text_store import t

router = Router(name="menu")


@router.callback_query(MenuCallback.filter(F.action == "main"))
async def menu_main_handler(callback: CallbackQuery, settings: Settings) -> None:
    if callback.message is not None:
        await callback.message.answer(
            t("start", "menu_text"),
            reply_markup=main_menu_keyboard(settings.web_public_url),
        )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "program"))
async def menu_program_handler(callback: CallbackQuery, repo: Repository) -> None:
    if callback.message is not None:
        header = t("menu", "program_header")
        lectures = await repo.list_lectures()
        await callback.message.answer(
            build_program_html(header=header, lectures=lectures),
            reply_markup=back_to_menu_keyboard(),
        )
    await callback.answer()
