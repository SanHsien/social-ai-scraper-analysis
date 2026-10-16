[English](CHANGELOG.en.md) | 中文版

# 變更紀錄

格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，新的在上面。

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

### 移除

- 原 README 中繞過反爬與 Cloudflare 的工具介紹與安裝說明。
- `targets.example.json`（列有真實個人帳號）與只會印說明文字的 `workflow_example.py`。
