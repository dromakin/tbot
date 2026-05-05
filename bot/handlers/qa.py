from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from bot.config import Settings
from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard
from bot.states import AskQuestionState
from bot.text_store import t

router = Router(name="qa")


@router.callback_query(MenuCallback.filter(F.action == "question"))
async def question_prompt_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await callback.message.answer(t("qa", "prompt"))
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
        await message.answer(t("qa", "non_text"))
        return

    await repo.upsert_user(
        tg_user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    question = await repo.create_question(
        user_id=message.from_user.id,
        text=message.text,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    nickname = f"@{message.from_user.username}" if message.from_user.username else "-"

    admin_message = t(
        "qa",
        "admin_forward",
        question_id=question.id,
        tg_user_id=message.from_user.id,
        nickname=nickname,
        full_name=message.from_user.full_name,
        question_text=message.text,
    )
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(admin_id, admin_message)
        except Exception:  # pragma: no cover - best-effort forward
            logger.exception("Failed to deliver question to admin_id=%s", admin_id)

    await message.answer(t("qa", "sent"), reply_markup=back_to_menu_keyboard())
    await state.clear()
