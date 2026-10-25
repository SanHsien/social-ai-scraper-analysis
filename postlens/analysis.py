"""互動分數、主題分類、開頭類型與分組統計。"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median

from .models import METRICS, Post

DEFAULT_WEIGHTS = {"likes": 1.0, "replies": 1.5, "reposts": 2.0, "quotes": 2.0}
UNCATEGORIZED = "未分類"
OTHER_HOOK = "其他"
MIN_SAMPLE = 5  # 分組少於這個數字，報表會標「樣本太少」


@dataclass
class Rules:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    topics: dict[str, list[re.Pattern]] = field(default_factory=dict)
    hooks: dict[str, list[re.Pattern]] = field(default_factory=dict)


def _compile(name: str, spec: dict) -> list[re.Pattern]:
    if not isinstance(spec, dict):
        raise ValueError(f"rule {name!r} must be an object with 'keywords' and/or 'patterns'")
    keywords = spec.get("keywords", [])
    patterns = spec.get("patterns", [])
    for label, value in (("keywords", keywords), ("patterns", patterns)):
        if not isinstance(value, list):  # 字串會被逐字拆開，變成每個字都是一條規則
            raise ValueError(f"rule {name!r}: '{label}' must be a list of strings")
    pats = [re.compile(re.escape(str(k)), re.IGNORECASE) for k in keywords]
    for p in patterns:
        try:
            pats.append(re.compile(p, re.IGNORECASE | re.MULTILINE))
        except re.error as exc:
            raise ValueError(f"rule {name!r} has an invalid pattern {p!r}: {exc}") from None
    if not pats:
        raise ValueError(f"rule {name!r} has no keywords or patterns")
    return pats


def load_rules(path: Path | None) -> Rules:
    if path is None:
        return Rules()
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("rules file must be a JSON object with 'weights', 'topics' and/or 'hooks'")
    for section in ("weights", "topics", "hooks"):
        if not isinstance(raw.get(section, {}), dict):
            raise ValueError(f"rules '{section}' must be an object")
    weights = dict(DEFAULT_WEIGHTS)
    for k, v in raw.get("weights", {}).items():
        if k not in METRICS:
            raise ValueError(f"unknown weight {k!r}; expected one of {', '.join(METRICS)}")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise ValueError(f"weight {k!r} must be a non-negative number")
        weights[k] = float(v)
    return Rules(
        weights=weights,
        topics={n: _compile(n, s) for n, s in raw.get("topics", {}).items()},
        hooks={n: _compile(n, s) for n, s in raw.get("hooks", {}).items()},
    )


def score(post: Post, weights: dict[str, float]) -> float:
    return sum(weights.get(m, 0.0) * getattr(post, m) for m in METRICS)


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def classify(post: Post, rules: Rules) -> None:
    post.topics = [n for n, pats in rules.topics.items() if any(p.search(post.text) for p in pats)] \
        or [UNCATEGORIZED]
    head = first_line(post.text)
    post.hook = next((n for n, pats in rules.hooks.items() if any(p.search(head) for p in pats)), OTHER_HOOK)


def percentile_ranks(values: list[float]) -> list[float]:
    """每個值在整體中的百分位（0–100，平手取平均名次）。"""
    n = len(values)
    if n == 1:
        return [100.0]
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2
        for k in range(i, j + 1):
            ranks[order[k]] = round(100.0 * avg / (n - 1), 1)
        i = j + 1
    return ranks


def filter_posts(posts: list[Post], since: datetime | None, until: datetime | None,
                 include_reposts: bool, platforms: set[str] | None = None) -> list[Post]:
    out = []
    for p in posts:
        if p.is_repost and not include_reposts:
            continue
        if since and p.created_at < since:
            continue
        if until and p.created_at >= until:
            continue
        if platforms is not None and p.platform not in platforms:
            continue
        out.append(p)
    return out


def analyze(posts: list[Post], rules: Rules) -> list[Post]:
    for p in posts:
        p.score = score(p, rules.weights)
        p.engagement_rate = (p.interactions / p.views) if p.views else None
        classify(p, rules)
    for p, r in zip(posts, percentile_ranks([p.score for p in posts]) if posts else []):
        p.percentile = r
    return posts


@dataclass
class GroupStats:
    name: str
    count: int
    share: float
    median_score: float
    mean_score: float
    median_rate: float | None
    top_decile: int  # 落在全體前 10% 的篇數
    best: Post

    @property
    def small_sample(self) -> bool:
        return self.count < MIN_SAMPLE


def group_stats(posts: list[Post], key) -> list[GroupStats]:
    groups: dict[str, list[Post]] = {}
    for p in posts:
        names = key(p)
        for name in names if isinstance(names, list) else [names]:
            groups.setdefault(name, []).append(p)
    total = len(posts)
    stats = []
    for name, items in groups.items():
        rates = [p.engagement_rate for p in items if p.engagement_rate is not None]
        scores = [p.score for p in items]
        stats.append(GroupStats(
            name=name,
            count=len(items),
            share=len(items) / total if total else 0.0,
            median_score=median(scores),
            mean_score=mean(scores),
            median_rate=median(rates) if rates else None,
            top_decile=sum(p.percentile >= 90 for p in items),
            best=max(items, key=lambda p: (p.score, p.created_at)),
        ))
    stats.sort(key=lambda s: (s.small_sample, -s.median_score, s.name))
    return stats


WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


def parse_offset(value: str) -> timezone:
    m = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", value.strip())
    if not m:
        raise ValueError(f"UTC offset must look like +08:00, got {value!r}")
    sign = 1 if m.group(1) == "+" else -1
    return timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))


def weekday_key(tz: timezone):
    return lambda p: f"週{WEEKDAYS[p.created_at.astimezone(tz).weekday()]}"


def hour_key(tz: timezone):
    def key(p: Post) -> str:
        h = p.created_at.astimezone(tz).hour
        start = h - h % 3
        return f"{start:02d}–{start + 3:02d} 時"
    return key
