from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard
from bot.text_store import t

router = Router(name="status")


@router.callback_query(MenuCallback.filter(F.action == "status"))
async def registration_status_handler(callback: CallbackQuery, repo: Repository) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    registrations = await repo.get_user_registrations(callback.from_user.id)
    if not registrations:
        await callback.message.answer(
            t("status", "empty"),
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    lines = [t("status", "header")]
    for registration, lecture in registrations:
        lines.append(
            t(
                "status",
                "item",
                lecture_number=lecture.number,
                lecture_title=lecture.title,
                lecture_scheduled_at=lecture.scheduled_at.strftime("%d.%m.%Y %H:%M"),
                registered_at=registration.registered_at.strftime("%d.%m.%Y %H:%M"),
            )
        )

    await callback.message.answer("\n".join(lines), reply_markup=back_to_menu_keyboard())
    await callback.answer()
