from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.models import LectureFormat
from bot.db.repository import Repository
from bot.keyboards.inline import LectureCallback, back_to_menu_keyboard

router = Router(name="stream")


@router.callback_query(LectureCallback.filter(F.action == "stream"))
async def stream_link_handler(
    callback: CallbackQuery,
    callback_data: LectureCallback,
    repo: Repository,
) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    lecture = await repo.get_lecture(callback_data.lecture_id)
    if lecture is None:
        await callback.message.answer("Лекция не найдена.", reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    if lecture.format != LectureFormat.ONLINE:
        await callback.message.answer(
            "Для очной лекции ссылка на онлайн-подключение не требуется.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    if not lecture.stream_url:
        await callback.message.answer(
            "Ссылка для подключения будет опубликована позже.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    is_registered = await repo.is_registered(callback.from_user.id, lecture.id)
    if not is_registered:
        await callback.message.answer(
            "Для получения ссылки сначала зарегистрируйтесь на лекцию.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    await repo.create_link_click(user_id=callback.from_user.id, lecture_id=lecture.id)
    await callback.message.answer(
        f"🔗 Ссылка для подключения к лекции №{lecture.number}:\n{lecture.stream_url}",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
