# AI 社群貼文自動抓取與爆款主題分析工作流 (Social AI Scraper & Analysis)

本專案整理自 Threads 討論（來源：`https://www.threads.com/share/_jV5NQ2xs/`，原創作者：`@aistart_up` AI平凡人創業學院）。
核心議題：**「叫 AI 去抓 100 個 X（Twitter）帳號上個月的貼文，自動整理出哪種主題表現最好。這件事現在用三個開源工具就能串起來。」**

---

## 1. 核心流程與架構圖 (Architecture)

```
[目標來源: 100 個 X 帳號清單 (targets.json)]
                │
                ▼ (突破反爬、Cloudflare 防護、防前端版面異動)
         【Scrapling】
                │  自適應結構抓取、Stealth 模式避開反爬偵測
                ▼
         【Agent Reach】
                │  AI Agent 專屬跨平台零 API 費用接口 (X / Reddit / YT 等)
                ▼
       【ScrapeGraphAI】 (串接本地 Ollama 或 OpenAI/Claude API)
                │  Prompt 即爬蟲，語意解析與維度抽取 (標籤、痛點、互動率)
                ▼
   [產出結果: 結構化 JSON / CSV 爆款主題資料庫 & 內容創作指南]
```

---

## 2. 三大開源工具深度解析

### ① Scrapling
- **定位**：高韌性、自適應的現代 Python 爬蟲框架。
- **解決痛點**：傳統爬蟲（如 BeautifulSoup / Scrapy）在網站前端改版更換 CSS class 或 DOM 結構時會瞬間壞掉；X 更有嚴苛的 Cloudflare / 反爬機制。
- **核心特點**：
  - **Adaptive Locators (`adaptive=True`)**：具備結構記憶能力，網頁佈局改動仍能智慧定位目標元素。
  - **Stealth Fetchers**：開箱即用的防偵測 HTTP/瀏覽器 Fetcher，能直接處理各類反爬閘門。
  - **高效併發**：支援多 Session、自動 Proxy 輪替與自適應節流。

### ② Agent Reach
- **定位**：為 AI Agent（Claude Code, Cursor, Windsurf 等）設計的社群公開資料統一入口。
- **解決痛點**：X 官方 API 費用門檻極高，一般個人創作者難以負擔；各大社群平台接口破碎。
- **核心特點**：
  - **零官方 API 費用**：整合輕量爬蟲、RSS 與平台公開接口。
  - **多平台支援**：一次打通 X (Twitter)、Reddit、YouTube、GitHub 等社群生態。
  - **Agent 友善**：專門為 Coding Assistant / Autonomous Agent 設計，隨插即用。

### ③ ScrapeGraphAI
- **定位**：由 LLM 驅動的知識圖譜爬蟲函式庫（"Scrape by asking"）。
- **解決痛點**：不需要針對每個頁面手寫冗長的 Regex / XPath 解析規則。
- **核心特點**：
  - **宣告式抓取**：只要下自然語言 Prompt（例如：「提取所有貼文內容、發布時間、按讚數、並分類為主題標籤」）。
  - **支援本地模型**：可對接 Ollama（例如 Llama 3, Qwen 2.5）或雲端 API，達成零成本隱私化資料提取。
  - **輸出結構化**：直接吐出乾淨嚴謹的 JSON 結構。

---

## 3. 值得借鏡的商業與工作流思維

1. **從「規則維護」演進為「語意抽取」**：
   不用再花時間修復因為前端 Class 名稱變更而壞掉的爬蟲腳本，讓 AI 直接理解文字語意與排版邏輯。
2. **數據驅動選題（Data-Driven Ideation）**：
   自媒體創作最忌憑空猜測受眾痛點。透過大規模採樣同領域前 100 名競品或頂尖帳號，用按讚數、轉推率（Engagement Rate）客觀計算出前 10% 的爆款主題。
3. **低成本自動化閉環**：
   結合開源工具與本地 LLM，在免付高額 API 訂閱的前提下，實現「數據收集 ➔ 主題聚類 ➔ 爆款拆解 ➔ 仿寫生成」的完整自動化管線。

---

## 4. 具體可仿照執行的落地步驟

### 步驟一：定義監控對象
建立 `targets.json` 檔案，收錄 20～100 個你所在利基領域（AI 工具、程式設計、電商、理財等）的活躍帳號。

### 步驟二：安裝核心環境
```bash
pip install scrapling scrapegraphai playright
playwright install
```

### 步驟三：批次擷取與清洗
使用 Scrapling / Agent Reach 批次爬取上個月所有公開貼文，過濾出互動指標（Likes, Retweets, Replies）。

### 步驟四：LLM 語意歸納與打分
使用 ScrapeGraphAI 或直接呼叫 LLM 進行以下欄位提取：
- `topic_category`：主題領域（工具評測、乾貨整理、產業快訊、個人觀點）
- `hook_type`：開頭鉤子型態（反常識認知、利益誘惑、焦慮喚起、資源贈送）
- `engagement_score`：計算加權分數，例如 `Likes + Retweets * 2 + Replies * 1.5`

### 步驟五：產生仿寫腳本與內容日曆
挑選出排名前 10% 的貼文，交由 AI 分析其論證結構（Hook ➔ Problem ➔ Solution ➔ CTA），並改寫成適合自己品牌語調的 Threads / X 貼文草稿。
