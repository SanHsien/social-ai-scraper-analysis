"""產生 examples/sample_posts.csv：完全虛構的示範資料，不對應任何真實帳號或貼文。

固定亂數種子，重跑會得到同一份檔案。
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

TEMPLATES = [
    ("Claude 和 ChatGPT 實測：同一個 bug 誰先修好？", 3.0),
    ("5 個我每天都在用的自動化流程", 2.6),
    ("別再手動整理會議紀錄了，這個模板直接套", 2.2),
    ("用 Python 把每週報表自動寄出", 1.6),
    ("我覺得 AI 工具最大的成本不是訂閱費", 1.3),
    ("git worktree 讓我同時開三個任務", 1.4),
    ("今天的咖啡很好喝", 0.4),
    ("整理了一份免費的提示詞懶人包", 2.8),
    ("部署前一定要跑的 3 個測試", 1.8),
    ("你會讓 AI 直接改正式環境嗎？", 2.0),
    ("Cursor 新版評測：值得升級嗎？", 2.4),
    ("週末去爬山", 0.5),
]


def main() -> None:
    rng = random.Random(20261016)
    start = datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(36):
        text, strength = TEMPLATES[i % len(TEMPLATES)]
        created = start + timedelta(days=i * 0.8, hours=rng.randint(0, 14))
        views = int(rng.randint(800, 2500) * strength)
        likes = int(views * rng.uniform(0.02, 0.06))
        rows.append({
            "id": f"demo-{i + 1:03d}",
            "timestamp": created.isoformat().replace("+00:00", "Z"),
            "text": text,
            "likes": likes,
            "replies": int(likes * rng.uniform(0.05, 0.3)),
            "reposts": int(likes * rng.uniform(0.02, 0.15)),
            "quotes": int(likes * rng.uniform(0.0, 0.05)),
            "views": views,
        })
    out = Path(__file__).with_name("sample_posts.csv")
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
