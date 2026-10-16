[English](CHANGELOG.en.md) | 中文版

# 變更紀錄

格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，新的在上面。

## 2026-10-17

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

## 2026-10-16

### 新增

- `postlens`：讀取 CSV／JSON／X 帳號封存檔 `tweets.js`，計算互動分數、互動率、百分位，依規則檔分類主題與開頭類型，輸出 `report.md`、`posts_scored.csv`、`summary.json`。
- `rules.example.json`、虛構示範資料與產生器 `examples/make_sample.py`。
- 測試（stdlib `unittest`，23 個）、`tools/dev_check.ps1`、GitHub Actions（Windows＋Ubuntu Python 3.10／3.13）。
- 雙語 README、MIT 授權、`.gitattributes`、`.editorconfig`。

### 修正

- Python 3.10 讀不了 Graph／Threads API 的 `+0000` 時區格式。
- `--since`／`--until` 給 10 位數 Unix 秒數時，被誤當成「只有日期」而套用 `--utc-offset`。
- 數字欄位是 `inf` 或檔案不是 UTF-8 時，改成指出檔名與列號的錯誤（結束碼 2）。
