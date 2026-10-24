# postlens：分析你自己匯出的貼文資料

零依賴（Python 標準函式庫）、只讀本機檔案、不連網的離線分析器。把你從平台**自己匯出**或透過**官方 API** 取得的貼文，算成互動分數、依平台／主題／開頭類型分組，產出 Markdown 報表。

與本專案的線上抓取模組無關，可單獨使用。

## 用法

```bash
python -m postlens analyze <檔案> [選項]
```

```bash
# X 帳號封存檔
python -m postlens analyze data/tweets.js

# 自己的 CSV，套規則檔，只看特定平台
python -m postlens analyze my_posts.csv --rules rules.example.json --platform x,threads --out out
```

輸出到 `--out`（預設 `out/`）：`report.md`（人看）、`posts_scored.csv`（逐篇，依分數排序，含 BOM 供 Excel 開）、`summary.json`（給程式接手）。

結束碼：`0` 成功、`1` 篩選後沒有貼文、`2` 輸入或選項錯誤（訊息會指出檔名與列號）。

## 輸入格式

`--format auto`（看副檔名）／`csv`／`json`／`x-archive`。CSV 與 JSON 欄位名稱大小寫不拘、數字可帶千分位逗號。

| 欄位 | 接受的名稱 | 必填 |
|---|---|---|
| 時間 | `created_at` `timestamp` `date` `time` `published_at` `posted_at` | 是 |
| 內容 | `text` `full_text` `content` `message` `caption` `body` | |
| 按讚 | `likes` `like_count` `favorite_count` `favorites` `reactions` | |
| 回覆 | `replies` `reply_count` `comments` `comment_count` | |
| 轉發 | `reposts` `repost_count` `retweets` `retweet_count` `shares` `share_count` | |
| 引用 | `quotes` `quote_count` | |
| 曝光 | `views` `view_count` `impressions` `impression_count` | |
| 平台 | `platform` `network` `source` `site` `channel_type` | |
| 編號 | `id` `id_str` `post_id` `media_id` | |
| 連結 | `url` `permalink` `link` | |

時間：ISO 8601（無時區當 UTC）、Unix 秒數、或 X 封存檔格式。缺少的數字是 `None`（曝光缺少時互動率不算），不當成 0。

## 計算

- **互動分數** = 按讚×1 ＋ 回覆×1.5 ＋ 轉發×2 ＋ 引用×2（權重可在規則檔改）
- **互動率** = （按讚＋回覆＋轉發＋引用）÷ 曝光；沒有曝光就不算
- **百分位**：每篇分數在整份資料中的位置，平手取平均名次
- **分組**看中位數為主；少於 5 篇標「樣本太少」排到最後

## 選項

| 選項 | 說明 |
|---|---|
| `--format` | `auto`／`csv`／`json`／`x-archive` |
| `--rules` | 規則檔（權重、主題、開頭類型）；不給就只算分數 |
| `--platform` | 逗號分隔，只分析這些平台（比對 `platform` 欄，大小寫不拘） |
| `--out` | 輸出資料夾，預設 `out` |
| `--utc-offset` | 星期與時段用的時區，預設 `+08:00` |
| `--since` `--until` | 期間（含起不含迄）；只寫日期時以 `--utc-offset` 解讀 |
| `--include-reposts` | 納入轉發 |

## 報表內容

依平台（資料含平台時才出現）、依主題、依開頭類型、依星期、依三小時時段、分數最高的 10 篇，以及解讀限制。
主題與開頭類型是關鍵字規則判斷，不是語意理解；報表呈現相關，不代表因果。
