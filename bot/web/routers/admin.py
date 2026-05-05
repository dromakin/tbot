from __future__ import annotations

from dataclasses import asdict

from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from bot.db.repository import Repository
from bot.services.export import build_export_zip, build_stats_csv
from bot.db.models import ClickEventType, QuestionStatus
from bot.text_store import t
from bot.web.auth import VerifiedTmaUser
from bot.web.deps import get_bot, get_repo, require_admin
from bot.web.schemas import (
    CourseOverviewOut,
    ClickSummaryItemOut,
    ClickSummaryOut,
    ClickSummaryTotalsOut,
    ClickTypeSettingOut,
    ClickTypeSettingPatchIn,
    ClickTimeseriesPointOut,
    ClickTopUserOut,
    ClickTypeStatsOut,
    LectureCreateIn,
    LectureClickStatsOut,
    LectureFunnelOut,
    LectureHourBucketOut,
    LectureOverviewRowOut,
    LectureOverviewSparklinePointOut,
    LectureMaterialsIn,
    LectureOut,
    LectureRegistrationFlagIn,
    QuestionModerationIn,
    QuestionOut,
    RegistrationRowOut,
    StatsRowOut,
)

router = APIRouter(prefix="/api", tags=["admin"])


def _lecture_to_out(lecture) -> LectureOut:
    return LectureOut.model_validate(lecture)


def _question_to_out(question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        tg_user_id=question.user_id,
        username=question.username,
        username_at=f"@{question.username}" if question.username else "",
        full_name=question.full_name,
        text=question.text,
        status=question.status,
        answer_text=question.answer_text,
        answered_at=question.answered_at,
        answered_by_admin_id=question.answered_by_admin_id,
        answered_by_admin_username=question.answered_by_admin_username,
        created_at=question.created_at,
        updated_at=question.updated_at,
    )


@router.get("/stats", response_model=list[StatsRowOut])
async def get_stats(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[StatsRowOut]:
    rows = await repo.get_stats()
    return [StatsRowOut(**asdict(row)) for row in rows]


@router.get("/course-overview", response_model=CourseOverviewOut)
async def get_course_overview(
    days: int = Query(default=7, ge=0, le=365),
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> CourseOverviewOut:
    row = await repo.get_course_overview(days=days)
    return CourseOverviewOut(
        lectures_total=row.lectures_total,
        lectures_open=row.lectures_open,
        lectures_past=row.lectures_past,
        registrations_total=row.registrations_total,
        unique_students=row.unique_students,
        avg_registrations_per_lecture=row.avg_registrations_per_lecture,
        attendance_rate=row.attendance_rate,
        questions_pending_total=row.questions_pending_total,
        period_clicks_total=row.period_clicks_total,
    )


@router.get("/course-overview/lectures", response_model=list[LectureOverviewRowOut])
async def get_course_overview_lectures(
    days: int = Query(default=7, ge=0, le=365),
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[LectureOverviewRowOut]:
    rows = await repo.get_course_overview_lectures(days=days)
    return [
        LectureOverviewRowOut(
            lecture_id=row.lecture_id,
            lecture_number=row.lecture_number,
            lecture_title=row.lecture_title,
            scheduled_at=row.scheduled_at,
            registration_open=row.registration_open,
            status=row.status,
            registrations=row.registrations,
            stream_link_unique=row.stream_link_unique,
            materials_lecture_unique=row.materials_lecture_unique,
            attendance_rate=row.attendance_rate,
            sparkline=[
                LectureOverviewSparklinePointOut(date=point.date, count=point.count)
                for point in row.sparkline
            ],
        )
        for row in rows
    ]


@router.get("/click-stats/summary", response_model=ClickSummaryOut)
async def get_click_summary(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> ClickSummaryOut:
    items, totals = await repo.get_click_summary()
    return ClickSummaryOut(
        items=[
            ClickSummaryItemOut(
                event_type=item.event_type,
                today=item.today_count,
                week=item.week_count,
                all_time=item.all_time_count,
            )
            for item in items
        ],
        totals=ClickSummaryTotalsOut(
            today=totals.today_count,
            week=totals.week_count,
            all_time=totals.all_time_count,
        ),
    )


@router.get("/click-types", response_model=list[ClickTypeSettingOut])
async def get_click_types(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[ClickTypeSettingOut]:
    rows = await repo.list_click_type_settings()
    return [
        ClickTypeSettingOut(
            event_type=row.event_type,
            enabled=row.enabled,
        )
        for row in rows
    ]


@router.patch("/click-types/{event_type}", response_model=ClickTypeSettingOut)
async def set_click_type_state(
    event_type: ClickEventType,
    payload: ClickTypeSettingPatchIn,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> ClickTypeSettingOut:
    row = await repo.set_click_type_enabled(event_type=event_type, enabled=payload.enabled)
    return ClickTypeSettingOut(event_type=row.event_type, enabled=row.enabled)


@router.get("/click-stats/types", response_model=list[ClickTypeStatsOut])
async def get_click_type_stats(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[ClickTypeStatsOut]:
    rows = await repo.get_click_type_stats()
    return [
        ClickTypeStatsOut(
            event_type=row.event_type,
            total_clicks=row.total_clicks,
            unique_users=row.unique_users,
        )
        for row in rows
    ]


@router.get("/click-stats/timeseries", response_model=list[ClickTimeseriesPointOut])
async def get_click_timeseries(
    days: int = Query(default=7, ge=1, le=60),
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[ClickTimeseriesPointOut]:
    rows = await repo.get_click_timeseries(days=days)
    return [
        ClickTimeseriesPointOut(
            date=row.bucket_date,
            event_type=row.event_type,
            count=row.clicks_count,
        )
        for row in rows
    ]


@router.get("/click-stats/lectures", response_model=list[LectureClickStatsOut])
async def get_lecture_click_stats(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[LectureClickStatsOut]:
    rows = await repo.get_lecture_click_stats()
    return [
        LectureClickStatsOut(
            lecture_id=row.lecture_id,
            lecture_number=row.lecture_number,
            lecture_title=row.lecture_title,
            stream_link_clicks=row.stream_link_clicks,
            materials_lecture_clicks=row.materials_lecture_clicks,
            registration_clicks=row.registration_clicks,
            total_clicks=row.total_clicks,
        )
        for row in rows
    ]


@router.get("/click-stats/top-users", response_model=list[ClickTopUserOut])
async def get_top_click_users(
    event_type: ClickEventType | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[ClickTopUserOut]:
    rows = await repo.get_top_click_users(event_type=event_type, limit=limit)
    return [
        ClickTopUserOut(
            tg_user_id=row.tg_user_id,
            username=row.username,
            username_at=f"@{row.username}" if row.username else "",
            full_name=row.full_name,
            clicks_count=row.clicks_count,
        )
        for row in rows
    ]


@router.get("/click-stats/funnel", response_model=LectureFunnelOut)
async def get_lecture_funnel(
    lecture_id: int,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> LectureFunnelOut:
    lecture = await repo.get_lecture(lecture_id)
    if lecture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    row = await repo.get_lecture_funnel(lecture_id=lecture_id)
    return LectureFunnelOut(
        lecture_id=row.lecture_id,
        registration_clicks=row.registration_clicks,
        registrations=row.registrations,
        stream_link_unique=row.stream_link_unique,
        materials_lecture_unique=row.materials_lecture_unique,
    )


@router.get("/click-stats/lecture/{lecture_id}/by-hour", response_model=list[LectureHourBucketOut])
async def get_lecture_clicks_by_hour(
    lecture_id: int,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[LectureHourBucketOut]:
    lecture = await repo.get_lecture(lecture_id)
    if lecture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    rows = await repo.get_lecture_clicks_by_hour(lecture_id=lecture_id)
    return [
        LectureHourBucketOut(
            bucket_start=row.bucket_start,
            event_type=row.event_type,
            count=row.clicks_count,
        )
        for row in rows
    ]


@router.get("/lectures", response_model=list[LectureOut])
async def get_lectures(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[LectureOut]:
    lectures = await repo.list_lectures()
    return [_lecture_to_out(lecture) for lecture in lectures]


@router.post("/lectures", response_model=LectureOut, status_code=status.HTTP_201_CREATED)
async def create_lecture(
    payload: LectureCreateIn,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> LectureOut:
    lecture = await repo.create_lecture(
        number=payload.number,
        title=payload.title,
        description=payload.description,
        scheduled_at=payload.scheduled_at,
        lecture_format=payload.format,
        stream_url=payload.stream_url,
        materials_url=payload.materials_url,
        registration_open=payload.registration_open,
    )
    return _lecture_to_out(lecture)


@router.patch("/lectures/{lecture_id}/registration", response_model=LectureOut)
async def set_registration_state(
    lecture_id: int,
    payload: LectureRegistrationFlagIn,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> LectureOut:
    ok = await repo.set_registration_open(lecture_id, payload.open)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    lecture = await repo.get_lecture(lecture_id)
    if lecture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    return _lecture_to_out(lecture)


@router.patch("/lectures/{lecture_id}/materials", response_model=LectureOut)
async def set_materials_url(
    lecture_id: int,
    payload: LectureMaterialsIn,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> LectureOut:
    ok = await repo.set_materials_url(lecture_id, payload.materials_url)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    lecture = await repo.get_lecture(lecture_id)
    if lecture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")
    return _lecture_to_out(lecture)


@router.get("/lectures/{lecture_id}/registrations", response_model=list[RegistrationRowOut])
async def get_lecture_registrations(
    lecture_id: int,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[RegistrationRowOut]:
    rows = await repo.list_lecture_registration_rows(lecture_id)
    return [
        RegistrationRowOut(
            tg_user_id=row.tg_user_id,
            username=row.username,
            username_at=f"@{row.username}" if row.username else "",
            full_name=row.full_name,
            registered_at=row.registered_at,
            clicks_count=row.clicks_count,
        )
        for row in rows
    ]


@router.get("/questions", response_model=list[QuestionOut])
async def get_questions(
    question_status: QuestionStatus | None = None,
    limit: int = 100,
    offset: int = 0,
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> list[QuestionOut]:
    rows = await repo.list_questions(status=question_status, limit=limit, offset=offset)
    return [_question_to_out(row) for row in rows]


@router.patch("/questions/{question_id}", response_model=QuestionOut)
async def moderate_question(
    question_id: int,
    payload: QuestionModerationIn,
    current_admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
    bot: Bot = Depends(get_bot),
) -> QuestionOut:
    if payload.status == "ignored":
        question = await repo.set_question_ignored(question_id)
    else:
        answer_text = (payload.answer_text or "").strip()
        if not answer_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="answer_text is required when status=answered",
            )
        question = await repo.answer_question(
            question_id=question_id,
            answer_text=answer_text,
            admin_id=current_admin.tg_user_id,
            admin_username=current_admin.username,
        )
        if question is not None:
            try:
                await bot.send_message(
                    question.user_id,
                    t("qa", "web_answer", answer_text=answer_text),
                )
            except Exception as exc:  # pragma: no cover - network dependent
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to deliver answer to user: {exc}",
                ) from exc

    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return _question_to_out(question)


@router.get("/export.csv")
async def export_csv(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> Response:
    rows = await repo.get_export_rows()
    csv_bytes = build_stats_csv(rows)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="stats.csv"'},
    )


@router.get("/export.zip")
async def export_zip(
    _admin: VerifiedTmaUser = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> Response:
    registrations = await repo.get_export_rows()
    click_events = await repo.iter_click_events_raw()
    clicks_per_lecture = await repo.get_lecture_click_stats()
    clicks_per_user = await repo.get_clicks_per_user()
    attendance_lectures, attendance_rows = await repo.get_attendance_matrix()
    users = await repo.list_users()

    funnel_per_lecture = []
    for lecture_row in clicks_per_lecture:
        funnel_row = await repo.get_lecture_funnel(lecture_row.lecture_id)
        funnel_per_lecture.append((lecture_row, funnel_row))

    zip_bytes = build_export_zip(
        registrations=registrations,
        click_events=click_events,
        clicks_per_lecture=clicks_per_lecture,
        clicks_per_user=clicks_per_user,
        attendance_lectures=attendance_lectures,
        attendance_rows=attendance_rows,
        funnel_per_lecture=funnel_per_lecture,
        users=users,
    )
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="stats_bundle.zip"'},
    )
