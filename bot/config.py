from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    db_dsn: str = Field(alias="DB_DSN")
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")
    org_contact_text: str = Field(alias="ORG_CONTACT_TEXT")
    general_materials_url: str = Field(alias="GENERAL_MATERIALS_URL")
    remind_before_min: int = Field(default=60, alias="REMIND_BEFORE_MIN")
    tz: str = Field(default="Europe/Moscow", alias="TZ")

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
