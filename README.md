[English](README.en.md) | 中文版

# AI 社群貼文自動抓取與爆款主題分析工作流 (Social AI Scraper & Analysis)

本專案整理自 Threads 深度討論（來源：`https://www.threads.com/share/_jV5NQ2xs/`，原創作者：`@aistart_up` AI平凡人創業學院）。

核心議題：**「叫 AI 自動抓取 100 個 X（Twitter）帳號的貼文，自動分析哪種主題與鉤子表現最好。結合三大開源工具與分析引擎，打造自媒體選題與一人創業閉環。」**

專案兼具**線上自動化爬取（突破反爬與高昂官方 API 限制）**與**離線零依賴數據分析報表（`postlens`）**。

---

## 1. 核心流程與架構圖 (Architecture)

```
[目標來源: 100 個 X 帳號清單 (targets.json)]
                │
                ▼ 突破 Cloudflare、Turnstile 防護、指紋反爬與前端結構改版
         【Scrapling】
                │  - StealthyFetcher 防偵測無頭瀏覽器
                │  - Adaptive Locators (自適應定位器，DOM 結構變更自動修復)
                ▼
         【Agent Reach】
                │  - 專為 AI Agent 設計的跨平台社群介面 (X / Reddit / YouTube)
                │  - 零官方 API 費用，整合本地 Session、RSS 與多路由容錯
                ▼
        【ScrapeGraphAI】
                │  - Prompt 即爬蟲（自然語言語意解析與知識圖譜構建）
                │  - 支援本地 Ollama (Llama 3, Qwen 2.5) 零成本或雲端 LLM
                ▼
    [爆款主題分析與報表引擎 (analyzer.py / postlens)]
                │  - 互動加權評分 (Likes + Retweets*2.5 + Replies*1.5)
                │  - 篩選前 10%～20% 爆款並自動拆解：主題類別、開頭鉤子、爆款要素、仿寫指南
                ▼
[產出結果: results.json & viral_insights.csv / postlens Markdown 報表]
```

---

## 2. 三大開源爬蟲工具深度解析

### ① Scrapling
- **定位**：高韌性、自適應的現代 Python 爬蟲框架。
- **解決痛點**：傳統爬蟲（如 BeautifulSoup / Scrapy）在網站前端改版更換 CSS class 或 DOM 結構時會瞬間壞掉；X 更有嚴苛的 Cloudflare / 反爬機制。
- **核心特點**：
  - **StealthyFetcher 防偵測**：底層具備瀏覽器指紋混淆技術，開箱即用穿透各類反機器人驗證。
  - **Adaptive Locators (`adaptive=True`)**：具備結構記憶能力，網頁佈局改動仍能智慧定位目標元素。
  - **資源過濾加速**：支援 `block_ads=True` 與 `disable_resources=True`，阻擋無關追蹤碼與重度圖片載入。

### ② Agent Reach (`agent-reach`)
- **定位**：為 AI Agent（Claude Code, Cursor, Windsurf 等）設計的社群公開資料統一入口。
- **解決痛點**：X 官方 API 費用門檻極高，一般個人創作者難以負擔；各大社群平台接口破碎。
- **核心特點**：
  - **零官方 API 費用**：整合輕量爬蟲、RSS、本地 Session 與開放端點。
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

## 3. 專案目錄結構

```
social-ai-scraper-analysis/
├── scrapers/                     # 爬蟲模組
│   ├── __init__.py
│   ├── scrapling_scraper.py      # Scrapling StealthyFetcher 與自適應解析
│   ├── agent_reach_scraper.py    # Agent Reach 跨平台免 API 社群調用
│   └── scrapegraph_analyzer.py   # ScrapeGraphAI 宣告式 Prompt 抽取
├── analyzer.py                   # 互動率評分、爆款篩選、鉤子拆解與仿寫模組
├── workflow_example.py           # 完整端到端可執行自動化工作流腳本
├── targets.example.json          # 監控對象清單範本
├── requirements.txt              # 爬蟲與 AI 套件依賴
├── postlens/                     # 零依賴本機數據分析報表引擎
│   ├── __init__.py
│   ├── analysis.py               # 統計分組與百分位計算
│   ├── loaders.py                # CSV / JSON / X Archive 載入器
│   └── report.py                 # Markdown 報表生成器
├── examples/                     # 範例資料集
├── tests/                        # 單元測試集
└── README.md
```

---

## 4. 快速安裝與環境建置

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

## 5. 執行工作流

### 模式 A：線上自動化爬取與爆款分析
執行整合管線，自動抓取目標帳號並產出爆款主題分析：
```bash
python workflow_example.py
```

支援自訂參數：
```bash
# 指定使用 Scrapling 引擎，並設定代理伺服器
python workflow_example.py --engine scrapling --proxy http://127.0.0.1:7890 --max-posts 10

# 使用 Agent Reach 跨平台介面
python workflow_example.py --engine agent-reach

# 指定自訂目標清單與輸出檔名
python workflow_example.py --targets targets.example.json --output-csv viral_insights.csv
```

### 模式 B：離線貼文數據報表 (`postlens`)
若手邊已有封存檔或已抓取之 CSV/JSON 檔案，可直接呼叫內建的零依賴分析模組：
```bash
python -m postlens analyze examples/sample_posts.csv --rules rules.example.json --out out
```
產出：
- `out/report.md`：依主題、開頭類型、時段分組的完整 Markdown 報表。
- `out/posts_scored.csv`：每篇貼文的評分與百分位數。
- `out/summary.json`：結構化摘要統計。

---

## 6. 分析計算方式與維度

- **互動加權分數**：
  $$\text{Score} = \text{Likes} \times 1.0 + \text{Retweets} \times 2.5 + \text{Replies} \times 1.5 + \text{Quotes} \times 2.0$$
- **爆款萃取維度**：
  - `topic_category`：領域主題分類（AI 工具評測、一人創業、個人成長等）
  - `hook_style`：開頭鉤子型態（反常識顛覆型、利益誘惑型、教學清單型等）
  - `viral_factors`：高轉發關鍵驅動要素
  - `imitation_guide`：客製化仿寫範本指南

---

## 7. 測試與驗證

執行完整測試套件：
```bash
python -m unittest discover -s tests -v
python tools/check_links.py
python workflow_example.py
```

Windows 完整檢查：
```powershell
pwsh -File tools/dev_check.ps1
```

---

## 8. 專案守則與維護規範 (Governance & Agent Rules)

- **核心定位與開發者意志**：本專案聚焦於社群公開資料擷取、自適應突破反爬與爆款主題自動化分析。
- **嚴禁 Agent 擅自自我設限**：詳見 [AGENTS.md](AGENTS.md)。嚴禁任何 AI Agent 未經開發者明確同意擅自改寫專案定位、閹割核心爬蟲與反爬功能、或刪減目標清單。任何維護與程式碼調整皆必須以開發者之明確需求為唯一依歸。

---

## 9. 授權條款

[MIT](LICENSE)
