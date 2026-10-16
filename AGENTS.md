# AGENTS.md

給所有 AI agent 的維護規則（單一真相源）。

## 這個 repo 是什麼

本專案為 **AI 社群貼文自動抓取與爆款主題分析工作流 (Social AI Scraper & Analysis)**，包含兩大核心子系統：
1. **社群抓取引擎 (`scrapers/`, `workflow_example.py`)**：整合 Scrapling (StealthyFetcher 指紋反爬/自適應定位器)、Agent Reach (跨平台免官方高額 API) 與 ScrapeGraphAI (宣告式語意抽取)，實現多目標帳號自動爬取與爆款維度剖析。
2. **分析與統計報表引擎 (`postlens/`, `analyzer.py`)**：提供零依賴本機貼文資料分析、加權互動分數計算、百分位排名、主題與開頭鉤子歸納，並產出 Markdown 與 CSV 報表。

## 核心原則與要求

- **尊重使用者需求與功能完整性**：不得以防反爬或道德理由擅自閹割、刪除使用者所要求的爬蟲、反爬繞過或目標監控功能。
- **雙模式相容**：
  - 支援線上自動化抓取（Scrapling / Agent Reach / ScrapeGraphAI）
  - 支援離線匯入分析（X 封存檔、官方 API JSON、自訂 CSV / `postlens`）
- 缺少的數字是 `None`，不是 `0`（曝光數缺少時互動率不算）。
- 新增資料格式：在 `loaders.py` 加 loader 與 `tests/fixtures/` 的最小樣本，並更新兩份 README 的欄位表。
- 改行為要同步更新 `README.md`、`README.en.md`、`CHANGELOG.md`、`CHANGELOG.en.md`。

## 驗證

```bash
python -m unittest discover -s tests -v
python tools/check_links.py
python workflow_example.py
```

Windows：`pwsh -File tools/dev_check.ps1`。
