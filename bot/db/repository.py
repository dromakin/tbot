from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, case, distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    ClickEvent,
    ClickEventSetting,
    ClickEventType,
    Lecture,
    LectureFormat,
    Question,
    QuestionStatus,
    Registration,
    User,
)


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


@dataclass(slots=True)
class ClickTypeSettingRow:
    event_type: ClickEventType
    enabled: bool


@dataclass(slots=True)
class ClickTypeStatsRow:
    event_type: ClickEventType
    total_clicks: int
    unique_users: int


@dataclass(slots=True)
class LectureClickStatsRow:
    lecture_id: int
    lecture_number: int
    lecture_title: str
    stream_link_clicks: int
    materials_lecture_clicks: int
    registration_clicks: int
    total_clicks: int


@dataclass(slots=True)
class ClickSummaryItemRow:
    event_type: ClickEventType
    today_count: int
    week_count: int
    all_time_count: int


@dataclass(slots=True)
class ClickSummaryTotalsRow:
    today_count: int
    week_count: int
    all_time_count: int


@dataclass(slots=True)
class ClickTimeseriesPointRow:
    bucket_date: str
    event_type: ClickEventType
    clicks_count: int


@dataclass(slots=True)
class ClickTopUserRow:
    tg_user_id: int
    username: str | None
    full_name: str
    clicks_count: int


@dataclass(slots=True)
class LectureFunnelRow:
    lecture_id: int
    registration_clicks: int
    registrations: int
    stream_link_unique: int
    materials_lecture_unique: int


@dataclass(slots=True)
class LectureHourBucketRow:
    bucket_start: datetime
    event_type: ClickEventType
    clicks_count: int


@dataclass(slots=True)
class LectureOverviewSparklinePointRow:
    date: str
    count: int


@dataclass(slots=True)
class CourseOverviewRow:
    lectures_total: int
    lectures_open: int
    lectures_past: int
    registrations_total: int
    unique_students: int
    avg_registrations_per_lecture: float
    attendance_rate: float
    questions_pending_total: int
    period_clicks_total: int


@dataclass(slots=True)
class LectureOverviewRow:
    lecture_id: int
    lecture_number: int
    lecture_title: str
    scheduled_at: datetime
    registration_open: bool
    status: str
    registrations: int
    stream_link_unique: int
    materials_lecture_unique: int
    attendance_rate: float
    sparkline: list[LectureOverviewSparklinePointRow]


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

    async def set_materials_url(self, lecture_id: int, materials_url: str | None) -> bool:
        lecture = await self.session.get(Lecture, lecture_id)
        if lecture is None:
            return False
        lecture.materials_url = materials_url
        await self.session.commit()
        return True

    async def register_user_for_lecture(
        self,
        user_id: int,
        lecture_id: int,
        *,
        username: str | None,
        full_name: str,
    ) -> tuple[bool, Lecture | None]:
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

        registration = Registration(
            user_id=user_id,
            username=username,
            full_name=full_name,
            lecture_id=lecture_id,
            registered_at=utcnow(),
        )
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

    async def list_click_type_settings(self) -> list[ClickTypeSettingRow]:
        result = await self.session.execute(select(ClickEventSetting.event_type, ClickEventSetting.enabled))
        configured = {row[0]: bool(row[1]) for row in result.all()}
        return [
            ClickTypeSettingRow(event_type=event_type, enabled=configured.get(event_type, True))
            for event_type in ClickEventType
        ]

    async def set_click_type_enabled(
        self,
        event_type: ClickEventType,
        enabled: bool,
    ) -> ClickTypeSettingRow:
        setting = await self.session.get(ClickEventSetting, event_type)
        if setting is None:
            setting = ClickEventSetting(event_type=event_type, enabled=enabled)
            self.session.add(setting)
        else:
            setting.enabled = enabled
        await self.session.commit()
        return ClickTypeSettingRow(event_type=event_type, enabled=enabled)

    async def create_click_event(
        self,
        *,
        user_id: int,
        event_type: ClickEventType,
        lecture_id: int | None = None,
    ) -> bool:
        setting = await self.session.get(ClickEventSetting, event_type)
        if setting is not None and not setting.enabled:
            return False

        event = ClickEvent(
            user_id=user_id,
            lecture_id=lecture_id,
            event_type=event_type,
            created_at=utcnow(),
        )
        self.session.add(event)
        await self.session.commit()
        return True

    async def create_link_click(self, user_id: int, lecture_id: int) -> None:
        await self.create_click_event(
            user_id=user_id,
            lecture_id=lecture_id,
            event_type=ClickEventType.STREAM_LINK,
        )

    async def create_question(
        self,
        user_id: int,
        text: str,
        *,
        username: str | None,
        full_name: str,
    ) -> Question:
        question = Question(
            user_id=user_id,
            username=username,
            full_name=full_name,
            text=text,
            status=QuestionStatus.PENDING,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def list_questions(
        self,
        *,
        status: QuestionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Question]:
        stmt = select(Question)
        if status is not None:
            stmt = stmt.where(Question.status == status)
        stmt = stmt.order_by(Question.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def set_question_ignored(self, question_id: int) -> Question | None:
        question = await self.session.get(Question, question_id)
        if question is None:
            return None
        question.status = QuestionStatus.IGNORED
        question.answer_text = None
        question.answered_at = None
        question.answered_by_admin_id = None
        question.answered_by_admin_username = None
        question.updated_at = utcnow()
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def answer_question(
        self,
        question_id: int,
        *,
        answer_text: str,
        admin_id: int,
        admin_username: str | None,
    ) -> Question | None:
        question = await self.session.get(Question, question_id)
        if question is None:
            return None
        now = utcnow()
        question.status = QuestionStatus.ANSWERED
        question.answer_text = answer_text
        question.answered_at = now
        question.answered_by_admin_id = admin_id
        question.answered_by_admin_username = admin_username
        question.updated_at = now
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
                ClickEvent.user_id.label("user_id"),
                func.count(ClickEvent.id).label("clicks_count"),
            )
            .where(
                ClickEvent.lecture_id == lecture_id,
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
            )
            .group_by(ClickEvent.user_id)
            .subquery()
        )
        stmt = (
            select(
                Registration.user_id,
                Registration.username,
                Registration.full_name,
                Registration.registered_at,
                func.coalesce(clicks_agg.c.clicks_count, 0),
            )
            .select_from(Registration)
            .outerjoin(clicks_agg, clicks_agg.c.user_id == Registration.user_id)
            .where(Registration.lecture_id == lecture_id)
            .order_by(Registration.user_id.asc())
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
                ClickEvent.lecture_id.label("lecture_id"),
                func.count(ClickEvent.id).label("total_clicks"),
                func.count(distinct(ClickEvent.user_id)).label("unique_clicks"),
            )
            .where(
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.lecture_id)
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

    async def get_click_type_stats(self) -> list[ClickTypeStatsRow]:
        stmt = (
            select(
                ClickEvent.event_type,
                func.count(ClickEvent.id),
                func.count(distinct(ClickEvent.user_id)),
            )
            .group_by(ClickEvent.event_type)
            .order_by(ClickEvent.event_type.asc())
        )
        result = await self.session.execute(stmt)
        return [
            ClickTypeStatsRow(
                event_type=row[0],
                total_clicks=int(row[1]),
                unique_users=int(row[2]),
            )
            for row in result.all()
        ]

    async def get_lecture_click_stats(self) -> list[LectureClickStatsRow]:
        stream_agg = (
            select(ClickEvent.lecture_id.label("lecture_id"), func.count(ClickEvent.id).label("stream_clicks"))
            .where(
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.lecture_id)
            .subquery()
        )
        materials_agg = (
            select(ClickEvent.lecture_id.label("lecture_id"), func.count(ClickEvent.id).label("materials_clicks"))
            .where(
                ClickEvent.event_type == ClickEventType.MATERIALS_LECTURE,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.lecture_id)
            .subquery()
        )
        registration_agg = (
            select(ClickEvent.lecture_id.label("lecture_id"), func.count(ClickEvent.id).label("registration_clicks"))
            .where(
                ClickEvent.event_type == ClickEventType.REGISTRATION_CLICK,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.lecture_id)
            .subquery()
        )
        stmt = (
            select(
                Lecture.id,
                Lecture.number,
                Lecture.title,
                func.coalesce(stream_agg.c.stream_clicks, 0),
                func.coalesce(materials_agg.c.materials_clicks, 0),
                func.coalesce(registration_agg.c.registration_clicks, 0),
            )
            .outerjoin(stream_agg, stream_agg.c.lecture_id == Lecture.id)
            .outerjoin(materials_agg, materials_agg.c.lecture_id == Lecture.id)
            .outerjoin(registration_agg, registration_agg.c.lecture_id == Lecture.id)
            .order_by(Lecture.number.asc())
        )
        result = await self.session.execute(stmt)
        rows: list[LectureClickStatsRow] = []
        for row in result.all():
            stream_clicks = int(row[3])
            materials_clicks = int(row[4])
            registration_clicks = int(row[5])
            rows.append(
                LectureClickStatsRow(
                    lecture_id=row[0],
                    lecture_number=row[1],
                    lecture_title=row[2],
                    stream_link_clicks=stream_clicks,
                    materials_lecture_clicks=materials_clicks,
                    registration_clicks=registration_clicks,
                    total_clicks=stream_clicks + materials_clicks + registration_clicks,
                )
            )
        return rows

    async def get_click_summary(self) -> tuple[list[ClickSummaryItemRow], ClickSummaryTotalsRow]:
        now = utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        stmt = (
            select(
                ClickEvent.event_type,
                func.count(ClickEvent.id).label("all_time_count"),
                func.sum(case((ClickEvent.created_at >= today_start, 1), else_=0)).label("today_count"),
                func.sum(case((ClickEvent.created_at >= week_start, 1), else_=0)).label("week_count"),
            )
            .group_by(ClickEvent.event_type)
            .order_by(ClickEvent.event_type.asc())
        )
        result = await self.session.execute(stmt)
        by_type: dict[ClickEventType, ClickSummaryItemRow] = {}
        for row in result.all():
            by_type[row[0]] = ClickSummaryItemRow(
                event_type=row[0],
                today_count=int(row[2] or 0),
                week_count=int(row[3] or 0),
                all_time_count=int(row[1] or 0),
            )

        items = [
            by_type.get(
                event_type,
                ClickSummaryItemRow(
                    event_type=event_type,
                    today_count=0,
                    week_count=0,
                    all_time_count=0,
                ),
            )
            for event_type in ClickEventType
        ]
        totals = ClickSummaryTotalsRow(
            today_count=sum(item.today_count for item in items),
            week_count=sum(item.week_count for item in items),
            all_time_count=sum(item.all_time_count for item in items),
        )
        return items, totals

    async def get_click_timeseries(self, days: int = 7) -> list[ClickTimeseriesPointRow]:
        safe_days = max(1, days)
        since = utcnow() - timedelta(days=safe_days - 1)
        date_bucket = func.date(ClickEvent.created_at)
        stmt = (
            select(
                date_bucket,
                ClickEvent.event_type,
                func.count(ClickEvent.id),
            )
            .where(ClickEvent.created_at >= since)
            .group_by(date_bucket, ClickEvent.event_type)
            .order_by(date_bucket.asc(), ClickEvent.event_type.asc())
        )
        result = await self.session.execute(stmt)
        return [
            ClickTimeseriesPointRow(
                bucket_date=str(row[0]),
                event_type=row[1],
                clicks_count=int(row[2]),
            )
            for row in result.all()
        ]

    async def get_top_click_users(
        self,
        *,
        event_type: ClickEventType | None = None,
        limit: int = 10,
    ) -> list[ClickTopUserRow]:
        safe_limit = max(1, limit)
        count_expr = func.count(ClickEvent.id)
        stmt = (
            select(
                User.tg_user_id,
                User.username,
                User.full_name,
                count_expr.label("clicks_count"),
            )
            .join(ClickEvent, ClickEvent.user_id == User.tg_user_id)
            .group_by(User.tg_user_id, User.username, User.full_name)
            .order_by(count_expr.desc(), User.tg_user_id.asc())
            .limit(safe_limit)
        )
        if event_type is not None:
            stmt = stmt.where(ClickEvent.event_type == event_type)

        result = await self.session.execute(stmt)
        return [
            ClickTopUserRow(
                tg_user_id=int(row[0]),
                username=row[1],
                full_name=row[2],
                clicks_count=int(row[3]),
            )
            for row in result.all()
        ]

    async def get_lecture_funnel(self, lecture_id: int) -> LectureFunnelRow:
        registration_clicks = await self.session.execute(
            select(func.count(ClickEvent.id)).where(
                ClickEvent.lecture_id == lecture_id,
                ClickEvent.event_type == ClickEventType.REGISTRATION_CLICK,
            )
        )
        registrations = await self.session.execute(
            select(func.count(Registration.id)).where(Registration.lecture_id == lecture_id)
        )
        stream_link_unique = await self.session.execute(
            select(func.count(distinct(ClickEvent.user_id))).where(
                ClickEvent.lecture_id == lecture_id,
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
            )
        )
        materials_lecture_unique = await self.session.execute(
            select(func.count(distinct(ClickEvent.user_id))).where(
                ClickEvent.lecture_id == lecture_id,
                ClickEvent.event_type == ClickEventType.MATERIALS_LECTURE,
            )
        )
        return LectureFunnelRow(
            lecture_id=lecture_id,
            registration_clicks=int(registration_clicks.scalar() or 0),
            registrations=int(registrations.scalar() or 0),
            stream_link_unique=int(stream_link_unique.scalar() or 0),
            materials_lecture_unique=int(materials_lecture_unique.scalar() or 0),
        )

    async def get_lecture_clicks_by_hour(self, lecture_id: int) -> list[LectureHourBucketRow]:
        stmt = (
            select(ClickEvent.created_at, ClickEvent.event_type)
            .where(ClickEvent.lecture_id == lecture_id)
            .order_by(ClickEvent.created_at.asc())
        )
        result = await self.session.execute(stmt)
        grouped: dict[tuple[datetime, ClickEventType], int] = {}
        for created_at, event_type in result.all():
            bucket = created_at.replace(minute=0, second=0, microsecond=0)
            key = (bucket, event_type)
            grouped[key] = grouped.get(key, 0) + 1

        sorted_keys = sorted(grouped.keys(), key=lambda item: (item[0], item[1].value))
        return [
            LectureHourBucketRow(
                bucket_start=bucket_start,
                event_type=event_type,
                clicks_count=grouped[(bucket_start, event_type)],
            )
            for bucket_start, event_type in sorted_keys
        ]

    async def get_course_overview(self, days: int) -> CourseOverviewRow:
        now = utcnow()
        since = None if days == 0 else now - timedelta(days=max(1, days) - 1)

        lectures_total_q = await self.session.execute(select(func.count(Lecture.id)))
        lectures_open_q = await self.session.execute(
            select(func.count(Lecture.id)).where(Lecture.registration_open.is_(True))
        )
        lectures_past_q = await self.session.execute(
            select(func.count(Lecture.id)).where(Lecture.scheduled_at <= now)
        )
        registrations_total_q = await self.session.execute(select(func.count(Registration.id)))
        unique_students_q = await self.session.execute(select(func.count(distinct(Registration.user_id))))
        pending_questions_q = await self.session.execute(
            select(func.count(Question.id)).where(Question.status == QuestionStatus.PENDING)
        )

        period_clicks_stmt = select(func.count(ClickEvent.id))
        if since is not None:
            period_clicks_stmt = period_clicks_stmt.where(ClickEvent.created_at >= since)
        period_clicks_q = await self.session.execute(period_clicks_stmt)

        stream_unique_rows = await self.session.execute(
            select(ClickEvent.user_id, ClickEvent.lecture_id)
            .where(
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
                ClickEvent.lecture_id.is_not(None),
            )
            .distinct()
        )
        stream_unique_total = len(stream_unique_rows.all())

        lectures_total = int(lectures_total_q.scalar() or 0)
        registrations_total = int(registrations_total_q.scalar() or 0)
        avg_registrations_per_lecture = (
            float(registrations_total) / float(lectures_total) if lectures_total > 0 else 0.0
        )
        attendance_rate = (
            (float(stream_unique_total) / float(registrations_total)) * 100.0
            if registrations_total > 0
            else 0.0
        )

        return CourseOverviewRow(
            lectures_total=lectures_total,
            lectures_open=int(lectures_open_q.scalar() or 0),
            lectures_past=int(lectures_past_q.scalar() or 0),
            registrations_total=registrations_total,
            unique_students=int(unique_students_q.scalar() or 0),
            avg_registrations_per_lecture=round(avg_registrations_per_lecture, 2),
            attendance_rate=round(attendance_rate, 2),
            questions_pending_total=int(pending_questions_q.scalar() or 0),
            period_clicks_total=int(period_clicks_q.scalar() or 0),
        )

    async def get_course_overview_lectures(self, days: int) -> list[LectureOverviewRow]:
        now = utcnow()
        since = None if days == 0 else now - timedelta(days=max(1, days) - 1)

        registrations_agg = (
            select(
                Registration.lecture_id.label("lecture_id"),
                func.count(Registration.id).label("registrations"),
            )
            .group_by(Registration.lecture_id)
            .subquery()
        )
        stream_unique_agg = (
            select(
                ClickEvent.lecture_id.label("lecture_id"),
                func.count(distinct(ClickEvent.user_id)).label("stream_unique"),
            )
            .where(
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.lecture_id)
            .subquery()
        )
        materials_unique_agg = (
            select(
                ClickEvent.lecture_id.label("lecture_id"),
                func.count(distinct(ClickEvent.user_id)).label("materials_unique"),
            )
            .where(
                ClickEvent.event_type == ClickEventType.MATERIALS_LECTURE,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.lecture_id)
            .subquery()
        )

        sparkline_stmt = (
            select(
                ClickEvent.lecture_id,
                func.date(ClickEvent.created_at).label("bucket_date"),
                func.count(ClickEvent.id).label("clicks_count"),
            )
            .where(ClickEvent.lecture_id.is_not(None))
            .group_by(ClickEvent.lecture_id, func.date(ClickEvent.created_at))
            .order_by(func.date(ClickEvent.created_at).asc())
        )
        if since is not None:
            sparkline_stmt = sparkline_stmt.where(ClickEvent.created_at >= since)
        sparkline_result = await self.session.execute(sparkline_stmt)
        sparkline_by_lecture: dict[int, list[LectureOverviewSparklinePointRow]] = {}
        for lecture_id, bucket_date, clicks_count in sparkline_result.all():
            if lecture_id is None:
                continue
            sparkline_by_lecture.setdefault(int(lecture_id), []).append(
                LectureOverviewSparklinePointRow(
                    date=str(bucket_date),
                    count=int(clicks_count or 0),
                )
            )

        overview_stmt = (
            select(
                Lecture.id,
                Lecture.number,
                Lecture.title,
                Lecture.scheduled_at,
                Lecture.registration_open,
                func.coalesce(registrations_agg.c.registrations, 0),
                func.coalesce(stream_unique_agg.c.stream_unique, 0),
                func.coalesce(materials_unique_agg.c.materials_unique, 0),
            )
            .outerjoin(registrations_agg, registrations_agg.c.lecture_id == Lecture.id)
            .outerjoin(stream_unique_agg, stream_unique_agg.c.lecture_id == Lecture.id)
            .outerjoin(materials_unique_agg, materials_unique_agg.c.lecture_id == Lecture.id)
            .order_by(Lecture.number.asc())
        )
        overview_result = await self.session.execute(overview_stmt)

        rows: list[LectureOverviewRow] = []
        for row in overview_result.all():
            lecture_id = int(row[0])
            scheduled_at = row[3]
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            registrations = int(row[5] or 0)
            stream_unique = int(row[6] or 0)
            materials_unique = int(row[7] or 0)
            status = "past" if scheduled_at <= now else ("open" if bool(row[4]) else "closed_upcoming")
            attendance_rate = ((float(stream_unique) / float(registrations)) * 100.0) if registrations > 0 else 0.0
            rows.append(
                LectureOverviewRow(
                    lecture_id=lecture_id,
                    lecture_number=int(row[1]),
                    lecture_title=row[2],
                    scheduled_at=scheduled_at,
                    registration_open=bool(row[4]),
                    status=status,
                    registrations=registrations,
                    stream_link_unique=stream_unique,
                    materials_lecture_unique=materials_unique,
                    attendance_rate=round(attendance_rate, 2),
                    sparkline=sparkline_by_lecture.get(lecture_id, []),
                )
            )
        return rows

    async def get_export_rows(self) -> list[ExportRow]:
        clicks_agg = (
            select(
                ClickEvent.user_id.label("user_id"),
                ClickEvent.lecture_id.label("lecture_id"),
                func.count(ClickEvent.id).label("clicks_count"),
                func.min(ClickEvent.created_at).label("first_click_at"),
                func.max(ClickEvent.created_at).label("last_click_at"),
            )
            .where(
                ClickEvent.event_type == ClickEventType.STREAM_LINK,
                ClickEvent.lecture_id.is_not(None),
            )
            .group_by(ClickEvent.user_id, ClickEvent.lecture_id)
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
