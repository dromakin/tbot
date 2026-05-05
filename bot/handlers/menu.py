from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard, main_menu_keyboard
from bot.texts import MENU_TEXT, PROGRAM_TEXT

router = Router(name="menu")


@router.callback_query(MenuCallback.filter(F.action == "main"))
async def menu_main_handler(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "program"))
async def menu_program_handler(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(PROGRAM_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()
