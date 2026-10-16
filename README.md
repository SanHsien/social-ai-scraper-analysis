[English](README.en.md) | 中文版

# postlens：你自己的貼文表現分析

**把你從平台匯出的貼文資料，算成互動分數、依主題與開頭類型分組，產出一份 Markdown 報表。**

只讀本機檔案、不連網、零依賴（Python 標準函式庫）。回答的問題是：「我寫的哪種主題、哪種開頭、哪個時段，表現比較好？」

> 本 repo 原名的「scraper」是早期筆記留下的，現在**不含任何爬蟲功能**。資料來源限制見下方〈資料從哪裡來〉。

## 快速開始

需要 Python 3.10+，不用安裝套件。用內附的虛構示範資料跑一次：

```bash
python -m postlens analyze examples/sample_posts.csv --rules rules.example.json --out out
```

```text
analyzed 36 of 36 posts
wrote out\report.md
wrote out\posts_scored.csv
wrote out\summary.json
```

`out/report.md` 的一段（實際輸出）：

```text
## 依主題

| 分組 | 篇數 | 占比 | 分數中位數 | 分數平均 | 互動率中位數 | 前 10% 篇數 | 最高分貼文 |
|---|---:|---:|---:|---:|---:|---:|---|
| AI 工具實測 | 6 | 17% | 404.5 | 409.8 | 5.55% | 4 | Claude 和 ChatGPT 實測：同一個 bug 誰先修好？ |
| 工作流程 | 6 | 17% | 203.8 | 197.6 | 5.64% | 0 | 別再手動整理會議紀錄了，這個模板直接套 |
| 程式開發 | 9 | 25% | 114.0 | 149.0 | 4.99% | 0 | 部署前一定要跑的 3 個測試 |
| 未分類 | 12 | 33% | 67.2 | 118.8 | 4.34% | 0 | 整理了一份免費的提示詞懶人包 |
| 個人觀點（樣本太少） | 3 | 8% | 182.5 | 192.3 | 6.29% | 0 | 我覺得 AI 工具最大的成本不是訂閱費 |
```

報表還有：依開頭類型、依星期、依三小時時段、分數最高的 10 篇，以及解讀限制。

## 資料從哪裡來

只分析**你有權使用**的資料：

| 來源 | 怎麼取得 | 用法 |
|---|---|---|
| X（Twitter）帳號封存檔 | 設定 → 你的帳戶 → 下載資料封存檔，解壓後的 `data/tweets.js` | `python -m postlens analyze data/tweets.js` |
| 平台官方 API | 用你自己帳號的授權呼叫官方 API（例如 Threads API 的貼文與 insights），把結果存成 JSON | `{"data": [...]}` 或陣列都可以 |
| 平台的資料下載功能、後台報表 | 匯出成 CSV 或 JSON | 欄位名稱見下表 |
| 手動整理 | 自己建 CSV | 至少要有時間欄 |

**不做、也不接受**以下用途的功能或說明：爬取網頁、自動登入、繞過驗證碼或反爬機制、規避流量限制、蒐集未經同意的他人帳號資料。要分析別人的公開內容，請先確認平台條款與對方同意。

X 封存檔沒有回覆數與曝光數，報表會註明「本資料沒有曝光數」；轉發別人的貼文（`RT @` 開頭）預設排除，加 `--include-reposts` 才納入。

## 欄位名稱

CSV 與 JSON 用同一套別名，大小寫不拘；數字可以有千分位逗號。

| 欄位 | 接受的名稱 | 必填 |
|---|---|---|
| 時間 | `created_at` `timestamp` `date` `time` `published_at` `posted_at` | 是 |
| 內容 | `text` `full_text` `content` `message` `caption` `body` | |
| 按讚 | `likes` `like_count` `favorite_count` `favorites` `reactions` | |
| 回覆 | `replies` `reply_count` `comments` `comment_count` | |
| 轉發 | `reposts` `repost_count` `retweets` `retweet_count` `shares` `share_count` | |
| 引用 | `quotes` `quote_count` | |
| 曝光 | `views` `view_count` `impressions` `impression_count` | |
| 編號 | `id` `id_str` `post_id` `media_id` | |
| 連結 | `url` `permalink` `link` | |

時間格式：ISO 8601（沒有時區當成 UTC）、Unix 秒數、或 X 封存檔格式。

## 計算方式

- **互動分數** = 按讚×1 ＋ 回覆×1.5 ＋ 轉發×2 ＋ 引用×2（權重可在規則檔改）
- **互動率** = （按讚＋回覆＋轉發＋引用）÷ 曝光；沒有曝光數就不算，不會當成 0
- **百分位**：每篇分數在整份資料中的位置，平手取平均名次；`前 10% 篇數` 是百分位 ≥ 90 的篇數
- **分組統計**看中位數為主，平均數為輔；少於 5 篇的分組標「樣本太少」並排到最後

## 規則檔

`rules.example.json` 定義權重、主題、開頭類型：

```json
{
  "weights": {"likes": 1, "replies": 1.5, "reposts": 2, "quotes": 2},
  "topics": {"AI 工具實測": {"keywords": ["claude", "chatgpt", "實測"]}},
  "hooks": {"提問": {"patterns": ["[?？]\\s*$"]}}
}
```

- `keywords`：不分大小寫的字面比對；`patterns`：正規表示式
- 主題比對全文，一篇可以屬於多個主題，都不符合就是「未分類」
- 開頭類型只看**第一行**，依規則檔順序取第一個符合的，都不符合就是「其他」

先跑一次，抽查「未分類」與「其他」的貼文，再補規則。

## 選項

| 選項 | 說明 |
|---|---|
| `--format` | `auto`（看副檔名）／`csv`／`json`／`x-archive` |
| `--rules` | 規則檔；不給就只算分數，主題全為「未分類」 |
| `--out` | 輸出資料夾，預設 `out` |
| `--utc-offset` | 星期與時段用的時區，預設 `+08:00` |
| `--since` `--until` | 期間（含起不含迄）；只寫日期時以 `--utc-offset` 解讀 |
| `--include-reposts` | 納入轉發 |

結束碼：`0` 成功、`1` 篩選後沒有貼文、`2` 輸入或選項錯誤（錯誤訊息會指出檔名與列號）。

## 輸出

| 檔案 | 內容 |
|---|---|
| `report.md` | 人看的報表 |
| `posts_scored.csv` | 每篇的分數、百分位、互動率、主題、開頭類型，依分數排序（UTF-8 BOM，Excel 可直接開） |
| `summary.json` | 主題與開頭類型的統計，給其他程式或 AI 接手 |

## 邊界

- 主題與開頭類型是關鍵字規則，不是語意理解。需要語意分類，可以把 `posts_scored.csv` 交給你慣用的 AI 工具再處理。
- 報表呈現相關，不代表因果：粉絲數變化、演算法調整、單篇被轉發都會影響分數。
- `examples/sample_posts.csv` 由 `examples/make_sample.py` 以固定亂數種子產生，完全虛構。

## 開發

```bash
python -m unittest discover -s tests -v
```

Windows 完整檢查：`pwsh -File tools/dev_check.ps1`。

## 授權

[MIT](LICENSE)
