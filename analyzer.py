"""
社群爆款貼文主題分析與內容洞察核心模組 (Social Viral Post Analyzer)
支援跨平台 (X, Threads, Instagram, Facebook, YouTube, Reddit) 互動指標權重計分與主題維度剖析
"""

import json
import csv
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ViralPostAnalyzer:
    """
    負責跨平台貼文互動分數計算、爆款排序篩選、主題分類與仿寫策略產出
    """

    def __init__(self, weight_like: float = 1.0, weight_repost: float = 2.5, weight_reply: float = 1.5):
        self.w_like = weight_like
        self.w_repost = weight_repost
        self.w_reply = weight_reply

    def calculate_score(self, post: Dict[str, Any]) -> float:
        platform = str(post.get("platform", "x")).lower()
        likes = float(post.get("likes", post.get("upvotes", 0)))
        reposts = float(post.get("retweets", post.get("reposts", post.get("shares", 0))))
        replies = float(post.get("replies", post.get("comments", 0)))
        views = float(post.get("views", 0))

        # 針對不同社群平台特性之加權計分模型
        if platform == "youtube":
            # YouTube：著重觀看量 (以千次計) + 讚數 + 留言討論度
            score = likes * 1.0 + replies * 2.5 + (views / 1000.0) * 1.5
        elif platform == "reddit":
            # Reddit：Upvotes 與深度留言討論為核心
            score = likes * 1.0 + replies * 2.0
        elif platform in ["facebook", "fb"]:
            # Facebook：分享 (Share) 權重最高，其次留言
            score = likes * 1.0 + reposts * 3.0 + replies * 2.0
        else:
            # X / Threads / Instagram
            score = likes * self.w_like + reposts * self.w_repost + replies * self.w_reply

        return round(score, 2)

    def rank_and_filter(self, posts: List[Dict[str, Any]], top_ratio: float = 0.2, min_count: int = 3) -> List[Dict[str, Any]]:
        for p in posts:
            p["engagement_score"] = self.calculate_score(p)

        # 依照互動分數由高至低排序
        sorted_posts = sorted(posts, key=lambda x: x["engagement_score"], reverse=True)
        target_count = max(min_count, int(len(sorted_posts) * top_ratio))
        return sorted_posts[:target_count]

    def analyze_post_content(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        對單則爆款貼文進行語意維度剖析
        """
        text = post.get("text", "")

        # 規則與語意啟發式分析（若未掛接雲端 LLM 時的快速判定）
        category = self._detect_category(text)
        hook_style = self._detect_hook_style(text)
        viral_factors = self._extract_viral_factors(text, post.get("engagement_score", 0), post.get("platform", "x"))
        imitation_guide = self._generate_imitation_guide(category, hook_style, text, post.get("platform", "x"))

        return {
            **post,
            "topic_category": category,
            "hook_style": hook_style,
            "viral_factors": viral_factors,
            "imitation_guide": imitation_guide
        }

    def _detect_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in ["工具", "tool", "ai", "開源", "架構", "github", "爬蟲", "代碼", "程式", "prompt", "模型"]):
            return "AI 工具評測與技術架構"
        elif any(k in text_lower for k in ["創業", "賺錢", "自媒體", "一人公司", "商業", "利潤", "變現", "流量", "獲客"]):
            return "一人創業與商業模式"
        elif any(k in text_lower for k in ["認知", "思考", "思維", "本質", "為什麼", "心態", "盲點"]):
            return "認知提升與個人成長"
        return "產業乾貨與趨勢觀察"

    def _detect_hook_style(self, text: str) -> str:
        first_line = text.split("\n")[0] if "\n" in text else text[:50]
        if any(k in first_line for k in ["為什麼", "千萬別", "多數人都錯了", "90%", "殘酷真相", "騙局", "秘密"]):
            return "反常識打破認知型 (Contrarian Hook)"
        elif any(k in first_line for k in ["整理了", "清單", "免費送", "打包", "資源", "乾貨", "模板"]):
            return "高價值資源誘惑型 (Resource Magnet Hook)"
        elif any(k in first_line for k in ["如何用", "實測", "3個步驟", "教學", "手把手", "指南"]):
            return "行動指南與教學型 (How-to Action Hook)"
        return "故事敘事與親身經歷型 (Storytelling Hook)"

    def _extract_viral_factors(self, text: str, score: float, platform: str) -> List[str]:
        factors = []
        if score > 2000:
            factors.append("具備極高轉發與擴散效應")
        if any(char in text for char in ["1.", "2.", "3.", "👉", "🔥", "📌", "【"]):
            factors.append("排版清爽結構化，降低閱讀負擔")
        if any(k in text for k in ["留言", "私訊", "轉發", "領取", "追蹤", "訂閱"]):
            factors.append("具備明確行動呼籲 (CTA) 驅動演算法擴散")
        if platform == "youtube":
            factors.append("標題精準切中痛點並提供完整實作展示")
        elif platform == "threads":
            factors.append("短平快對話感強烈，容易激發留言討論")
        if not factors:
            factors.append("切中受眾痛點與實際效率提升需求")
        return factors

    def _generate_imitation_guide(self, category: str, hook: str, original_text: str, platform: str) -> str:
        return (
            f"【{platform.upper()} 仿寫架構】採用「{hook}」為開頭，聚焦在「{category}」領域。\n"
            f"步驟：1. 第一行打破固有偏見或亮出驚人數據 ➔ 2. 說明具體工具或流程 ➔ 3. 條列落地步驟 ➔ 4. 文末 CTA 引導留言互動。"
        )

    def export_results(self, analyzed_posts: List[Dict[str, Any]], json_path: str, csv_path: str):
        # 輸出結構化 JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(analyzed_posts, f, ensure_ascii=False, indent=2)
        logger.info(f"結構化分析成果已寫入: {json_path}")

        # 輸出 CSV
        if analyzed_posts:
            keys = [
                "platform", "author", "engagement_score", "likes", "retweets", "replies", "views",
                "topic_category", "hook_style", "viral_factors", "text", "imitation_guide"
            ]
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                writer.writeheader()
                for p in analyzed_posts:
                    row = {**p}
                    if isinstance(row.get("viral_factors"), list):
                        row["viral_factors"] = " | ".join(row["viral_factors"])
                    writer.writerow(row)
            logger.info(f"爆款主題清單已匯出至 CSV: {csv_path}")
