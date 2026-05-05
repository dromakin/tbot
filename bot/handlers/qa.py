from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import Settings
from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard
from bot.states import AskQuestionState
from bot.texts import QUESTION_PROMPT_TEXT, QUESTION_SENT_TEXT

router = Router(name="qa")


@router.callback_query(MenuCallback.filter(F.action == "question"))
async def question_prompt_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await callback.message.answer(QUESTION_PROMPT_TEXT)
    await state.set_state(AskQuestionState.waiting_text)
    await callback.answer()


@router.message(AskQuestionState.waiting_text)
async def question_text_handler(
    message: Message,
    state: FSMContext,
    repo: Repository,
    settings: Settings,
) -> None:
    if message.from_user is None or message.text is None:
        await message.answer("Пожалуйста, отправьте вопрос текстом.")
        return

    question = await repo.create_question(user_id=message.from_user.id, text=message.text)
    nickname = f"@{message.from_user.username}" if message.from_user.username else "-"

    admin_message = (
        f"📩 Новый вопрос #{question.id}\n"
        f"tg_user_id: <code>{message.from_user.id}</code>\n"
        f"username: {nickname}\n"
        f"full_name: {message.from_user.full_name}\n\n"
        f"{message.text}"
    )
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(admin_id, admin_message)
        except Exception:  # pragma: no cover - best-effort forward
            logger.exception("Failed to deliver question to admin_id=%s", admin_id)

    await message.answer(QUESTION_SENT_TEXT, reply_markup=back_to_menu_keyboard())
    await state.clear()
