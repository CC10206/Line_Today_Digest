# Phase 8：wrapup

## 範圍

`Dockerfile` 驗證、README 補完、架構圖、跑完 PRD 第 11 節全部驗收清單。development-order.md 的最後一個階段。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `docker-compose.yml` | `app` 服務加 `environment.DATABASE_URL`，覆寫成 `db:5432`（容器之間要用 compose 服務名稱當主機名，`.env` 裡給本機 `uv run uvicorn` 開發用的 `localhost:5432` 在容器裡連不到）。 |
| `docs/architecture.svg`（新增） | 手刻的系統架構圖（PRD 原本要 `.png`，改用 SVG：GitHub 原生支援、向量圖品質更好、檔案更小）。畫 RSS 來源 → Ingestion → DB ← Enrichment、APScheduler 驅動、DB → API 模組 → Admin API / LINE Bot → LINE 使用者。 |
| `README.md` | 架構圖從「待補」換成實際嵌入 `docs/architecture.svg`。 |
| `app/common/schemas.py` | `ArticleSummary`、`CategoryCount` 補 `json_schema_extra` 範例（對照 PRD 第 7 節的 JSON 範例），讓 Swagger UI 顯示真的範例資料，不是只有型別預設值。 |
| `app/main.py`、`app/enrichment/service.py` | 針對兩個刻意的寬鬆 `except Exception`（`/healthz` 降級、enrichment 重試邏輯）加上精準的 `# noqa: BLE001`，`ruff check` 現在**全部通過**，不是整個專案停用這條規則。 |

## PRD 第 11 節驗收清單（最終狀態）

- [x] F1：`POST /api/admin/ingest` 後 DB 出現文章；重複執行不產生重複 `url`（階段 2 驗證，真實 RSS）
- [x] F1：其中一個 RSS 來源無法連線時，其他來源仍正常抓取（階段 2 驗證）
- [x] F2：`POST /api/admin/enrich` 後文章變 `ENRICHED`，有 3 句摘要、合法分類、embedding（階段 3 驗證，真實 Gemini API，全部 70 篇文章都處理過）
- [x] F2：LLM 拋例外時 `retry_count` 遞增，3 次後變 `FAILED`（階段 3 用 fake `LLMClient` 驗證，另外也在真實 503/404 錯誤下驗證過一次）
- [x] F3：`/api/articles` 分頁、分類篩選正確；不存在的 id 回 404 + 錯誤碼（階段 1 驗證）
- [x] F3：`/related` 不含自己、依相似度排序、只含 7 天內文章（階段 4 用手刻 embedding 驗證；另外階段 7 followup 加了相似度門檻，用全部 70 篇真實資料驗證過品質）
- [x] F3：`/docs` 可以直接打所有 `/api` 端點，每個端點都有說明與回應範例（這階段補上 `ArticleSummary`/`CategoryCount` 的 Swagger 範例，之前只有型別預設值）
- [x] F4：手機傳「今日新聞」收到 5 張卡片；點「相關新聞」收到 3 張並寫入 `click_event`（階段 7 真機測試）
- [x] F4：簽章錯誤的 webhook 請求回 400（階段 7 驗證）
- [x] F5：乾淨環境 `cp .env.example .env` → 填密鑰 → `docker compose up` 即可運作（這階段驗證，`app` 容器 build、連 DB、`alembic upgrade head`、`/healthz`、`/api/categories`、`/docs` 都正常；**但不是從全新空資料庫測的**，見下方已知問題）
- [x] README 含架構圖、啟動步驟、API 清單、Future work（這階段補架構圖）
- [ ] README 含 demo 影片連結（**沒做**，需要使用者自己錄一段操作影片）
- [x] 鷹架：`uv run ruff check .` 無錯誤（這階段修到全線通過）
- [~] 鷹架：`uv run pytest` 全綠（目前是 `collected 0 items`，技術上沒有失敗，但也沒有任何自動化測試——整個專案從階段 0 到現在都是用手動腳本 + 真實資料驗證，沒有寫 pytest 測試檔案，這是貫穿全專案的已知取捨，不是這階段特有的問題）
- [x] 鷹架：`CACHE_BACKEND` 與 `RECOMMENDER` 可切換且有預設值（鷹架階段就有，factory.py 的 `match` 語句）

## 已知問題 / 後續事項

1. **Docker 驗證不是從全新空資料庫測的**：跟使用者確認過，為了不損失目前 70 篇已處理好的文章（重做要再花 API 成本跟時間），選擇跳過「清空 db volume、從零驗證 `alembic upgrade head` 自動建表」這個最嚴格版本。現有證據（階段 0 host 端從零建表成功 + 這階段容器內對已有 schema 跑 migration 成功）合起來讓人有信心，但沒有「容器 + 全新空庫」這個精確組合的直接證據。
2. **沒有自動化測試套件**：整個專案用手動腳本 + 真實資料驗證取代 `pytest`，`uv run pytest` 目前且會持續是 0 個測試。如果之後要交作品集／面試，可能需要考慮至少補幾個關鍵路徑的自動化測試（例如 `enrich_pending` 的重試狀態機、`/related` 的排序邏輯），但這是全專案規模的決定，不是這階段該自行決定的事。
3. **Demo 影片沒有**：README 的連結欄位還是待補，需要使用者自己錄一段「`docker compose up` → Swagger UI 打 API → LINE 手機操作」的畫面。
