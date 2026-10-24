"""命令列入口：python -m postlens analyze <檔案> [選項]"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from .analysis import analyze, filter_posts, load_rules, parse_offset
from .loaders import DataError, load, parse_datetime
from .report import write_all


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="postlens",
        description="Analyze your own exported social posts: engagement score, topics, report.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("analyze", help="score, classify and write a report")
    a.add_argument("input", help="CSV, JSON, or X archive data/tweets.js")
    a.add_argument("--format", default="auto", choices=["auto", "csv", "json", "x-archive"])
    a.add_argument("--rules", help="rules JSON (weights, topics, hooks); see rules.example.json")
    a.add_argument("--out", default="out", help="output directory (default: out)")
    a.add_argument("--utc-offset", default="+08:00", help="time zone for weekday/hour grouping")
    a.add_argument("--since", help="only posts at or after this date (ISO 8601)")
    a.add_argument("--until", help="only posts before this date (ISO 8601)")
    a.add_argument("--include-reposts", action="store_true", help="keep reposts of other people's posts")
    a.add_argument("--platform", help="only these platforms, comma-separated (e.g. x,threads); matches the platform column")
    args = parser.parse_args(argv)

    try:
        tz = parse_offset(args.utc_offset)
        since = _date(args.since, tz)
        until = _date(args.until, tz)
        rules = load_rules(Path(args.rules) if args.rules else None)
        posts = load(Path(args.input), args.format)
    except (DataError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    platforms = {p.strip().lower() for p in args.platform.split(",") if p.strip()} if args.platform else None
    kept = filter_posts(posts, since, until, args.include_reposts, platforms)
    excluded = 0 if args.include_reposts else sum(p.is_repost for p in posts)
    analyze(kept, rules)
    paths = write_all(kept, rules, tz, excluded, Path(args.input).name, Path(args.out))
    print(f"analyzed {len(kept)} of {len(posts)} posts")
    for p in paths:
        print(f"wrote {p}")
    return 0 if kept else 1


def _date(value: str | None, tz) -> datetime | None:
    if not value:
        return None
    dt = parse_datetime(value)
    # 只給日期（沒有時間）時，以使用者指定的時區解讀
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        dt = dt.replace(tzinfo=tz)
    return dt


if __name__ == "__main__":
    sys.exit(main())
