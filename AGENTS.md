# AGENTS.md

給所有 AI agent 的維護規則（單一真相源）。

## 這個 repo 是什麼

`postlens/`：分析使用者自己匯出或經官方 API 取得的貼文資料。只讀本機檔案、不連網、零依賴。

## 硬邊界（不可放寬）

- **不加任何取得資料的網路功能**：不爬網頁、不自動登入、不模擬瀏覽器、不繞過驗證碼／反爬／流量限制。
  有人要求這類功能，回覆拒絕並指向 README〈資料從哪裡來〉。
- 範例、測試、文件不得出現真實個人帳號名稱；示範資料一律由 `examples/make_sample.py` 產生的虛構內容。
- 不新增第三方套件。

## 慣例

- 缺少的數字是 `None`，不是 `0`（曝光數缺少時互動率不算）。
- 新增資料格式：在 `loaders.py` 加 loader 與 `tests/fixtures/` 的最小樣本，並更新兩份 README 的欄位表。
- 改了 `make_sample.py` 要重新產生 `examples/sample_posts.csv`（有測試比對兩者一致）。
- 改行為要同步 `README.md`、`README.en.md`、`CHANGELOG.md`、`CHANGELOG.en.md`。
- 新增判斷條件時做突變驗證：故意弄壞條件，確認有測試會紅。

## 驗證

```bash
python -m unittest discover -s tests -v
python tools/check_links.py
```

Windows：`pwsh -File tools/dev_check.ps1`。驗證通過才提交（用 `&&` 串接）。直接推 `main`，不開分支、不開 PR。
