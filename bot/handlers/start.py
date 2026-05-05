from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.keyboards.inline import main_menu_keyboard
from bot.texts import MENU_TEXT, START_TEXT

router = Router(name="start")


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(START_TEXT)
    await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
@router.message(F.text & (F.text.casefold() == "меню"))
@router.message(F.text & (F.text.casefold() == "menu"))
async def menu_command_handler(message: Message) -> None:
    await message.answer(MENU_TEXT, reply_markup=main_menu_keyboard())
