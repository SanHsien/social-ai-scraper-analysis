[English](README.en.md) | 中文版

# AI 全社群貼文自動抓取與跨平台爆款主題分析工作流 (Multi-Platform Social AI Scraper & Analysis)

本專案源自 Threads 深度討論（來源：`https://www.threads.com/share/_jV5NQ2xs/`，原創作者：`@aistart_up` AI平凡人創業學院）。

核心目標：**「不只侷限於 X，全面擴展至 X (Twitter)、Threads、Instagram、Facebook、YouTube、Reddit 等各大主流社群平台；既能針對特定清單帳號批次爬取，更能不限帳號全網廣泛搜尋熱門議題與爆款貼文，自動歸納高互動主題、開頭鉤子 (Hook) 與仿寫指南。」**

用 **`postlens`** 把社群貼文資料整理成互動分數、主題與開頭鉤子報表（離線、零依賴）；資料可來自官方 API、平台匯出檔，或 `scrapers/` 裡的抓取器（技術細節見[第 3 節](#3-三大開源爬蟲工具深度解析)）。

---

## 1. 核心流程與架構圖 (Architecture)

```
       ┌─────────────────────────────────────────────────────────┐
       │ 雙探索模式：                                            │
       │  A. 指定帳號監控 (targets.json: X, Threads, IG, YT...) │
       │  B. 全網熱門議題探索 (Discovery: 關鍵字/話題/Hashtag)   │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼ 抓取層（scrapers/，細節見第 3 節）
                             【Scrapling】
                                    │  - 無頭瀏覽器抓取
                                    │  - Adaptive Locators (自適應定位器，DOM 結構變更自動修復)
                                    ▼
                             【Agent Reach】
                                    │  - 跨平台社群介面 (X / Reddit / YouTube / Threads 等)
                                    │  - 零官方 API 費用，整合本地 Session、RSS 與多路由容錯
                                    ▼
                            【ScrapeGraphAI】
                                    │  - Prompt 即爬蟲（自然語言語意解析與知識圖譜構建）
                                    │  - 支援本地 Ollama (Llama 3, Qwen 2.5) 零成本或雲端 LLM
                                    ▼
    [跨平台爆款主題分析與報表引擎 (analyzer.py / postlens)]
       │  - 平台加權評分 (X/Threads: 讚+轉*2.5+回*1.5 | YT: 觀看+讚+留言 | Reddit: 推+評)
       │  - 篩選前 10%～20% 爆款並自動拆解：主題領域、開頭鉤子、爆款要素、仿寫指南
       ▼
[產出成果: results.json & viral_insights.csv / postlens Markdown 報表]
```

---

## 2. 支援社群平台與抓取模式

### 支援的主流平台 (Platforms)
| 平台代碼 | 平台名稱 | 支援模式 | 核心指標 |
|---|---|---|---|
| `x` | X (前 Twitter) | 帳號監控 / 熱門搜尋 | Likes, Retweets, Replies, Views |
| `threads` | Instagram Threads | 帳號監控 / 熱門搜尋 | Likes, Reposts, Replies |
| `instagram` | Instagram (IG) | 帳號主頁 / 探索標籤 | Likes, Comments, Shares |
| `facebook` | Facebook (FB) | 公開粉專 / 社團話題 | Likes/Reactions, Shares, Comments |
| `youtube` | YouTube | 頻道影片 / 熱門關鍵字 | Views, Likes, Comments, Transcripts |
| `reddit` | Reddit | 指定 Subreddit / 全站熱榜 | Upvotes, Comments, Award/Share |

### 兩大運作模式 (Modes)
1. **指定帳號監控 (`--mode accounts`)**：
   依據 `targets.example.json` 設定的各平台指標帳號，批次採樣抓取近期發布內容。
2. **全網熱門廣泛探索 (`--mode trending`)**：
   不限於特定帳號，直接鎖定特定領域關鍵字（例如：「AI 工具」、「一人創業」、「自動化」），全網跨平台抓取最新爆發的高互動貼文。

---

## 3. 三大開源爬蟲工具深度解析

> ⚠️ **使用風險**：以抓取器取得平台資料，可能違反該平台的使用條款；執行抓取的帳號或 IP 可能遭限流、封鎖或停權。風險由使用者自行判斷與承擔。能用官方 API 或平台提供的資料匯出時，建議優先使用，再交給 `postlens` 分析。

### ① Scrapling
- **定位**：高韌性、自適應的現代 Python 爬蟲框架。
- **核心特點**：
  - **StealthyFetcher 防偵測**：底層具備瀏覽器指紋混淆技術，開箱即用穿透 Cloudflare Turnstile、AWS WAF 各類反爬驗證。
  - **Adaptive Locators (`adaptive=True`)**：具備結構記憶能力，網頁佈局改動仍能智慧重新定位目標元素。
  - **資源過濾加速**：支援 `block_ads=True` 與 `disable_resources=True`，阻擋無關追蹤碼與重度圖片載入。

### ② Agent Reach (`agent-reach`)
- **定位**：為 AI Agent（Claude Code, Cursor, Windsurf 等）設計的跨平台社群公開資料統一入口。
- **核心特點**：
  - **零官方 API 費用**：整合輕量爬蟲、RSS、本地 Session 與開放端點，免除動輒數千美元的 API 門檻。
  - **多平台擴展**：一次打通 X (Twitter)、Reddit、YouTube 字幕、GitHub 等社群生態。

### ③ ScrapeGraphAI
- **定位**：由 LLM 驅動的知識圖譜爬蟲函式庫（"Scrape by asking"）。
- **核心特點**：
  - **宣告式抓取**：只要下自然語言 Prompt（例如：「提取所有貼文內容、發布時間、按讚數，並分類為主題標籤」）。
  - **本地模型支援**：可對接 Ollama（例如 Llama 3, Qwen 2.5），達成零成本隱私化資料提取。

---

## 4. 專案目錄結構

```
social-ai-scraper-analysis/
├── scrapers/                     # 爬蟲模組
│   ├── __init__.py
│   ├── multi_platform_scraper.py # 跨平台整合調度 (X, Threads, IG, FB, YT, Reddit)
│   ├── scrapling_scraper.py      # Scrapling StealthyFetcher 與自適應解析
│   ├── agent_reach_scraper.py    # Agent Reach 跨平台免 API 社群調用
│   └── scrapegraph_analyzer.py   # ScrapeGraphAI 宣告式 Prompt 抽取
├── analyzer.py                   # 跨平台互動評分、爆款篩選、鉤子拆解與仿寫模組
├── workflow_example.py           # 完整端到端可執行自動化工作流腳本
├── targets.example.json          # 跨平台監控清單與熱門搜尋詞範本
├── requirements.txt              # 爬蟲與 AI 套件依賴
├── postlens/                     # 零依賴本機數據分析報表引擎
│   ├── __init__.py
│   ├── analysis.py               # 統計分組與百分位計算
│   ├── loaders.py                # CSV / JSON / X Archive 載入器
│   └── report.py                 # Markdown 報表生成器
├── examples/                     # 範例資料集
├── tests/                        # 單元測試集 (含跨平台測試)
└── README.md
```

---

## 5. 快速安裝與環境建置

### 步驟一：安裝相依套件
```bash
pip install -r requirements.txt
```

### 步驟二：安裝瀏覽器與防偵測內核
```bash
# 安裝 Scrapling 防反爬內核
scrapling install

# 安裝 Playwright 驅動程式
playwright install
```

---

## 6. 執行工作流

### 模式 A：全網熱門廣泛探索 (Trending Discovery)
直接針對特定關鍵字跨各大平台抓取爆款內容：
```bash
# 全網搜尋「一人創業」熱門貼文 (涵蓋 X, Threads, YouTube, Reddit)
python workflow_example.py --mode trending --platforms all --query "一人創業"

# 指定特定平台搜尋「AI 工具」
python workflow_example.py --mode trending --platforms threads,youtube,reddit --query "AI 工具"
```

### 模式 B：指定帳號跨平台監控 (Account Mode)
讀取 `targets.example.json` 監控各平台名單：
```bash
# 抓取所有已設定平台之帳號
python workflow_example.py --mode accounts --platforms all

# 僅針對 X 與 Threads 抓取
python workflow_example.py --mode accounts --platforms x,threads --max-posts 5
```

### 模式 C：離線貼文數據報表 (`postlens`)
若手邊已有封存檔或已抓取之 CSV/JSON 檔案，可直接呼叫內建的零依賴分析模組：
```bash
python -m postlens analyze examples/sample_posts.csv --rules rules.example.json --out out
```
產出：
- `out/report.md`：依主題、開頭類型、時段分組的完整 Markdown 報表。
- `out/posts_scored.csv`：每篇貼文的評分與百分位數。
- `out/summary.json`：結構化摘要統計。

---

## 7. 測試與驗證

執行完整測試套件：
```bash
python -m unittest discover -s tests -v
python tools/check_links.py
python workflow_example.py --mode accounts --platforms all
python workflow_example.py --mode trending --query "AI"
```

Windows 完整檢查：
```powershell
pwsh -File tools/dev_check.ps1
```

---

## 8. 專案守則與維護規範 (Governance & Agent Rules)

- **核心定位與開發者意志**：本專案聚焦於跨社群平台公開資料擷取、自適應突破反爬與爆款主題自動化分析。
- **嚴禁 Agent 擅自自我設限**：詳見 [AGENTS.md](AGENTS.md)。嚴禁任何 AI Agent 未經開發者明確同意擅自改寫專案定位、閹割核心爬蟲與反爬功能、或刪減目標清單。任何維護與程式碼調整皆必須以開發者之明確需求為唯一依歸。

---

## 9. 授權條款

[MIT](LICENSE)
