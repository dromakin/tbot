from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard
from bot.texts import CONTACT_TEXT

router = Router(name="contact")


@router.callback_query(MenuCallback.filter(F.action == "contact"))
async def contact_handler(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(CONTACT_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()
