from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bot.db.models import ClickEventType, LectureFormat, QuestionStatus


class MeOut(BaseModel):
    tg_user_id: int
    username: str | None
    full_name: str
    is_admin: bool


class LectureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    title: str
    description: str | None
    topics: str | None
    scheduled_at: datetime
    format: LectureFormat
    stream_url: str | None
    materials_url: str | None
    registration_open: bool


class LectureCreateIn(BaseModel):
    number: int
    title: str
    description: str = ""
    topics: str | None = None
    scheduled_at: datetime
    format: LectureFormat
    stream_url: str | None = None
    materials_url: str | None = None
    registration_open: bool = False


class LectureRegistrationFlagIn(BaseModel):
    open: bool = Field(description="Open registration if true")


class LectureMaterialsIn(BaseModel):
    materials_url: str | None = None


class LectureStreamIn(BaseModel):
    stream_url: str | None = None


class LectureTopicsIn(BaseModel):
    topics: str | None = None


class GeneralMaterialsSettingOut(BaseModel):
    url: str | None


class GeneralMaterialsSettingIn(BaseModel):
    url: str | None = None


class StatsRowOut(BaseModel):
    lecture_id: int
    lecture_number: int
    lecture_title: str
    registrations_count: int
    unique_clicks_count: int
    total_clicks_count: int


class RegistrationRowOut(BaseModel):
    tg_user_id: int
    username: str | None
    username_at: str
    full_name: str
    registered_at: datetime
    clicks_count: int


class ClickTypeSettingOut(BaseModel):
    event_type: ClickEventType
    enabled: bool


class ClickTypeSettingPatchIn(BaseModel):
    enabled: bool


class ClickTypeStatsOut(BaseModel):
    event_type: ClickEventType
    total_clicks: int
    unique_users: int


class LectureClickStatsOut(BaseModel):
    lecture_id: int
    lecture_number: int
    lecture_title: str
    stream_link_clicks: int
    materials_lecture_clicks: int
    registration_clicks: int
    total_clicks: int


class ClickSummaryItemOut(BaseModel):
    event_type: ClickEventType
    today: int
    week: int
    all_time: int


class ClickSummaryTotalsOut(BaseModel):
    today: int
    week: int
    all_time: int


class ClickSummaryOut(BaseModel):
    items: list[ClickSummaryItemOut]
    totals: ClickSummaryTotalsOut


class ClickTimeseriesPointOut(BaseModel):
    date: str
    event_type: ClickEventType
    count: int


class ClickTopUserOut(BaseModel):
    tg_user_id: int
    username: str | None
    username_at: str
    full_name: str
    clicks_count: int


class LectureFunnelOut(BaseModel):
    lecture_id: int
    registration_clicks: int
    registrations: int
    stream_link_unique: int
    materials_lecture_unique: int


class LectureHourBucketOut(BaseModel):
    bucket_start: datetime
    event_type: ClickEventType
    count: int


class CourseOverviewOut(BaseModel):
    lectures_total: int
    lectures_open: int
    lectures_past: int
    registrations_total: int
    unique_students: int
    avg_registrations_per_lecture: float
    attendance_rate: float
    questions_pending_total: int
    period_clicks_total: int


class LectureOverviewSparklinePointOut(BaseModel):
    date: str
    count: int


class LectureOverviewRowOut(BaseModel):
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
    sparkline: list[LectureOverviewSparklinePointOut]


class QuestionOut(BaseModel):
    id: int
    tg_user_id: int
    username: str | None
    username_at: str
    full_name: str
    text: str
    status: QuestionStatus
    answer_text: str | None
    answered_at: datetime | None
    answered_by_admin_id: int | None
    answered_by_admin_username: str | None
    created_at: datetime
    updated_at: datetime


class QuestionModerationIn(BaseModel):
    status: Literal["ignored", "answered"]
    answer_text: str | None = None


class UserLectureOut(BaseModel):
    lecture_id: int
    lecture_number: int
    lecture_title: str
    description: str | None
    scheduled_at: datetime
    format: LectureFormat
    registration_open: bool
    is_registered: bool
    has_materials: bool
    has_stream: bool


class UserMaterialsLectureOut(BaseModel):
    lecture_id: int
    lecture_number: int
    lecture_title: str
    scheduled_at: datetime
    has_materials: bool


class UserRegistrationOut(BaseModel):
    lecture_id: int
    lecture_number: int
    lecture_title: str
    scheduled_at: datetime
    registered_at: datetime


class UserActionOut(BaseModel):
    status: Literal["ok", "already_registered", "closed", "not_found", "offline", "pending", "not_registered"]
    message: str
    url: str | None = None


class ProgramLectureOut(BaseModel):
    number: int
    title: str
    topics: list[str]


class UserStaticOut(BaseModel):
    program_header: str
    program_lectures: list[ProgramLectureOut]
    contact_text: str
