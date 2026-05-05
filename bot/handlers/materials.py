from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.db.repository import Repository
from bot.keyboards.inline import LectureCallback, MenuCallback, back_to_menu_keyboard, materials_keyboard
from bot.texts import MATERIALS_TEXT

router = Router(name="materials")


@router.callback_query(MenuCallback.filter(F.action == "materials"))
async def materials_menu_handler(callback: CallbackQuery, repo: Repository, settings: Settings) -> None:
    lectures = await repo.list_lectures()
    if callback.message is not None:
        await callback.message.answer(
            MATERIALS_TEXT,
            reply_markup=materials_keyboard(lectures, settings.general_materials_url),
        )
    await callback.answer()


@router.callback_query(LectureCallback.filter(F.action == "materials"))
async def materials_for_lecture_handler(
    callback: CallbackQuery,
    callback_data: LectureCallback,
    repo: Repository,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    lecture = await repo.get_lecture(callback_data.lecture_id)
    if lecture is None or not lecture.materials_url:
        await callback.message.answer("Материалы для этой лекции пока недоступны.", reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    is_registered = await repo.is_registered(callback.from_user.id, lecture.id)
    if not is_registered:
        await callback.message.answer(
            "Вы не регистрировались на лекцию!\n\nДоп.материал вам не доступен!",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        f"✅ <b>Вы были зарегистрированы!</b>\n\nДоп. материал доступен по ссылке: {lecture.materials_url}",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
