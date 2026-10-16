"""資料模型：一篇貼文與它的互動數字。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

METRICS = ("likes", "replies", "reposts", "quotes")


@dataclass
class Post:
    id: str
    created_at: datetime  # 一律帶時區（aware）
    text: str
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    quotes: int = 0
    views: int | None = None  # 平台沒提供就是 None，不要當成 0
    url: str = ""
    is_repost: bool = False  # 轉發別人的貼文，預設不納入分析
    # 以下由分析步驟填入
    score: float = 0.0
    engagement_rate: float | None = None
    percentile: float = 0.0
    topics: list[str] = field(default_factory=list)
    hook: str = ""

    @property
    def interactions(self) -> int:
        return self.likes + self.replies + self.reposts + self.quotes
