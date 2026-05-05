from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base


class LectureFormat(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"


class ClickEventType(StrEnum):
    STREAM_LINK = "stream_link"
    MATERIALS_GENERAL = "materials_general"
    MATERIALS_LECTURE = "materials_lecture"
    REGISTRATION_CLICK = "registration_click"


class QuestionStatus(StrEnum):
    PENDING = "pending"
    IGNORED = "ignored"
    ANSWERED = "answered"


class User(Base):
    __tablename__ = "users"

    tg_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    registrations: Mapped[list["Registration"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    link_clicks: Mapped[list["LinkClick"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    click_events: Mapped[list["ClickEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    questions: Mapped[list["Question"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Lecture(Base):
    __tablename__ = "lectures"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    format: Mapped[LectureFormat] = mapped_column(
        Enum(
            LectureFormat,
            name="lecture_format",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    stream_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    materials_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    registration_open: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    registrations: Mapped[list["Registration"]] = relationship(back_populates="lecture", cascade="all, delete-orphan")
    link_clicks: Mapped[list["LinkClick"]] = relationship(back_populates="lecture", cascade="all, delete-orphan")
    click_events: Mapped[list["ClickEvent"]] = relationship(back_populates="lecture", cascade="all, delete-orphan")


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("user_id", "lecture_id", name="uq_user_lecture_registration"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.tg_user_id", ondelete="CASCADE"), nullable=False)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="registrations")
    lecture: Mapped[Lecture] = relationship(back_populates="registrations")


class LinkClick(Base):
    __tablename__ = "link_clicks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.tg_user_id", ondelete="CASCADE"), nullable=False)
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="link_clicks")
    lecture: Mapped[Lecture] = relationship(back_populates="link_clicks")


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.tg_user_id", ondelete="CASCADE"), nullable=False)
    lecture_id: Mapped[int | None] = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=True)
    event_type: Mapped[ClickEventType] = mapped_column(
        Enum(
            ClickEventType,
            name="click_event_type",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="click_events")
    lecture: Mapped[Lecture | None] = relationship(back_populates="click_events")


class ClickEventSetting(Base):
    __tablename__ = "click_event_settings"

    event_type: Mapped[ClickEventType] = mapped_column(
        Enum(
            ClickEventType,
            name="click_event_type",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.tg_user_id", ondelete="CASCADE"), nullable=False)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[QuestionStatus] = mapped_column(
        Enum(
            QuestionStatus,
            name="question_status",
            native_enum=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=QuestionStatus.PENDING,
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    answered_by_admin_username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="questions")
