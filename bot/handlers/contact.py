from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard
from bot.text_store import t

router = Router(name="contact")


@router.callback_query(MenuCallback.filter(F.action == "contact"))
async def contact_handler(callback: CallbackQuery) -> None:
    if callback.message is not None:
        await callback.message.answer(t("contact", "text"), reply_markup=back_to_menu_keyboard())
    await callback.answer()
