from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard, main_menu_keyboard
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
async def menu_program_handler(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(t("menu", "program_text"), reply_markup=back_to_menu_keyboard())
    await callback.answer()
