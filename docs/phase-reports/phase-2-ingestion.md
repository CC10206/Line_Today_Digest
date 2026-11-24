# Phase 2：ingestion

## 範圍

RSS 抓取、HTML 清理、依 `url` 去重、admin 手動觸發，對應 PRD 第 11 節 F1 兩項驗收標準。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `app/config.py` | `settings.feeds` 從佔位符換成實際驗證過的 RSS 網址：中央社 `https://feedx.net/rss/cna.xml`、自由時報 `https://news.ltn.com.tw/rss/all.xml`。這兩個網址是上網查證後用 WebFetch 實際抓過、確認是有效 RSS 的（不是憑記憶猜的）。 |
| `app/article/repository.py` | 補 `upsert_on_conflict(rows)`：用 Postgres `INSERT ... ON CONFLICT (url) DO NOTHING RETURNING id`，回傳實際插入筆數；`status`/`retry_count`/`created_at` 這些欄位不用在 Python 端填，因為 migration 的 SQL 已經用 `DEFAULT` 設好了。 |
| `app/ingestion/fetcher.py`（新增內容） | `fetch_all()` 逐一呼叫 `feedparser.parse`，單一來源例外時記 log 並回空清單，不影響其他來源；用 `BeautifulSoup` 清掉 `entry.summary` 的 HTML 標籤；`published_at` 從 `entry.published_parsed` 轉成 UTC datetime，缺少就跳過該筆。 |
| `app/ingestion/service.py`（新增內容） | `ingest(db)` 整合 fetch + upsert，回傳每個來源的 `fetched`/`inserted` 統計並記 log。 |
| `app/admin/router.py`（新增內容） | `POST /api/admin/ingest`，用共用的 `verify_admin_token`（比對 header `X-Admin-Token` 跟 `settings.admin_token`）當 dependency，401 時不給進。 |
| `app/main.py` | 掛上 `admin_router`。 |

## 驗證結果

- `GET /healthz` → 200（基礎設施沒壞）。
- `POST /api/admin/ingest` 不帶 token → 422（FastAPI 必填 header 缺失）；帶錯 token → `401 {"detail":"invalid admin token"}`。
- 帶正確 token 第一次呼叫 → `{"fetched":{"cna":30,"ltn":40},"inserted":{"cna":30,"ltn":40}}`，DB 裡 `source` 分組統計確認 `cna=30`、`ltn=40`，共 70 筆。
- **立刻再呼叫一次** → `{"fetched":{"cna":30,"ltn":40},"inserted":{"cna":0,"ltn":0}}`，確認 `url` 去重生效，不會重複插入。
- **單一來源失敗不影響其他來源**：寫一個暫時腳本把其中一個 feed 換成不存在的網域（`https://this-domain-does-not-exist-todaydigest.invalid/rss.xml`），直接呼叫 `fetch_all()` 驗證：壞掉的來源回空清單、沒有拋例外，另一個來源（`ltn`，40 篇）正常抓到。
- 這次**沒有刪除**驗證時抓到的 70 篇真實新聞（跟階段 1 塞的假測試資料不同，這些是從真實 RSS 抓到的真內容，狀態是 `PENDING`，剛好可以留給階段 3 enrichment 測試用）。
- `uv run pytest`：`no tests ran`（collected 0 items）。
- `uv run ruff check .`：3 個錯誤，跟階段 1 結束時完全一樣（已知問題，沒有新增）。

## 已知問題 / 後續事項

- 目前 DB 裡有 70 篇 `PENDING` 的真實新聞，階段 3（enrichment）會直接拿這批資料測試 LLM 處理流程。
- `image_url` 目前一律填 `None`——RSS 的 `<item>` 不一定有結構化的圖片欄位（要看各來源有沒有 `media:content`/`enclosure`），這次沒有花額外力氣去解析，之後如果 LINE Bot 卡片想顯示縮圖，可以再回來加。
- PRD 非功能需求提到「使用 logging（JSON 格式）」，目前 `fetcher.py`/`ingestion/service.py` 用的是標準 `logging`，還沒有設定 JSON 格式化（這是全專案共用的 logging 設定，不是這個模組單獨的事），先用標準文字 log，之後若要讓 log 進到監控系統（Phase 2 的 Prometheus/Grafana）再一起處理。
