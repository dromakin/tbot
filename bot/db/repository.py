from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import Select, distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Lecture, LectureFormat, LinkClick, Question, Registration, User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class LectureStats:
    lecture_id: int
    lecture_number: int
    lecture_title: str
    registrations_count: int
    unique_clicks_count: int
    total_clicks_count: int


@dataclass(slots=True)
class ExportRow:
    tg_user_id: int
    username: str | None
    full_name: str
    lecture_number: int
    lecture_title: str
    registered_at: datetime
    clicks_count: int
    first_click_at: datetime | None
    last_click_at: datetime | None


@dataclass(slots=True)
class LectureRegistrationRow:
    tg_user_id: int
    username: str | None
    full_name: str
    registered_at: datetime
    clicks_count: int


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_user(self, tg_user_id: int, username: str | None, full_name: str) -> User:
        user = await self.session.get(User, tg_user_id)
        if user is None:
            user = User(
                tg_user_id=tg_user_id,
                username=username,
                full_name=full_name,
                first_seen_at=utcnow(),
                last_seen_at=utcnow(),
            )
            self.session.add(user)
        else:
            user.username = username
            user.full_name = full_name
            user.last_seen_at = utcnow()
        await self.session.commit()
        return user

    async def create_lecture(
        self,
        *,
        number: int,
        title: str,
        description: str,
        scheduled_at: datetime,
        lecture_format: LectureFormat,
        stream_url: str | None = None,
        materials_url: str | None = None,
        registration_open: bool = False,
    ) -> Lecture:
        lecture = Lecture(
            number=number,
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            format=lecture_format,
            stream_url=stream_url,
            materials_url=materials_url,
            registration_open=registration_open,
        )
        self.session.add(lecture)
        await self.session.commit()
        await self.session.refresh(lecture)
        return lecture

    async def list_lectures(self) -> list[Lecture]:
        result = await self.session.execute(select(Lecture).order_by(Lecture.number.asc()))
        return list(result.scalars().all())

    async def list_open_lectures(self) -> list[Lecture]:
        result = await self.session.execute(
            select(Lecture)
            .where(Lecture.registration_open.is_(True))
            .order_by(Lecture.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def list_online_lectures(self) -> list[Lecture]:
        result = await self.session.execute(
            select(Lecture)
            .where(Lecture.format == LectureFormat.ONLINE)
            .order_by(Lecture.scheduled_at.asc())
        )
        return list(result.scalars().all())

    async def get_lecture(self, lecture_id: int) -> Lecture | None:
        return await self.session.get(Lecture, lecture_id)

    async def delete_lecture(self, lecture_id: int) -> bool:
        lecture = await self.session.get(Lecture, lecture_id)
        if lecture is None:
            return False
        await self.session.delete(lecture)
        await self.session.commit()
        return True

    async def set_registration_open(self, lecture_id: int, is_open: bool) -> bool:
        lecture = await self.session.get(Lecture, lecture_id)
        if lecture is None:
            return False
        lecture.registration_open = is_open
        await self.session.commit()
        return True

    async def set_stream_url(self, lecture_id: int, stream_url: str) -> bool:
        lecture = await self.session.get(Lecture, lecture_id)
        if lecture is None:
            return False
        lecture.stream_url = stream_url
        await self.session.commit()
        return True

    async def set_materials_url(self, lecture_id: int, materials_url: str) -> bool:
        lecture = await self.session.get(Lecture, lecture_id)
        if lecture is None:
            return False
        lecture.materials_url = materials_url
        await self.session.commit()
        return True

    async def register_user_for_lecture(self, user_id: int, lecture_id: int) -> tuple[bool, Lecture | None]:
        lecture = await self.session.get(Lecture, lecture_id)
        if lecture is None:
            return False, None
        if not lecture.registration_open:
            return False, lecture
        existing = await self.session.execute(
            select(Registration).where(
                Registration.user_id == user_id,
                Registration.lecture_id == lecture_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return False, lecture

        registration = Registration(user_id=user_id, lecture_id=lecture_id, registered_at=utcnow())
        self.session.add(registration)
        await self.session.commit()
        return True, lecture

    async def is_registered(self, user_id: int, lecture_id: int) -> bool:
        result = await self.session.execute(
            select(Registration.id).where(
                Registration.user_id == user_id,
                Registration.lecture_id == lecture_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_user_registrations(self, user_id: int) -> list[tuple[Registration, Lecture]]:
        stmt: Select[tuple[Registration, Lecture]] = (
            select(Registration, Lecture)
            .join(Lecture, Lecture.id == Registration.lecture_id)
            .where(Registration.user_id == user_id)
            .order_by(Lecture.scheduled_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def create_link_click(self, user_id: int, lecture_id: int) -> None:
        click = LinkClick(user_id=user_id, lecture_id=lecture_id, clicked_at=utcnow())
        self.session.add(click)
        await self.session.commit()

    async def create_question(self, user_id: int, text: str) -> Question:
        question = Question(user_id=user_id, text=text, created_at=utcnow())
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def list_registered_users_for_lecture(self, lecture_id: int) -> list[int]:
        result = await self.session.execute(
            select(Registration.user_id).where(Registration.lecture_id == lecture_id)
        )
        return [row[0] for row in result.all()]

    async def list_lecture_registration_rows(self, lecture_id: int) -> list[LectureRegistrationRow]:
        clicks_agg = (
            select(
                LinkClick.user_id.label("user_id"),
                func.count(LinkClick.id).label("clicks_count"),
            )
            .where(LinkClick.lecture_id == lecture_id)
            .group_by(LinkClick.user_id)
            .subquery()
        )
        stmt = (
            select(
                User.tg_user_id,
                User.username,
                User.full_name,
                Registration.registered_at,
                func.coalesce(clicks_agg.c.clicks_count, 0),
            )
            .join(Registration, Registration.user_id == User.tg_user_id)
            .outerjoin(clicks_agg, clicks_agg.c.user_id == User.tg_user_id)
            .where(Registration.lecture_id == lecture_id)
            .order_by(User.tg_user_id.asc())
        )
        result = await self.session.execute(stmt)
        return [
            LectureRegistrationRow(
                tg_user_id=row[0],
                username=row[1],
                full_name=row[2],
                registered_at=row[3],
                clicks_count=int(row[4]),
            )
            for row in result.all()
        ]

    async def close_started_registrations(self) -> int:
        stmt = (
            update(Lecture)
            .where(Lecture.registration_open.is_(True), Lecture.scheduled_at <= utcnow())
            .values(registration_open=False)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return int(result.rowcount or 0)

    async def get_stats(self) -> list[LectureStats]:
        clicks_agg = (
            select(
                LinkClick.lecture_id.label("lecture_id"),
                func.count(LinkClick.id).label("total_clicks"),
                func.count(distinct(LinkClick.user_id)).label("unique_clicks"),
            )
            .group_by(LinkClick.lecture_id)
            .subquery()
        )
        regs_agg = (
            select(
                Registration.lecture_id.label("lecture_id"),
                func.count(Registration.id).label("registrations"),
            )
            .group_by(Registration.lecture_id)
            .subquery()
        )
        stmt = (
            select(
                Lecture.id,
                Lecture.number,
                Lecture.title,
                func.coalesce(regs_agg.c.registrations, 0),
                func.coalesce(clicks_agg.c.unique_clicks, 0),
                func.coalesce(clicks_agg.c.total_clicks, 0),
            )
            .outerjoin(regs_agg, regs_agg.c.lecture_id == Lecture.id)
            .outerjoin(clicks_agg, clicks_agg.c.lecture_id == Lecture.id)
            .order_by(Lecture.number.asc())
        )
        result = await self.session.execute(stmt)
        return [
            LectureStats(
                lecture_id=row[0],
                lecture_number=row[1],
                lecture_title=row[2],
                registrations_count=int(row[3]),
                unique_clicks_count=int(row[4]),
                total_clicks_count=int(row[5]),
            )
            for row in result.all()
        ]

    async def get_export_rows(self) -> list[ExportRow]:
        clicks_agg = (
            select(
                LinkClick.user_id.label("user_id"),
                LinkClick.lecture_id.label("lecture_id"),
                func.count(LinkClick.id).label("clicks_count"),
                func.min(LinkClick.clicked_at).label("first_click_at"),
                func.max(LinkClick.clicked_at).label("last_click_at"),
            )
            .group_by(LinkClick.user_id, LinkClick.lecture_id)
            .subquery()
        )
        stmt = (
            select(
                User.tg_user_id,
                User.username,
                User.full_name,
                Lecture.number,
                Lecture.title,
                Registration.registered_at,
                func.coalesce(clicks_agg.c.clicks_count, 0),
                clicks_agg.c.first_click_at,
                clicks_agg.c.last_click_at,
            )
            .join(Registration, Registration.user_id == User.tg_user_id)
            .join(Lecture, Lecture.id == Registration.lecture_id)
            .outerjoin(
                clicks_agg,
                (clicks_agg.c.user_id == User.tg_user_id) & (clicks_agg.c.lecture_id == Lecture.id),
            )
            .order_by(Lecture.number.asc(), User.tg_user_id.asc())
        )
        result = await self.session.execute(stmt)
        rows = []
        for row in result.all():
            rows.append(
                ExportRow(
                    tg_user_id=row[0],
                    username=row[1],
                    full_name=row[2],
                    lecture_number=row[3],
                    lecture_title=row[4],
                    registered_at=row[5],
                    clicks_count=int(row[6]),
                    first_click_at=row[7],
                    last_click_at=row[8],
                )
            )
        return rows
