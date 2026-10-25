#!/usr/bin/env python3
"""
AI 全社群貼文自動抓取與爆款主題分析工作流 (Multi-Platform Social AI Scraper & Analysis Pipeline)
支援平台：X (Twitter)、Threads、Instagram、Facebook、YouTube、Reddit
支援模式：
  1. 指定帳號監控 (Account Mode)
  2. 全網熱門議題/關鍵字廣泛探索 (Trending / Discovery Mode)
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Any

# 確保在 Windows 預設 CP950/繁體環境下輸出 UTF-8 不發生編碼錯誤
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from scrapers.multi_platform_scraper import MultiPlatformScraper, Platform
from analyzer import ViralPostAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MultiPlatformScraper")

ALL_PLATFORMS = ["x", "threads", "instagram", "facebook", "youtube", "reddit"]

def parse_args():
    parser = argparse.ArgumentParser(description="跨主流社群平台 AI 爆款自動抓取與主題分析工具")
    parser.add_argument("--mode", choices=["accounts", "trending"], default="accounts",
                        help="執行模式：accounts (指定帳號監控) 或 trending (熱門議題廣泛探索)")
    parser.add_argument("--platforms", default="x,threads,youtube,reddit",
                        help=f"指定要抓取的平台（逗號分隔，可選: {','.join(ALL_PLATFORMS)} 或 all）")
    parser.add_argument("--query", default=None,
                        help="熱門探索模式使用的關鍵字（如：'AI 工具'、'一人創業'）")
    parser.add_argument("--targets", default="targets.example.json",
                        help="目標帳號清單 JSON 檔路徑")
    parser.add_argument("--max-posts", type=int, default=3,
                        help="每個平台/目標抓取的貼文數量")
    parser.add_argument("--max-targets", type=int, default=None,
                        help="每個平台爬取的目標帳號上限 (預設全數爬取)")
    parser.add_argument("--run-postlens", action="store_true", default=False,
                        help="分析完成後自動調用 postlens 產出 Markdown 統計報表")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True,
                        help="無頭瀏覽器模式（預設開啟；用 --no-headless 顯示瀏覽器視窗）")
    parser.add_argument("--proxy", default=None,
                        help="Proxy 代理伺服器位置 (例如 http://127.0.0.1:7890)")
    parser.add_argument("--output-json", default="results.json",
                        help="分析結果輸出 JSON 路徑")
    parser.add_argument("--output-csv", default="viral_insights.csv",
                        help="爆款主題輸出 CSV 路徑")
    return parser.parse_args()

def resolve_platforms(platform_arg: str) -> List[Platform]:
    if platform_arg.strip().lower() == "all":
        return [Platform.from_str(p) for p in ALL_PLATFORMS]
    selected = []
    for item in platform_arg.split(","):
        item_clean = item.strip().lower()
        if item_clean:
            try:
                selected.append(Platform.from_str(item_clean))
            except ValueError:
                logger.warning(f"略過未知平台: {item_clean}")
    return selected or [Platform.X, Platform.THREADS]

def load_targets_config(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        logger.warning(f"找不到設定檔 {filepath}，使用預設配置。")
        return {
            "platforms": {
                "x": ["karpathy", "levelsio", "sama"],
                "threads": ["aistart_up", "zuck"],
                "youtube": ["@Fireship"],
                "reddit": ["r/artificial"]
            },
            "trending_queries": ["AI 工具", "一人創業"]
        }
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"platforms": {"x": data}, "trending_queries": ["AI 工具", "一人創業"]}
    return data

def main():
    args = parse_args()
    target_platforms = resolve_platforms(args.platforms)
    platform_names = [p.value for p in target_platforms]

    print("=" * 70)
    print("🚀 AI 全社群貼文自動抓取與跨平台爆款主題分析工作流啟動")
    print("=" * 70)
    print(f"[*] 執行模式: {'【特定帳號監控】' if args.mode == 'accounts' else '【熱門議題廣泛探索】'}")
    print(f"[*] 目標平台: {', '.join(platform_names).upper()}")
    print(f"[*] 反爬防護: Scrapling StealthFetcher 指紋偽裝 / 自適應定位器啟動")

    config = load_targets_config(args.targets)
    scraper = MultiPlatformScraper(headless=args.headless, proxy=args.proxy)
    analyzer = ViralPostAnalyzer()

    all_posts: List[Dict[str, Any]] = []

    if args.mode == "accounts":
        platform_accounts_map = config.get("platforms", {})
        for p in target_platforms:
            accounts = platform_accounts_map.get(p.value, [])
            if not accounts and p.value == "x" and "targets" in config:
                accounts = config["targets"]
            if not accounts:
                accounts = ["sample_user"]

            target_accounts = accounts[:args.max_targets] if args.max_targets else accounts
            for acc in target_accounts:
                posts = scraper.fetch_account_posts(p, acc, max_posts=args.max_posts)
                all_posts.extend(posts)
    else:
        # Trending / Discovery Mode
        query = args.query
        if not query:
            queries = config.get("trending_queries", ["AI 工具與自動化工作流"])
            query = queries[0] if queries else "AI 工具"

        print(f"[*] 探索主題關鍵字: 「{query}」")
        for p in target_platforms:
            posts = scraper.search_trending_posts(p, query, max_posts=args.max_posts)
            all_posts.extend(posts)

    print(f"\n[+] 跨平台總計蒐集 {len(all_posts)} 則社群貼文。開始進行加權計分與爆款歸納...")

    # 爆款排序與維度萃取
    top_posts = analyzer.rank_and_filter(all_posts, top_ratio=0.3, min_count=2)
    analyzed_results = []
    for p in top_posts:
        analysis = analyzer.analyze_post_content(p)
        analyzed_results.append(analysis)

    # 匯出結果
    analyzer.export_results(analyzed_results, args.output_json, args.output_csv)

    # 成果終端機展示
    print("\n" + "=" * 70)
    print("🏆 跨平台爆款主題與仿寫策略精選 (Cross-Platform Viral Insights)")
    print("=" * 70)
    for idx, item in enumerate(analyzed_results[:4], 1):
        plat = str(item.get("platform", "x")).upper()
        author = item.get("author") or item.get("target", "unknown")
        print(f"\n【Top {idx}】平台: [{plat}] | 作者/來源: @{author} | 互動分: {item.get('engagement_score')}")
        metrics_str = f"👍 {item.get('likes')} | 🔁 {item.get('retweets')} | 💬 {item.get('replies')}"
        if item.get("views"):
            metrics_str += f" | 👁️ {item.get('views')}"
        print(f"📊 數據: {metrics_str}")
        print(f"🏷️  領域分類: {item.get('topic_category')}")
        print(f"🪝 開頭鉤子: {item.get('hook_style')}")
        print(f"💡 爆款因素: {', '.join(item.get('viral_factors', []))}")
        print(f"📝 仿寫指南:\n   {item.get('imitation_guide')}")
        print("-" * 70)

    print(f"\n🎉 成果已存檔:")
    print(f"   - JSON 檔案: {os.path.abspath(args.output_json)}")
    print(f"   - CSV 檔案 : {os.path.abspath(args.output_csv)}")
    print("=" * 70)

    if args.run_postlens:
        print("\n[*] 正在透過 postlens 分析引擎生成統計報表...")
        try:
            from postlens.cli import main as postlens_main
            code = postlens_main(["analyze", args.output_csv, "--out", "out"])
            if code == 0:
                print(f"[+] postlens 報表已生成於: {os.path.abspath('out/report.md')}")
            else:
                logger.warning(f"postlens 報表生成失敗（結束碼 {code}），請看上方錯誤訊息")
        except Exception as e:
            logger.warning(f"執行 postlens 報表生成發生異常: {e}")

if __name__ == "__main__":
    main()
