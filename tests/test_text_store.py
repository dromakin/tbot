from __future__ import annotations

import pytest

from bot.text_store import t


def test_text_store_loads_block_and_key() -> None:
    text = t("start", "menu_text")
    assert "Выберите" in text


def test_text_store_renders_placeholders() -> None:
    text = t(
        "registration",
        "success",
        lecture_number=3,
        lecture_title="Безопасность API",
    )
    assert "Лекция №3: Безопасность API" in text


def test_text_store_raises_for_missing_key() -> None:
    with pytest.raises(KeyError):
        t("start", "missing.key")
