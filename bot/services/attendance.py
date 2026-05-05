from __future__ import annotations

from bot.db.repository import Repository


async def register_stream_click(repo: Repository, user_id: int, lecture_id: int) -> None:
    """Persist a single click used as attendance proxy."""
    await repo.create_link_click(user_id=user_id, lecture_id=lecture_id)
