from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from bot.config import Settings
from bot.db.models import ClickEventType, LectureFormat
from bot.db.repository import Repository
from bot.text_store import t
from bot.web.auth import VerifiedTmaUser
from bot.web.deps import get_app_settings, get_current_user, get_repo
from bot.web.schemas import UserActionOut, UserLectureOut, UserRegistrationOut, UserStaticOut

router = APIRouter(prefix="/api/user", tags=["user"])


def _to_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def get_user_or_403(
    current_user: VerifiedTmaUser = Depends(get_current_user),
) -> VerifiedTmaUser:
    return current_user


async def _upsert_current_user(repo: Repository, current_user: VerifiedTmaUser) -> None:
    await repo.upsert_user(
        tg_user_id=current_user.tg_user_id,
        username=current_user.username,
        full_name=current_user.full_name,
    )


@router.get("/lectures", response_model=list[UserLectureOut])
async def get_user_lectures(
    current_user: VerifiedTmaUser = Depends(get_user_or_403),
    repo: Repository = Depends(get_repo),
) -> list[UserLectureOut]:
    lectures = await repo.list_lectures()
    registrations = await repo.get_user_registrations(current_user.tg_user_id)
    registered_lecture_ids = {lecture.id for _, lecture in registrations}
    now = datetime.now(timezone.utc)

    result: list[UserLectureOut] = []
    for lecture in lectures:
        scheduled_at = _to_aware(lecture.scheduled_at)
        if not lecture.registration_open and scheduled_at < now:
            continue

        result.append(
            UserLectureOut(
                lecture_id=lecture.id,
                lecture_number=lecture.number,
                lecture_title=lecture.title,
                description=lecture.description,
                scheduled_at=scheduled_at,
                format=lecture.format,
                registration_open=lecture.registration_open,
                is_registered=lecture.id in registered_lecture_ids,
                has_materials=bool(lecture.materials_url),
                has_stream=lecture.format == LectureFormat.ONLINE and bool(lecture.stream_url),
            )
        )
    return result


@router.post("/lectures/{lecture_id}/register", response_model=UserActionOut)
async def register_for_lecture(
    lecture_id: int,
    current_user: VerifiedTmaUser = Depends(get_user_or_403),
    repo: Repository = Depends(get_repo),
) -> UserActionOut:
    await _upsert_current_user(repo, current_user)
    await repo.create_click_event(
        user_id=current_user.tg_user_id,
        lecture_id=lecture_id,
        event_type=ClickEventType.REGISTRATION_CLICK,
    )
    created, lecture = await repo.register_user_for_lecture(
        user_id=current_user.tg_user_id,
        lecture_id=lecture_id,
        username=current_user.username,
        full_name=current_user.full_name,
    )
    if lecture is None:
        return UserActionOut(status="not_found", message=t("registration", "lecture_not_found"))
    if not lecture.registration_open:
        return UserActionOut(status="closed", message=t("registration", "closed"))
    if not created:
        return UserActionOut(
            status="already_registered",
            message=t(
                "registration",
                "already_registered",
                lecture_number=lecture.number,
                lecture_title=lecture.title,
            ),
        )
    return UserActionOut(
        status="ok",
        message=t(
            "registration",
            "success",
            lecture_number=lecture.number,
            lecture_title=lecture.title,
        ),
    )


@router.get("/lectures/{lecture_id}/stream", response_model=UserActionOut)
async def get_stream_for_lecture(
    lecture_id: int,
    current_user: VerifiedTmaUser = Depends(get_user_or_403),
    repo: Repository = Depends(get_repo),
) -> UserActionOut:
    await _upsert_current_user(repo, current_user)
    lecture = await repo.get_lecture(lecture_id)
    if lecture is None:
        return UserActionOut(status="not_found", message=t("stream", "lecture_not_found"))
    if lecture.format != LectureFormat.ONLINE:
        return UserActionOut(status="offline", message=t("stream", "offline_no_link"))
    if not lecture.stream_url:
        return UserActionOut(status="pending", message=t("stream", "link_pending"))

    is_registered = await repo.is_registered(current_user.tg_user_id, lecture.id)
    if not is_registered:
        return UserActionOut(status="not_registered", message=t("stream", "not_registered"))

    await repo.create_click_event(
        user_id=current_user.tg_user_id,
        lecture_id=lecture.id,
        event_type=ClickEventType.STREAM_LINK,
    )
    return UserActionOut(
        status="ok",
        message=t("stream", "success", lecture_number=lecture.number, stream_url=lecture.stream_url),
        url=lecture.stream_url,
    )


@router.get("/lectures/{lecture_id}/materials", response_model=UserActionOut)
async def get_materials_for_lecture(
    lecture_id: int,
    current_user: VerifiedTmaUser = Depends(get_user_or_403),
    repo: Repository = Depends(get_repo),
) -> UserActionOut:
    await _upsert_current_user(repo, current_user)
    lecture = await repo.get_lecture(lecture_id)
    if lecture is None:
        return UserActionOut(status="not_found", message=t("stream", "lecture_not_found"))
    if not lecture.materials_url:
        return UserActionOut(status="pending", message=t("materials", "unavailable"))

    is_registered = await repo.is_registered(current_user.tg_user_id, lecture.id)
    if not is_registered:
        return UserActionOut(status="not_registered", message=t("materials", "not_registered"))

    await repo.create_click_event(
        user_id=current_user.tg_user_id,
        lecture_id=lecture.id,
        event_type=ClickEventType.MATERIALS_LECTURE,
    )
    return UserActionOut(
        status="ok",
        message=t("materials", "lecture_url", materials_url=lecture.materials_url),
        url=lecture.materials_url,
    )


@router.get("/materials/general", response_model=UserActionOut)
async def get_general_materials(
    current_user: VerifiedTmaUser = Depends(get_user_or_403),
    settings: Settings = Depends(get_app_settings),
    repo: Repository = Depends(get_repo),
) -> UserActionOut:
    await _upsert_current_user(repo, current_user)
    await repo.create_click_event(
        user_id=current_user.tg_user_id,
        lecture_id=None,
        event_type=ClickEventType.MATERIALS_GENERAL,
    )
    return UserActionOut(
        status="ok",
        message=t("materials", "general_url", general_materials_url=settings.general_materials_url),
        url=settings.general_materials_url,
    )


@router.get("/registrations", response_model=list[UserRegistrationOut])
async def get_user_registrations(
    current_user: VerifiedTmaUser = Depends(get_user_or_403),
    repo: Repository = Depends(get_repo),
) -> list[UserRegistrationOut]:
    rows = await repo.get_user_registrations(current_user.tg_user_id)
    return [
        UserRegistrationOut(
            lecture_id=lecture.id,
            lecture_number=lecture.number,
            lecture_title=lecture.title,
            scheduled_at=_to_aware(lecture.scheduled_at),
            registered_at=registration.registered_at,
        )
        for registration, lecture in rows
    ]


@router.get("/static", response_model=UserStaticOut)
async def get_user_static(
    _current_user: VerifiedTmaUser = Depends(get_user_or_403),
) -> UserStaticOut:
    return UserStaticOut(
        program_text=t("menu", "program_text"),
        contact_text=t("contact", "text"),
    )
