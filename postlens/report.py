"""輸出：Markdown 報表、逐篇 CSV、摘要 JSON。"""
from __future__ import annotations

import csv
import json
from datetime import timezone
from pathlib import Path

from .analysis import MIN_SAMPLE, GroupStats, Rules, group_stats, hour_key, weekday_key
from .models import Post


def _short(text: str, n: int = 50) -> str:
    one = " ".join(text.split())
    return (one[: n - 1] + "…") if len(one) > n else one


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _offset(dt) -> str:
    raw = dt.strftime("%z")  # +0800；`%:z` 要 Python 3.12 才有
    return f"{raw[:3]}:{raw[3:5]}"


def _rate(v: float | None) -> str:
    return "—" if v is None else f"{v:.2%}"


def _table(title: str, stats: list[GroupStats], with_best: bool) -> list[str]:
    head = "| 分組 | 篇數 | 占比 | 分數中位數 | 分數平均 | 互動率中位數 | 前 10% 篇數 |"
    sep = "|---|---:|---:|---:|---:|---:|---:|"
    if with_best:
        head += " 最高分貼文 |"
        sep += "---|"
    lines = [f"## {title}", "", head, sep]
    for s in stats:
        name = _cell(s.name) + ("（樣本太少）" if s.small_sample else "")
        row = (f"| {name} | {s.count} | {s.share:.0%} | {s.median_score:.1f} | {s.mean_score:.1f} | "
               f"{_rate(s.median_rate)} | {s.top_decile} |")
        if with_best:
            row += f" {_cell(_short(s.best.text, 36))} |"
        lines.append(row)
    return lines + [""]


def markdown(posts: list[Post], rules: Rules, tz: timezone, excluded_reposts: int, source: str) -> str:
    if not posts:
        return "# 貼文表現報表\n\n沒有符合條件的貼文。\n"
    start = min(p.created_at for p in posts).astimezone(tz)
    end = max(p.created_at for p in posts).astimezone(tz)
    has_views = any(p.views is not None for p in posts)
    weights = "、".join(f"{k}×{v:g}" for k, v in rules.weights.items())
    lines = [
        "# 貼文表現報表",
        "",
        f"- 資料來源：`{source}`",
        f"- 期間：{start:%Y-%m-%d} 至 {end:%Y-%m-%d}（UTC{_offset(start)}）",
        f"- 篇數：{len(posts)}" + (f"（另排除轉發 {excluded_reposts} 篇）" if excluded_reposts else ""),
        f"- 互動分數 = {weights}",
        "- 互動率 = （按讚＋回覆＋轉發＋引用）÷ 曝光" + ("" if has_views else "；本資料沒有曝光數，互動率欄位為「—」"),
        "",
    ]
    if any(p.platform for p in posts):
        lines += _table("依平台", group_stats(posts, lambda p: p.platform or "未標示"), with_best=True)
    lines += _table("依主題", group_stats(posts, lambda p: p.topics), with_best=True)
    lines.append("> 一篇貼文可以同時屬於多個主題，所以占比加總可能超過 100%。")
    lines.append("")
    lines += _table("依開頭類型", group_stats(posts, lambda p: p.hook), with_best=True)
    lines += _table("依星期", group_stats(posts, weekday_key(tz)), with_best=False)
    lines += _table("依發文時段", group_stats(posts, hour_key(tz)), with_best=False)

    top = sorted(posts, key=lambda p: (-p.score, p.created_at))[:10]
    lines += ["## 分數最高的 10 篇", "", "| 日期 | 分數 | 互動率 | 主題 | 開頭類型 | 內容 |",
              "|---|---:|---:|---|---|---|"]
    for p in top:
        text = _cell(_short(p.text))
        if p.url:
            text = f"[{text}]({p.url})"
        lines.append(f"| {p.created_at.astimezone(tz):%Y-%m-%d} | {p.score:.1f} | {_rate(p.engagement_rate)} | "
                     f"{_cell('、'.join(p.topics))} | {_cell(p.hook)} | {text} |")
    lines += [
        "",
        "## 解讀限制",
        "",
        f"- 篇數少於 {MIN_SAMPLE} 的分組標為「樣本太少」並排在最後，不要拿來下結論。",
        "- 分數受粉絲數成長、演算法調整、單篇被大帳號轉發等因素影響；這份報表只呈現相關，不代表因果。",
        "- 主題與開頭類型是關鍵字規則判斷，不是語意理解；先抽查「未分類」與「其他」的貼文，再調整規則檔。",
        "",
    ]
    return "\n".join(lines)


CSV_FIELDS = ["id", "created_at", "platform", "score", "percentile", "engagement_rate", "likes", "replies",
              "reposts", "quotes", "views", "topics", "hook", "url", "text"]


def write_csv(posts: list[Post], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_FIELDS)
        for p in sorted(posts, key=lambda p: (-p.score, p.created_at)):
            w.writerow([p.id, p.created_at.isoformat(), p.platform, f"{p.score:g}", p.percentile,
                        "" if p.engagement_rate is None else f"{p.engagement_rate:.6f}",
                        p.likes, p.replies, p.reposts, p.quotes, "" if p.views is None else p.views,
                        ";".join(p.topics), p.hook, p.url, p.text])


def summary(posts: list[Post], rules: Rules) -> dict:
    def dump(stats: list[GroupStats]) -> list[dict]:
        return [{"name": s.name, "count": s.count, "median_score": round(s.median_score, 3),
                 "mean_score": round(s.mean_score, 3),
                 "median_engagement_rate": None if s.median_rate is None else round(s.median_rate, 6),
                 "top_decile": s.top_decile, "small_sample": s.small_sample} for s in stats]
    return {
        "posts": len(posts),
        "weights": rules.weights,
        "topics": dump(group_stats(posts, lambda p: p.topics)) if posts else [],
        "hooks": dump(group_stats(posts, lambda p: p.hook)) if posts else [],
        "platforms": (dump(group_stats(posts, lambda p: p.platform or "未標示"))
                      if posts and any(p.platform for p in posts) else []),
    }


def write_all(posts: list[Post], rules: Rules, tz: timezone, excluded: int, source: str, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = [out / "report.md", out / "posts_scored.csv", out / "summary.json"]
    paths[0].write_text(markdown(posts, rules, tz, excluded, source), encoding="utf-8", newline="\n")
    write_csv(posts, paths[1])
    paths[2].write_text(json.dumps(summary(posts, rules), ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    return paths
