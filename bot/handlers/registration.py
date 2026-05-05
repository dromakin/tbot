from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.repository import Repository
from bot.keyboards.inline import LectureCallback, MenuCallback, back_to_menu_keyboard, open_lectures_keyboard
from bot.texts import REGISTRATION_CLOSED_TEXT

router = Router(name="registration")


@router.callback_query(MenuCallback.filter(F.action == "register"))
async def registration_menu_handler(callback: CallbackQuery, repo: Repository) -> None:
    if callback.message is None:
        await callback.answer()
        return

    lectures = await repo.list_open_lectures()
    if not lectures:
        await callback.message.answer(REGISTRATION_CLOSED_TEXT, reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    await callback.message.answer(
        "<b>📝 Регистрация на лекцию</b>\n\nВыберите лекцию из списка ниже:",
        reply_markup=open_lectures_keyboard(lectures, action="register"),
    )
    await callback.answer()


@router.callback_query(LectureCallback.filter(F.action == "register"))
async def register_for_lecture_handler(
    callback: CallbackQuery,
    callback_data: LectureCallback,
    repo: Repository,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    created, lecture = await repo.register_user_for_lecture(
        user_id=callback.from_user.id,
        lecture_id=callback_data.lecture_id,
    )
    if lecture is None:
        await callback.message.answer("Лекция не найдена.", reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    if not lecture.registration_open:
        await callback.message.answer(REGISTRATION_CLOSED_TEXT, reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    if created:
        text = (
            "✅ <b>Регистрация прошла успешно!</b>\n"
            f"Лекция №{lecture.number}: {lecture.title}\n"
            "До встречи на лекции! 🚀"
        )
    else:
        text = (
            "✅ <b>Вы уже зарегистрированы!</b>\n"
            f"Лекция №{lecture.number}: {lecture.title}"
        )
    await callback.message.answer(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()
