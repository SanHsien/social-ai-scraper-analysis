"""讀取使用者自己匯出或透過官方 API 取得的貼文資料。

支援：
- 通用 CSV／JSON（欄位名稱有別名，見 FIELD_ALIASES）
- X（Twitter）帳號封存檔裡的 `data/tweets.js`
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from .models import Post

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "id": ("id", "id_str", "post_id", "media_id"),
    "created_at": ("created_at", "timestamp", "date", "time", "published_at", "posted_at"),
    "text": ("text", "full_text", "content", "message", "caption", "body"),
    "likes": ("likes", "like_count", "favorite_count", "favorites", "reactions"),
    "replies": ("replies", "reply_count", "comments", "comment_count"),
    "reposts": ("reposts", "repost_count", "retweets", "retweet_count", "shares", "share_count"),
    "quotes": ("quotes", "quote_count"),
    "views": ("views", "view_count", "impressions", "impression_count"),
    "url": ("url", "permalink", "link"),
}

X_ARCHIVE_PREFIX = re.compile(r"^\s*window\.YTD\.[A-Za-z0-9_]+\.part\d+\s*=\s*")


class DataError(ValueError):
    """輸入資料格式不對。訊息會指出檔案與列號。"""


def parse_datetime(value: str) -> datetime:
    """ISO 8601、Unix 秒數或 X 封存檔格式（`Wed Oct 10 20:19:24 +0000 2018`）。沒有時區視為 UTC。"""
    value = str(value).strip()
    if re.fullmatch(r"\d{9,11}(\.\d+)?", value):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    value_iso = value.replace("Z", "+00:00")
    # Graph／Threads API 的 `+0000` 時區；Python 3.10 的 fromisoformat 只認 `+00:00`
    value_iso = re.sub(r"^(\d{4}-\d{2}-\d{2}[T ][\d:.]+)([+-]\d{2})(\d{2})$", r"\1\2:\3", value_iso)
    try:
        dt = datetime.fromisoformat(value_iso)
    except ValueError:
        try:
            dt = datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            try:
                dt = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                raise ValueError(f"unrecognized date: {value!r}") from None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _pick(row: dict, field: str):
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for alias in FIELD_ALIASES[field]:
        if alias in lowered and lowered[alias] not in (None, ""):
            return lowered[alias]
    return None


def _to_int(value, field: str) -> int | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    try:
        number = int(float(text))
    except (ValueError, OverflowError):
        raise ValueError(f"{field} is not a number: {value!r}") from None
    if number < 0:
        raise ValueError(f"{field} is negative: {value!r}")
    return number


def post_from_row(row: dict, where: str) -> Post:
    try:
        created = _pick(row, "created_at")
        if created is None:
            raise ValueError("missing created_at/timestamp/date column")
        text = _pick(row, "text") or ""
        post_id = _pick(row, "id")
        counts = {f: _to_int(_pick(row, f), f) for f in ("likes", "replies", "reposts", "quotes", "views")}
    except ValueError as exc:
        raise DataError(f"{where}: {exc}") from None
    try:
        created_at = parse_datetime(created)
    except ValueError as exc:
        raise DataError(f"{where}: {exc}") from None
    return Post(
        id=str(post_id) if post_id is not None else where,
        created_at=created_at,
        text=str(text),
        likes=counts["likes"] or 0,
        replies=counts["replies"] or 0,
        reposts=counts["reposts"] or 0,
        quotes=counts["quotes"] or 0,
        views=counts["views"],
        url=str(_pick(row, "url") or ""),
    )


def load_csv(path: Path) -> list[Post]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise DataError(f"{path}: empty CSV")
        return [post_from_row(row, f"{path.name}:{i}") for i, row in enumerate(reader, start=2)]


def load_json(path: Path) -> list[Post]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        data = data["data"]  # 官方 API 常見的 {"data": [...]} 包裝
    if not isinstance(data, list):
        raise DataError(f"{path}: expected a JSON list of posts or {{\"data\": [...]}}")
    return [post_from_row(row, f"{path.name}[{i}]") for i, row in enumerate(data)]


def load_x_archive(path: Path) -> list[Post]:
    """X 帳號封存檔（設定 → 下載資料封存）裡的 `data/tweets.js`。封存檔沒有回覆數與曝光數。"""
    raw = path.read_text(encoding="utf-8-sig")
    match = X_ARCHIVE_PREFIX.match(raw)
    if not match:
        raise DataError(f"{path}: not an X archive tweets.js (missing 'window.YTD.tweets.part0 =' prefix)")
    entries = json.loads(raw[match.end():])
    posts = []
    for i, entry in enumerate(entries):
        tweet = entry.get("tweet", entry) if isinstance(entry, dict) else None
        if not isinstance(tweet, dict):
            raise DataError(f"{path.name}[{i}]: unexpected entry")
        post = post_from_row(
            {
                "id": tweet.get("id_str") or tweet.get("id"),
                "created_at": tweet.get("created_at"),
                "full_text": tweet.get("full_text") or tweet.get("text", ""),
                "favorite_count": tweet.get("favorite_count"),
                "retweet_count": tweet.get("retweet_count"),
            },
            f"{path.name}[{i}]",
        )
        post.is_repost = post.text.startswith("RT @")
        posts.append(post)
    return posts


def load(path: Path, fmt: str = "auto") -> list[Post]:
    path = Path(path)
    if not path.is_file():
        raise DataError(f"input file not found: {path}")
    if fmt == "auto":
        suffix = path.suffix.lower()
        if suffix == ".csv":
            fmt = "csv"
        elif suffix == ".js":
            fmt = "x-archive"
        elif suffix == ".json":
            fmt = "json"
        else:
            raise DataError(f"{path}: cannot guess format from extension; pass --format")
    loader = {"csv": load_csv, "json": load_json, "x-archive": load_x_archive}.get(fmt)
    if loader is None:
        raise DataError(f"unknown format {fmt!r}")
    try:
        return loader(path)
    except json.JSONDecodeError as exc:
        raise DataError(f"{path}: invalid JSON: {exc}") from None
    except UnicodeDecodeError:
        raise DataError(f"{path}: not UTF-8; re-save the file as UTF-8 and try again") from None
