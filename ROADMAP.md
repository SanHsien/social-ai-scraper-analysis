# 路線圖

> 本 repo 後續工作的單一真相源。做完一項，就在同一個 commit 刪掉那一列；新工作只加在這裡。
> 現況段的數字是 2026-10-29 依 `main` `554bc5743485` 查的快照，開工前先重查 GitHub。

## 現況

社群貼文互動分析與爆款主題整理（跨平台資料正規化、互動分數、主題與開頭鉤子歸納、`postlens` 離線報表），自有 repo（public，非 fork，沒有上游）。健康：`CI`、`CodeQL`、`Dependency freshness` 預設分支最近一次皆 success（2026-10-28）；open issue 0 筆、open PR 0 筆；Dependabot 與 Code scanning 告警 0 筆；最近 release 為 v1.0.0（2026-10-16）。近期可以直接動手的已知缺陷已修復完畢，目前無待辦缺陷。

## 近期：可以直接動手

目前無待辦項目。

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
