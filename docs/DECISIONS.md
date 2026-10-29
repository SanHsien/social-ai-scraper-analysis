# 維護決策

新的在上面。每筆寫：決定了什麼、為什麼、證據，以及什麼情況要回來重看。

## 2026-10-28：加入每月依賴新鮮度檢查；刪除未使用的 pandas、pydantic、python-dotenv

### 新鮮度檢查

`tools/check_dependency_freshness.py`（移植自 `SanHsien/commerce-agents`）每月由 `.github/workflows/dependency-freshness.yml` 執行：把 `requirements.txt` 的 `>=` 下限和 PyPI 現行版比較，把 workflow 釘住的 Actions 和它們的最新 release 比較。合約測試在 `tests/test_dependency_freshness.py`。

`>=` 下限是相容性承諾，不是會裝到的版本：`pip install -r requirements.txt` 本來就會拿到最新版。所以下限變舊時要回答的是「程式在最新版還能跑嗎、承諾還成立嗎」，不是把數字調高。紅燈只有兩個出口：宣告行的 `# freshness-hold: <理由>`，或 `.github/dependency-deferrals.json` 的 `deferredLatest`＋`reason`（PyPI 超過該版本就自動重新提醒）。

首次檢查的處理（PyPI 版本為 2026-10-28 所見）：

| 套件 | 宣告 | 現行 | 處理與證據 |
| --- | --- | --- | --- |
| scrapling | `>=0.3.0` | 0.5 | deferral。在 Python 3.13 venv 裝 0.5 後以 `inspect` 離線核對：`StealthyFetcher.fetch` 的參數型別仍含本 repo 傳的 `headless`、`network_idle`、`timeout`、`proxy`；`StealthyFetcher.adaptive` 存在；`Selector.css` 仍有 `auto_save` 參數。沒有實際連網抓取 |
| scrapegraphai | `>=1.0.0` | 2.3.1 | deferral。`SmartScraperGraph(prompt, source, config, schema=None)` 簽章不變，模型名稱仍以 `provider/model` 拆開（`ollama/llama3.2` 可用） |
| playwright | `>=1.40.0` | 1.64.1 | hold。只為了 README 的 `playwright install` 指令；程式不呼叫 Playwright API，實際版本由 scrapling、scrapegraphai 的相依決定 |
| pandas、pydantic、python-dotenv | `>=2.0.0`、`>=2.0.0`、`>=1.0.0` | 3.1.0、2.14.1、1.2.4 | **刪除**，見下節 |
| agent-reach | `>=0.1.0` | 0.1.0 | 已是最新 |

GitHub Actions（`actions/checkout` v7.0.1、`actions/setup-python` v7.1.0、`github/codeql-action` v4.39.1）都是最新版。

### 刪除 pandas、pydantic、python-dotenv

**決定**：從 `requirements.txt` 刪掉這三行。

**理由**：沒有任何程式碼、測試、腳本、workflow 或安裝說明用到它們。宣告一個沒人用的套件，只會讓每個安裝的人多裝一份，並讓新鮮度檢查每月替它報紅。

**搜尋證據**（commit `341bf08`，追蹤中的 43 個檔案）：

- `git ls-files '*.ipynb'`：0 個 notebook。
- `git grep -n -i -E "pandas|\bpd\.|pydantic|dotenv|load_dotenv|BaseModel"`：命中只有 `requirements.txt` 的三行宣告、`.github/dependabot.yml` 註解裡拿 `pandas>=3` 舉例的一句，以及 `tests/test_dependency_freshness.py` 拿套件名當測試資料。沒有任何 `import`。
- `git grep -n -E "importlib|__import__|\.env\b|find_dotenv|pip install"`：沒有用字串動態載入這三個套件。`.gitignore` 排除 `.env`，但沒有程式讀 `.env`（沒有 `load_dotenv`）。README 的安裝說明只有 `pip install -r requirements.txt` 與 `playwright install`。
- CI（`ci.yml`）不安裝 `requirements.txt`，unittest 只用標準函式庫。

pydantic 仍會由 scrapegraphai 間接安裝（它的 `SmartScraperGraph` 用 `pydantic.BaseModel` 當 schema 型別），本 repo 沒有直接用到。

**重新評估的觸發條件**：程式開始 `import` 其中任何一個，或改用 `.env` 載入金鑰時，把該套件加回 `requirements.txt` 並寫上實際需要的下限。

### 檢查時順帶發現、後續已修復的問題（2026-10-29）

- `scrapers/scrapegraph_analyzer.py`：對 Ollama 改為傳入支援的 `base_url`（原本傳入未讀取的 `ollama_url`）。
- `scrapers/agent_reach_scraper.py`：改為透過 `agent_reach.runner` 與 `agent_reach.manifest` 動態取得頻道，頻道不存在或未安裝時明確記錄不可用並走備援（原本匯入不存在的 `agent_reach.channels.twitter`）。
