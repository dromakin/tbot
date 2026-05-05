from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from bot.web.auth import InitDataError, verify_init_data


BOT_TOKEN = "test_bot_token"


def build_init_data(
    *,
    user_id: int,
    username: str | None,
    auth_date: int,
    tamper_hash: bool = False,
    include_user: bool = True,
) -> str:
    payload: dict[str, str] = {
        "query_id": "AAEAAAE",
        "auth_date": str(auth_date),
    }
    if include_user:
        payload["user"] = json.dumps(
            {
                "id": user_id,
                "username": username,
                "first_name": "Test",
                "last_name": "User",
            },
            separators=(",", ":"),
        )

    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(payload.items(), key=lambda x: x[0]))
    digest = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if tamper_hash:
        digest = "0" * len(digest)

    return urlencode({**payload, "hash": digest})


def test_verify_init_data_valid() -> None:
    raw = build_init_data(user_id=123, username="admin", auth_date=int(time.time()))
    user = verify_init_data(raw=raw, bot_token=BOT_TOKEN, max_age_sec=86400)

    assert user.tg_user_id == 123
    assert user.username == "admin"
    assert user.full_name == "Test User"


def test_verify_init_data_invalid_hash() -> None:
    raw = build_init_data(user_id=123, username="admin", auth_date=int(time.time()), tamper_hash=True)

    with pytest.raises(InitDataError, match="Invalid initData signature"):
        verify_init_data(raw=raw, bot_token=BOT_TOKEN, max_age_sec=86400)


def test_verify_init_data_expired() -> None:
    raw = build_init_data(user_id=123, username="admin", auth_date=int(time.time()) - 1000)

    with pytest.raises(InitDataError, match="initData expired"):
        verify_init_data(raw=raw, bot_token=BOT_TOKEN, max_age_sec=60)


def test_verify_init_data_missing_user() -> None:
    raw = build_init_data(user_id=123, username="admin", auth_date=int(time.time()), include_user=False)

    with pytest.raises(InitDataError, match="Missing user"):
        verify_init_data(raw=raw, bot_token=BOT_TOKEN, max_age_sec=86400)
