from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    db_dsn: str = Field(validation_alias=AliasChoices("DATABASE_URL", "DB_DSN"))
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    remind_before_min: int = Field(default=60, alias="REMIND_BEFORE_MIN")
    tz: str = Field(default="Europe/Moscow", alias="TZ")

    web_enabled: bool = Field(default=True, alias="WEB_ENABLED")
    web_host: str = Field(default="0.0.0.0", alias="WEB_HOST")
    web_port: int = Field(default=8080, validation_alias=AliasChoices("PORT", "WEB_PORT"))
    web_public_url: str = Field(default="", alias="WEB_PUBLIC_URL")
    web_init_data_max_age_sec: int = Field(default=86400, alias="WEB_INIT_DATA_MAX_AGE_SEC")
    web_dev_auth_bypass: bool = Field(default=False, alias="WEB_DEV_AUTH_BYPASS")
    web_dev_user_id: int = Field(default=0, alias="WEB_DEV_USER_ID")
    web_dev_user_username: str = Field(default="", alias="WEB_DEV_USER_USERNAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def admin_ids(self) -> list[int]:
        raw_value = (self.admin_ids_raw or "").strip()
        if not raw_value:
            return []
        return [int(part.strip()) for part in raw_value.split(",") if part.strip()]

    @field_validator("db_dsn", mode="before")
    @classmethod
    def normalize_db_dsn(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        raw_value = value.strip()
        if raw_value.startswith("postgres://"):
            return "postgresql+asyncpg://" + raw_value[len("postgres://") :]
        if raw_value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + raw_value[len("postgresql://") :]
        return raw_value

    @field_validator("web_dev_user_id", mode="before")
    @classmethod
    def parse_web_dev_user_id(cls, value: object) -> int | object:
        if value is None:
            return 0
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return 0
            return int(raw_value)
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
