from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.db.models import ClickEventType
from bot.db.repository import Repository
from bot.keyboards.inline import LectureCallback, MenuCallback, back_to_menu_keyboard, materials_keyboard
from bot.text_store import t

router = Router(name="materials")


@router.callback_query(MenuCallback.filter(F.action == "materials"))
async def materials_menu_handler(callback: CallbackQuery, repo: Repository, settings: Settings) -> None:
    lectures = await repo.list_lectures()
    if callback.message is not None:
        await callback.message.answer(
            t("materials", "intro"),
            reply_markup=materials_keyboard(lectures),
        )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "materials_general"))
async def materials_general_handler(callback: CallbackQuery, repo: Repository, settings: Settings) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return
    await repo.upsert_user(
        tg_user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )
    await repo.create_click_event(
        user_id=callback.from_user.id,
        event_type=ClickEventType.MATERIALS_GENERAL,
        lecture_id=None,
    )
    await callback.message.answer(
        t("materials", "general_url", general_materials_url=settings.general_materials_url),
        reply_markup=back_to_menu_keyboard(),
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
    await repo.upsert_user(
        tg_user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
    )

    lecture = await repo.get_lecture(callback_data.lecture_id)
    if lecture is None or not lecture.materials_url:
        await callback.message.answer(t("materials", "unavailable"), reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    is_registered = await repo.is_registered(callback.from_user.id, lecture.id)
    if not is_registered:
        await callback.message.answer(
            t("materials", "not_registered"),
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    await repo.create_click_event(
        user_id=callback.from_user.id,
        event_type=ClickEventType.MATERIALS_LECTURE,
        lecture_id=lecture.id,
    )
    await callback.message.answer(
        t("materials", "lecture_url", materials_url=lecture.materials_url),
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()
