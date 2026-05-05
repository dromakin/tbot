from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.models import ClickEventType, LectureFormat
from bot.db.repository import Repository
from bot.keyboards.inline import LectureCallback, back_to_menu_keyboard
from bot.text_store import t

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
        await callback.message.answer(t("stream", "lecture_not_found"), reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    if lecture.format != LectureFormat.ONLINE:
        await callback.message.answer(
            t("stream", "offline_no_link"),
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    if not lecture.stream_url:
        await callback.message.answer(
            t("stream", "link_pending"),
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    is_registered = await repo.is_registered(callback.from_user.id, lecture.id)
    if not is_registered:
        await callback.message.answer(
            t("stream", "not_registered"),
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    await repo.create_click_event(
        user_id=callback.from_user.id,
        lecture_id=lecture.id,
        event_type=ClickEventType.STREAM_LINK,
    )
    await callback.message.answer(
        t("stream", "success", lecture_number=lecture.number, stream_url=lecture.stream_url),
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
