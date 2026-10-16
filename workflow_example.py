#!/usr/bin/env python3
"""
AI 社群貼文自動抓取與爆款主題分析工作流 (Social AI Scraper & Analysis Pipeline)
完整實作：整合 Scrapling (防反爬/自適應)、Agent Reach (跨平台免API) 與 ScrapeGraphAI (語意抽取)
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

from scrapers.scrapling_scraper import ScraplingSocialScraper
from scrapers.agent_reach_scraper import AgentReachScraper
from scrapers.scrapegraph_analyzer import ScrapeGraphExtractor
from analyzer import ViralPostAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SocialAIScraper")

def parse_args():
    parser = argparse.ArgumentParser(description="AI 社群爆款貼文自動抓取與主題分析工具")
    parser.add_argument("--targets", default="targets.example.json", help="目標帳號清單 JSON 檔路徑")
    parser.add_argument("--engine", choices=["scrapling", "agent-reach", "scrapegraph", "auto"], default="auto",
                        help="指定爬蟲抓取引擎 (scrapling / agent-reach / scrapegraph / auto)")
    parser.add_argument("--max-posts", type=int, default=5, help="每個目標帳號抓取的最大貼文數")
    parser.add_argument("--headless", action="store_true", default=True, help="無頭瀏覽器模式")
    parser.add_argument("--proxy", default=None, help="Proxy 代理伺服器位置 (例如 http://127.0.0.1:7890)")
    parser.add_argument("--output-json", default="results.json", help="分析結果輸出 JSON 路徑")
    parser.add_argument("--output-csv", default="viral_insights.csv", help="爆款主題輸出 CSV 路徑")
    parser.add_argument("--llm-model", default="ollama/llama3.2", help="ScrapeGraphAI 使用的 LLM 模型")
    return parser.parse_args()

def load_targets(filepath: str) -> List[str]:
    if not os.path.exists(filepath):
        logger.error(f"找不到目標帳號檔案: {filepath}")
        return ["karpathy", "levelsio", "OpenAI", "sama", "hwchase17"]
    with open(filepath, "r", encoding="utf-8") as f:
        targets = json.load(f)
    if isinstance(targets, list):
        return targets
    elif isinstance(targets, dict) and "targets" in targets:
        return targets["targets"]
    return []

def main():
    args = parse_args()
    print("=" * 65)
    print("🚀 AI 社群貼文自動抓取與爆款主題分析工作流啟動")
    print("=" * 65)

    targets = load_targets(args.targets)
    print(f"[*] 載入目標帳號清單 ({len(targets)} 個): {', '.join(targets[:5])}{'...' if len(targets) > 5 else ''}")
    print(f"[*] 抓取引擎配置: {args.engine} | 每個帳號限制: {args.max_posts} 篇")
    print(f"[*] 防反爬機制: Scrapling StealthFetcher 指紋偽裝 / 自適應定位器啟動")

    # 初始化各組件
    scrapling_scraper = ScraplingSocialScraper(headless=args.headless, proxy=args.proxy)
    agent_reach_scraper = AgentReachScraper()
    scrapegraph_extractor = ScrapeGraphExtractor(llm_model=args.llm_model)
    post_analyzer = ViralPostAnalyzer()

    all_posts: List[Dict[str, Any]] = []

    # 執行爬取
    for username in targets:
        logger.info(f"==> 正在抓取目標帳號: @{username}")
        posts = []
        if args.engine in ["scrapling", "auto"]:
            posts = scrapling_scraper.fetch_user_posts(username, max_posts=args.max_posts)

        if not posts and args.engine in ["agent-reach", "auto"]:
            logger.info("切換為 Agent Reach 跨平台介面抓取...")
            posts = agent_reach_scraper.fetch_tweets(username, count=args.max_posts)

        if not posts and args.engine == "scrapegraph":
            logger.info("調用 ScrapeGraphAI 宣告式語意爬蟲...")
            prompt = f"請提取 @{username} 最近的公開貼文內容、讚數、轉推數與回覆數"
            res = scrapegraph_extractor.extract_from_url_or_html(f"https://x.com/{username}", prompt)
            posts = res.get("posts", [])

        all_posts.extend(posts)
        logger.info(f"    成功獲取 @{username} 的 {len(posts)} 則貼文")

    print(f"\n[+] 總計抓取取得 {len(all_posts)} 則社群貼文。開始進行爆款計算與主題語意歸納...")

    # 篩選前 20% 爆款貼文
    top_posts = post_analyzer.rank_and_filter(all_posts, top_ratio=0.3, min_count=2)

    # 針對爆款貼文進行維度剖析
    analyzed_results = []
    for p in top_posts:
        analysis = post_analyzer.analyze_post_content(p)
        analyzed_results.append(analysis)

    # 匯出結構化成果
    post_analyzer.export_results(analyzed_results, args.output_json, args.output_csv)

    # 終端機摘要呈現
    print("\n" + "=" * 65)
    print("🏆 爆款主題分析結果精選 (Top Viral Insights)")
    print("=" * 65)
    for idx, item in enumerate(analyzed_results[:3], 1):
        print(f"\n【Top {idx}】作者: @{item.get('author')} | 互動權重分: {item.get('engagement_score')}")
        print(f"📊 數據: 👍 {item.get('likes')} | 🔁 {item.get('retweets')} | 💬 {item.get('replies')}")
        print(f"🏷️  領域分類: {item.get('topic_category')}")
        print(f"🪝 開頭鉤子: {item.get('hook_style')}")
        print(f"💡 爆款因素: {', '.join(item.get('viral_factors', []))}")
        print(f"📝 仿寫指南:\n   {item.get('imitation_guide')}")
        print("-" * 65)

    print(f"\n🎉 完整資料已存檔:")
    print(f"   - JSON 檔案: {os.path.abspath(args.output_json)}")
    print(f"   - CSV 檔案 : {os.path.abspath(args.output_csv)}")
    print("=" * 65)

if __name__ == "__main__":
    main()
