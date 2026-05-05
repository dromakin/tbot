from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from time import time
from urllib.parse import urlencode

from bot.config import get_settings


def _build_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def _build_data_check_string(payload: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in sorted(payload.items(), key=lambda item: item[0]))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate signed Telegram Mini App initData")
    parser.add_argument("--user-id", type=int, default=None, help="Telegram user id for the generated payload")
    parser.add_argument("--username", default=None, help="Telegram username without @")
    parser.add_argument("--first-name", default="Dev", help="User first name in the payload")
    parser.add_argument("--last-name", default="", help="User last name in the payload")
    parser.add_argument("--query-id", default="AAEAAAE", help="query_id value used in payload")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    settings = get_settings()

    user_id = args.user_id or settings.web_dev_user_id
    if not user_id:
        raise SystemExit("Missing user id. Pass --user-id or set WEB_DEV_USER_ID in .env")

    username = args.username
    if username is None:
        username = settings.web_dev_user_username.strip() or None

    user_payload: dict[str, object] = {
        "id": user_id,
        "first_name": args.first_name,
        "last_name": args.last_name,
    }
    if username:
        user_payload["username"] = username

    payload = {
        "auth_date": str(int(time())),
        "query_id": args.query_id,
        "user": json.dumps(user_payload, separators=(",", ":"), ensure_ascii=False),
    }

    secret_key = _build_secret_key(settings.bot_token)
    data_check_string = _build_data_check_string(payload)
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    print(urlencode(payload))


if __name__ == "__main__":
    main()
