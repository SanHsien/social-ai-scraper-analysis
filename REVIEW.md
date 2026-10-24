# 專案程式碼審查報告 (Repository Code Review)

審查日期：2026-10-17
審查對象：`social-ai-scraper-analysis` 全端專案代碼與架構

---

## 1. 審查範圍與總結 (Executive Summary)

本專案為 **AI 全社群貼文自動抓取與跨平台爆款主題分析工作流**，核心涵蓋：
1. **跨社群抓取引擎 (`scrapers/`)**：X (Twitter)、Threads、Instagram、Facebook、YouTube、Reddit 的帳號爬取與熱門關鍵字探索，整合 Scrapling (StealthyFetcher 指紋反爬/自適應定位器)、Agent Reach (跨平台免官方 API) 與 ScrapeGraphAI。
2. **分析與統計報表引擎 (`analyzer.py`, `postlens/`)**：互動加權計分、爆款前 20% 主題與開頭鉤子萃取、零依賴本地統計與 Markdown 報表生成。
3. **自動化流程與品質閘門 (`workflow_example.py`, `tests/`, `tools/`)**：端到端 CLI 執行工作流、單元測試套件與 Windows 開發檢查腳本。

### 總體審查結論
代碼架構分層清晰，解耦良好。本次審查發現並修復了數個跨模組資料互通缺陷、數值安全轉換漏洞與參數硬編碼問題，目前所有單元測試與開發閘門皆已順利綠燈通過。

---

## 2. 發現之缺陷與修正清單 (Bugs & Vulnerabilities Fixed)

### ① 缺陷 1：跨模組資料流斷裂（`viral_insights.csv` 缺少 `created_at`）
- **嚴重性**：高（High）
- **檔案**：`analyzer.py`
- **問題分析**：`workflow_example.py` 產出的 `viral_insights.csv` 未包含 `created_at` 與 `id` 欄位。當使用者將爬取之 CSV 輸入 `postlens` 分析時（`python -m postlens analyze viral_insights.csv`），`postlens` 的嚴格載入器會直接引發 `DataError: missing created_at/timestamp/date column` 終止執行。
- **修復方案**：在 `analyzer.py` 的 CSV 欄位清單補齊 `created_at`、`id`、`reposts`、`url` 等標準欄位，並將缺漏時間自動補齊為當前 UTC ISO-8601 時間戳記，達成與 `postlens` 100% 互通。

### ② 缺陷 2：指標數值轉換異常崩潰（NoneType 與格式化字串處理不當）
- **嚴重性**：中高（Medium-High）
- **檔案**：`analyzer.py`, `scrapers/agent_reach_scraper.py`
- **問題分析**：社群 API 或爬蟲回傳的互動數據中，若欄位值為 `None`（例如平台無曝光數）或帶有千分位逗號與單位縮寫（如 `"1,500"`、`"2.5K"`），原代碼直接呼叫 `float(None)` 或 `int(value)` 會拋出 `TypeError` 或 `ValueError` 導致爬取管線中斷。
- **修復方案**：實作 `_safe_float` 與 `_safe_int` 工具函式，針對 `None`、空字串、千分位逗號以及 `K` / `M` / `B` 單位進行正則解析與容錯轉換，防止爬蟲因單則異常貼文而崩潰。

### ③ 缺陷 3：目標帳號採樣上限寫死（Hardcoded Target Limit）
- **嚴重性**：中（Medium）
- **檔案**：`workflow_example.py`
- **問題分析**：原先在遍歷目標帳號時硬編碼為 `accounts[:3]`，使得當使用者在 `targets.json` 設定 20 或 100 個監控對象時，超過 3 個的帳號會被靜默略過。
- **修復方案**：新增 `--max-targets` 命令列參數，預設對清單內的所有帳號進行全數爬取，並支援依需求限制採樣數。

### ④ 缺陷 4：探索搜尋關鍵字未經 URL 編碼
- **嚴重性**：中低（Low-Medium）
- **檔案**：`scrapers/multi_platform_scraper.py`
- **問題分析**：在探索 Threads、X 等平台的搜尋 URL 時，直接字串格式化拼接 `f"https://www.threads.com/search?q={query}"`，若關鍵字包含中文或空格時易引發不合法的 URL 或被伺服器拒絕。
- **修復方案**：引入 `urllib.parse.quote_plus` 對查詢參數進行標準轉義。

### ⑤ 缺陷 5：非標準時間戳記導致下游解析失敗
- **嚴重性**：低（Low）
- **檔案**：`scrapers/scrapling_scraper.py`, `scrapers/multi_platform_scraper.py`
- **問題分析**：部分備援數據與次級文本解析器將發布時間寫為 `"recent"`，無法通過嚴格的 ISO-8601 時間解析器。
- **修復方案**：統一使用 `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")` 標準時間格式輸出。

---

## 3. 功能增強與管線打通 (Enhancements)

1. **一鍵聯動本地統計報表 (`--run-postlens`)**：
   在 `workflow_example.py` 增設 `--run-postlens` 旗標，抓取並匯出 CSV 後可自動喚起 `postlens` 生成結構化 Markdown 報表與百分位統計，實現爬取與深度分析無縫閉環。
2. **擴充單元測試覆蓋 (`tests/test_multi_platform.py`)**：
   新增針對 `_safe_float` 容錯能力、跨平台權重計分、以及 `postlens.loaders.load_csv` 互通性的自動化測試用例，全專案測試用例增加至 31 項。

---

## 4. 品質閘門驗證結果 (Verification Gates)

### 單元測試 (`python -m unittest discover -s tests -v`)
- **測試總數**：31 項
- **執行結果**：全數通過（31 OK，0 Failures，0 Errors）。

### 文件相對連結檢查 (`python tools/check_links.py`)
- **檢查文件數**：7 份 Markdown 檔案（含 `REVIEW.md`）。
- **執行結果**：0 個失效連結。

### 開發者完整閘門檢查 (`pwsh -File tools/dev_check.ps1`)
- **測試檢查**：通過。
- **連結檢查**：通過。
- **Git Diff 空白行檢查**：通過。

---

## 5. 後續最佳化建議 (Roadmap & Recommendations)

1. **Proxy 代理池自動輪替**：後續可增加代理健康狀態探測器，在遭遇 429 或 Cloudflare 驗證失敗時自動切換 IP。
2. **LLM 抽取重試與熔斷**：當本地 Ollama 或遠端 API 響應延遲或超時時，加入指數退避重試（Exponential Backoff）。
