from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db.repository import Repository
from bot.keyboards.inline import MenuCallback, back_to_menu_keyboard

router = Router(name="status")


@router.callback_query(MenuCallback.filter(F.action == "status"))
async def registration_status_handler(callback: CallbackQuery, repo: Repository) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    registrations = await repo.get_user_registrations(callback.from_user.id)
    if not registrations:
        await callback.message.answer(
            "🛡 Результат проверки\n\n"
            "Регистрация не найдена!\n\n"
            "К сожалению, мы не нашли вашу регистрацию на лекции.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    lines = ["🛡 <b>Результат проверки</b>", "", "Вы зарегистрированы на лекции:"]
    for registration, lecture in registrations:
        lines.append(
            f"• Лекция №{lecture.number}: {lecture.title}\n"
            f"  Дата: {lecture.scheduled_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"  Регистрация: {registration.registered_at.strftime('%d.%m.%Y %H:%M')}"
        )

    await callback.message.answer("\n".join(lines), reply_markup=back_to_menu_keyboard())
    await callback.answer()
