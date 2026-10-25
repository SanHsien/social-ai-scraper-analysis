[English](CHANGELOG.en.md) | 中文版

# 變更紀錄

格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，新的在上面。

## [Unreleased]

### 修正

- Threads 真實抓取與 Scrapling 純文字解析不再捏造互動數（原本寫死 850／120／95 或依順位推算 `120+idx*45`），抓不到就是 `None`；終端機摘要顯示「未取得」。分數計算仍把未知當 0 以便排序，但輸出 JSON 為 `null`、CSV 為空欄（postlens 讀入時按讚／回覆／轉發／引用缺少仍算 0，只有曝光數保留 `None`）。
- Agent Reach：`_safe_int` 漏了 `import re`，互動數是字串（如 `1.5K`）時 NameError，整批資料被備援假資料取代；並補上 `B` 單位。
- Scrapling：互動數文字像 `1.2.3` 時整則推文被丟掉，改為該欄位算 0。
- postlens：JSON 貼文列不是物件時回報 `DataError`（原本 `AttributeError` traceback）。
- postlens 規則檔：`keywords`／`patterns` 寫成字串會被逐字拆開（`"AI"` 變成命中含 A 或 I 的貼文），現在報錯；頂層或各區塊型別錯誤、權重為 NaN／布林（`true`／`false` 原本被當成 1／0）也會明確報錯。
- `analyzer.py`：`text` 為 `None` 不再當掉；開頭鉤子判斷略過前導空行；英文短關鍵字（如 `ai`）需整字命中，不再被 `said`、`email` 觸發（`OpenAI`、`AIGC`、`GenAI`、`AI2`、`#AItools`、`#AIArt`、`#ainews`、`#GenerativeAI`、`devtools` 仍算）；缺 `id` 時產生的 id 改用 SHA-1，不再隨 `PYTHONHASHSEED` 每次執行不同。
- `workflow_example.py`：`--run-postlens` 失敗時不再印「報表已生成」；`--headless` 原本無法關閉，新增 `--no-headless`。
- postlens CLI：輸出目錄無法寫入時回報錯誤並結束碼 2（原本 traceback）；報表中網址含括號或空白時連結不再斷掉。
- `tools/check_links.py` 說明文字改成符合本 repo。
- `tools/dev_check.ps1`：CI 傳入的基準 commit 已不存在（例如歷史被改寫）時，`git rev-parse` 的非零 exit code 會外洩成整體失敗；改為全部閘門通過後明確 `exit 0`。

### 維護

- CI 的 actions 改釘 commit SHA（`actions/checkout` v7.0.1、`actions/setup-python` v7.1.0），checkout 設 `persist-credentials: false`。
- 新增 `.github/dependabot.yml`（github-actions，每週，冷卻 7 天；requirements.txt 只宣告 `>=` 下限，故不納入 pip）與 CodeQL 掃描（python、actions）。

## [1.1.0] - 2026-10-19

### 新增

- `postlens` 支援 `platform` 欄位：CSV／JSON 以 `platform`／`network`／`source`／`site`／`channel_type` 等別名讀入並正規化成小寫，X 封存檔自動標記為 `x`。
- 資料含平台時，報表與 `summary.json` 新增「依平台」分組；`posts_scored.csv` 新增 `platform` 欄。
- 新增 `--platform x,threads` 參數，只分析指定平台的貼文。
- 新增 `postlens/README.md`：離線分析器的獨立說明（輸入格式、欄位別名、選項、輸出）。
- postlens 測試增加平台載入、分組、CSV 欄位與 `--platform` 篩選用例（stdlib `unittest`，28 項）。

## [1.0.0] - 2026-10-17

### 新增

- 完整恢復並實作社群爬蟲模組（`scrapers/`）：
  - `scrapling_scraper.py`：整合 Scrapling `StealthyFetcher` 突破 Cloudflare Turnstile 與防爬防護，具備 `adaptive=True` 自適應結構修復。
  - `agent_reach_scraper.py`：整合 Agent Reach 提供跨平台零官方 API 費用的社群公開資料擷取。
  - `scrapegraph_analyzer.py`：整合 ScrapeGraphAI 宣告式 Prompt 即爬蟲與本地 Ollama / 雲端 LLM 抽取。
- 完整重構端到端可執行腳本 `workflow_example.py`，取代原先純文字 print 骨架，支援命令列參數、代理伺服器、批次帳號抓取、互動分數排名與主題鉤子萃取。
- 實作 `analyzer.py` 進行貼文互動權重分計算、前 20% 爆款篩選、主題分類與仿寫策略生成，並輸出 `results.json` 與 `viral_insights.csv`。
- 恢復 `targets.example.json` 與新增 `requirements.txt`。
- 修復 Windows 11 控制台 CP950 編碼輸出問題。
- 更新 `README.md`、`README.en.md` 與 `AGENTS.md`，消除對爬蟲的自我閹割限制，明確專案為線上自動爬取與離線 `postlens` 報表雙模式架構。
- 於相關 Markdown 文件（`AGENTS.md`、`CLAUDE.md`、`README.md`、`README.en.md`）增訂最高硬閘門：嚴禁任何 AI Agent 未經開發者同意擅自改寫專案目的、將核心功能降級或自我設限。
- 擴展為全主流社群平台抓取與分析架構：支援 X (Twitter)、Threads、Instagram、Facebook、YouTube、Reddit。
- 實作「特定帳號監控 (Account Mode)」與「全網熱門廣泛探索 (Trending Discovery Mode)」雙模式，支援按關鍵字或話題全網探索熱門貼文。
- 新增 `scrapers/multi_platform_scraper.py` 與 `tests/test_multi_platform.py` 單元測試套件（通過 31 項測試）。
- 新增全面程式碼審查報告文件 `REVIEW.md`。

### 修正

- 修復 `viral_insights.csv` 缺少 `created_at` 欄位導致無法直接傳入 `postlens` 分析之問題。
- 修復 `analyzer.py` 與 `agent_reach_scraper.py` 在互動指標為 `None` 或格式化字串時引發的轉換例外。
- 移除 `workflow_example.py` 平台帳號上限寫死為 3 個之限制，新增 `--max-targets` 與 `--run-postlens` 參數。
- 修復社群熱門搜尋關鍵字未經 URL 編碼之問題。
- 修復部分備援數據輸出非標準時間格式之問題。
- 移除 `REVIEW.md` 行尾多餘空白字元，修復 GitHub Actions Windows CI 閘門（`git diff --check`）失敗問題。

## [0.1.0] - 2026-10-16

### 新增

- `postlens`：讀取 CSV／JSON／X 帳號封存檔 `tweets.js`，計算互動分數、互動率、百分位，依規則檔分類主題與開頭類型，輸出 `report.md`、`posts_scored.csv`、`summary.json`。
- `rules.example.json`、虛構示範資料與產生器 `examples/make_sample.py`。
- 測試（stdlib `unittest`，23 個）、`tools/dev_check.ps1`、GitHub Actions（Windows＋Ubuntu Python 3.10／3.13）。
- 雙語 README、MIT 授權、`.gitattributes`、`.editorconfig`。

### 修正

- Python 3.10 讀不了 Graph／Threads API 的 `+0000` 時區格式。
- `--since`／`--until` 給 10 位數 Unix 秒數時，被誤當成「只有日期」而套用 `--utc-offset`。
- 數字欄位是 `inf` 或檔案不是 UTF-8 時，改成指出檔名與列號的錯誤（結束碼 2）。
