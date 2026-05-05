from __future__ import annotations

from fastapi import APIRouter, Depends

from bot.config import Settings
from bot.web.auth import VerifiedTmaUser
from bot.web.deps import get_app_settings, get_current_user
from bot.web.schemas import MeOut

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/me", response_model=MeOut)
async def me_handler(
    current_user: VerifiedTmaUser = Depends(get_current_user),
    settings: Settings = Depends(get_app_settings),
) -> MeOut:
    return MeOut(
        tg_user_id=current_user.tg_user_id,
        username=current_user.username,
        full_name=current_user.full_name,
        is_admin=current_user.tg_user_id in settings.admin_ids,
    )
