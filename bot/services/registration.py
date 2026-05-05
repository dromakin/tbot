from __future__ import annotations

from bot.db.repository import Repository


async def register_to_lecture(
    repo: Repository,
    user_id: int,
    lecture_id: int,
    *,
    username: str | None,
    full_name: str,
) -> tuple[bool, bool]:
    created, lecture = await repo.register_user_for_lecture(
        user_id=user_id,
        lecture_id=lecture_id,
        username=username,
        full_name=full_name,
    )
    return created, lecture is not None
