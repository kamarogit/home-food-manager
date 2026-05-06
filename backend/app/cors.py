"""
CORS は環境変数のみで調整する（フロントと API が別ホストのときは CORS_ORIGINS にフロントの URL を列挙）。

- CORS_ORIGINS: カンマまたは改行区切り（例: https://app.example.com,http://localhost:5173）
- CORS_ORIGIN_REGEX: 未設定時はローカル／LAN 向けの既定正規表現を使う。
  空文字を明示的に設定した場合は正規表現マッチを使わない（許可は CORS_ORIGINS のみ）。
"""

from __future__ import annotations

import os
import re

# ローカル開発向け: プライベート IP からのアクセスを許可（本番の別ホスト運用では無効化推奨）
_DEFAULT_ORIGIN_REGEX = (
    r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$"
)

_DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def parse_cors_origins(raw: str | None) -> list[str]:
    if raw is None or not raw.strip():
        return []
    out: list[str] = []
    for chunk in raw.split(","):
        for line in chunk.splitlines():
            t = line.strip()
            if t:
                out.append(t)
    return out


def resolve_cors_settings() -> tuple[list[str], str | None]:
    origins = parse_cors_origins(os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS))

    if "CORS_ORIGIN_REGEX" not in os.environ:
        return origins, _DEFAULT_ORIGIN_REGEX

    regex_raw = os.environ["CORS_ORIGIN_REGEX"].strip()
    if not regex_raw:
        return origins, None

    try:
        re.compile(regex_raw)
    except re.error as e:
        msg = f"CORS_ORIGIN_REGEX が不正な正規表現です: {e}"
        raise ValueError(msg) from e

    return origins, regex_raw
