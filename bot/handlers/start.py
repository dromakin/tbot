from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import Settings
from bot.keyboards.inline import main_menu_keyboard
from bot.text_store import t

router = Router(name="start")


@router.message(CommandStart())
async def start_handler(message: Message, settings: Settings) -> None:
    await message.answer(t("start", "start_text"))
    await message.answer(t("start", "menu_text"), reply_markup=main_menu_keyboard(settings.web_public_url))


@router.message(Command("menu"))
@router.message(F.text & (F.text.casefold() == "меню"))
@router.message(F.text & (F.text.casefold() == "menu"))
async def menu_command_handler(message: Message, settings: Settings) -> None:
    await message.answer(t("start", "menu_text"), reply_markup=main_menu_keyboard(settings.web_public_url))
