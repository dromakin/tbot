from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from time import time
from urllib.parse import parse_qsl


class InitDataError(ValueError):
    """Raised when Telegram initData is invalid."""


@dataclass(slots=True)
class VerifiedTmaUser:
    tg_user_id: int
    username: str | None
    full_name: str
    auth_date: int


def _build_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def _build_data_check_string(items: list[tuple[str, str]]) -> str:
    return "\n".join(f"{key}={value}" for key, value in sorted(items, key=lambda x: x[0]))


def verify_init_data(raw: str, bot_token: str, max_age_sec: int) -> VerifiedTmaUser:
    if not raw:
        raise InitDataError("Missing initData")

    pairs = parse_qsl(raw, keep_blank_values=True)
    if not pairs:
        raise InitDataError("Malformed initData")

    data = dict(pairs)
    received_hash = data.get("hash")
    if not received_hash:
        raise InitDataError("Missing hash in initData")

    check_items = [(k, v) for k, v in pairs if k != "hash"]
    data_check_string = _build_data_check_string(check_items)
    secret_key = _build_secret_key(bot_token)
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise InitDataError("Invalid initData signature")

    auth_date_raw = data.get("auth_date")
    if not auth_date_raw or not auth_date_raw.isdigit():
        raise InitDataError("Invalid auth_date")

    auth_date = int(auth_date_raw)
    now = int(time())
    if auth_date > now + 30:
        raise InitDataError("auth_date is in the future")
    if now - auth_date > max_age_sec:
        raise InitDataError("initData expired")

    user_raw = data.get("user")
    if not user_raw:
        raise InitDataError("Missing user in initData")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise InitDataError("Invalid user payload") from exc

    user_id = user.get("id")
    if not isinstance(user_id, int):
        raise InitDataError("Invalid user id in initData")

    username = user.get("username")
    if username is not None and not isinstance(username, str):
        username = None

    first_name = user.get("first_name") if isinstance(user.get("first_name"), str) else ""
    last_name = user.get("last_name") if isinstance(user.get("last_name"), str) else ""
    full_name = (f"{first_name} {last_name}").strip() or f"user_{user_id}"

    return VerifiedTmaUser(
        tg_user_id=user_id,
        username=username,
        full_name=full_name,
        auth_date=auth_date,
    )
