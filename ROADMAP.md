# 路線圖

> 本 repo 後續工作的單一真相源。做完一項，就在同一個 commit 刪掉那一列；新工作只加在這裡。
> 現況段的數字是 2026-10-29 依 `main` `554bc5743485` 查的快照，開工前先重查 GitHub。

## 現況

社群貼文互動分析與爆款主題整理（跨平台資料正規化、互動分數、主題與開頭鉤子歸納、`postlens` 離線報表），自有 repo（public，非 fork，沒有上游）。健康：`CI`、`CodeQL`、`Dependency freshness` 預設分支最近一次皆 success（2026-10-28）；open issue 0 筆、open PR 0 筆；Dependabot 與 Code scanning 告警 0 筆；最近 release 為 v1.0.0（2026-10-16）。已知未修的是三個不影響 CI 的缺陷，列在近期表。

## 近期：可以直接動手
| 項目 | 為什麼 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |
| 修正 `ollama_url` 設定不生效 | `scrapers/scrapegraph_analyzer.py` 把 `ollama_url` 寫進 `graph_config["llm"]`，但 scrapegraphai 2.3.1 不讀這個鍵，自訂的 Ollama 位址不會生效 | 先寫離線測試（以最新版支援的鍵名斷言設定被傳入，修前失敗）；`python -m unittest discover -s tests` 綠；`docs/DECISIONS.md` 對應「未修」條目更新或刪除 | Claude Sonnet | `scrapers/scrapegraph_analyzer.py:23,65`；`.github/dependency-deferrals.json`（scrapegraphai 條目）；依賴新鮮度報告（2026-10-28） |
| 修正 `agent_reach` 的 import 路徑 | `scrapers/agent_reach_scraper.py` import `agent_reach.channels.twitter`，在最新版 agent-reach 0.1.0 不存在，函式庫這條路一定退回備援資料 | 在 agent-reach 最新版找出替代入口並先寫離線測試（修前走備援、修後走真實入口或明確回報「不可用」）；`python -m unittest discover -s tests` 綠 | Claude Sonnet | `scrapers/agent_reach_scraper.py:43`；依賴新鮮度報告（2026-10-28） |
| `tools/dev_check.ps1` 切到 repo 根目錄再跑 unittest | 從別的目錄呼叫時，unittest 找不到 `scrapers` 模組而失敗（CI 從根目錄跑所以不受影響） | 從非根目錄執行 `pwsh -NoProfile -File <路徑>\tools\dev_check.ps1` exit 0 | Claude Haiku | `tools/dev_check.ps1:8,20`；依賴新鮮度報告（2026-10-28） |

## 中期：等條件成立再做
| 項目 | 觸發條件 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |
| scrapling／scrapegraphai deferral 到期處理 | PyPI 出現比 `deferredLatest` 更新的版本，`Dependency freshness`（每月 1 日）會自動轉紅 | 離線核對新版簽章（`inspect`）、更新或刪除該筆 deferral（維持三段式版本號）；`python tools/check_dependency_freshness.py --strict` exit 0 | Claude Sonnet | `.github/dependency-deferrals.json`；`.github/workflows/dependency-freshness.yml:14` |
| `postlens` 缺值互動數 Optional 化 | 維護者決定要區分「未取得」與「0」（目前載入時缺少的按讚／回覆／轉發／引用算 0，只有曝光數保留 None） | 模型、評分、報表三處一致處理 None；補測試證明缺值不被當 0 排名；`python -m unittest discover -s tests` 綠；CHANGELOG 該條已知殘留註記刪除 | Claude Opus | `postlens/models.py:15-18`；深掃報告（2026-10-26）「追加修正」 |
| 真實抓取驗證（Threads／Scrapling 路徑） | 維護者有登入或可用網路環境並要實測 | 在實機跑一次抓取，確認互動數缺值時為「未取得」而非捏造數字；結果記進 `docs/DECISIONS.md` | 維護者 | 深掃報告（2026-10-26）；commit `a0c4fa6` |

## 刻意不做
| 不做什麼 | 理由 | 什麼情況下重新考慮 |
| --- | --- | --- |
| 把 pip 加進 `dependabot.yml` | `requirements.txt` 只宣告 `>=` 下限，由每月 `Dependency freshness` 檢查；既有決定（見 `.github/dependabot.yml` 註解） | 改為宣告 exact pin 時 |
| 為 `posts_scored.csv` 加 CSV 公式注入前綴 | 加前綴會破壞 analyzer→postlens 往返與資料保真 | 報表要直接交給試算表使用者開啟時 |
| 重新加回 pandas、pydantic、python-dotenv | 全 repo 搜尋確認未使用，已於 `98ff636` 刪除（搜尋證據在 `docs/DECISIONS.md`） | 程式實際需要該套件時 |
| 修改 Playwright 的 hold | 只為 README 的 `playwright install`，程式不呼叫其 API | 程式開始呼叫 Playwright API 時 |

## 維護方式

自有 repo：以 `tools\dev_check.ps1` 與 `python -m unittest discover -s tests` 全綠為閘門；每月 `Dependency freshness`、每週 `CodeQL`；有使用者可見變更才升版並建立 release。
