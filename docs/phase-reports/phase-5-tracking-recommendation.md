# Phase 5：tracking-recommendation

## 範圍

`click_event` 寫入、`Recommender` Protocol 跟 `LatestRecommender`（PRD 第 5.2 節已給程式碼）、`GET /api/recommend`。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `app/tracking/models.py` | `created_at` 補 `server_default=func.now()`——跟階段 3 修 `Article.created_at` 一樣的鷹架缺陷，`ClickEvent` 也有，這次順手一起修掉，沒有等它在測試時才炸出來。 |
| `app/tracking/service.py`（新增內容） | `TrackingService.record(line_user_id, article_id, action)`，直接 `db.add` + `commit`。 |
| `app/recommendation/router.py`（新增） | `GET /api/recommend?lineUserId=&limit=5`，接上 `recommendation/factory.py` 的 `get_recommender`。PRD 樹狀圖沒有明確指定這個端點放哪，照 development-order.md 階段 5 的決定獨立開檔案（跟 `admin` 一樣符合「依功能切模組」）。 |
| `app/main.py` | 掛上 `recommendation_router`。 |

`recommendation/base.py`、`latest.py`、`factory.py` 都是 PRD 第 5.2 節已經給的程式碼，這階段沒有修改，只是確認它們能正常運作。

## 驗證結果

- **`TrackingService.record`**：直接呼叫寫入 `click_event`，用原始 SQL 查回確認 `line_user_id`、`article_id`、`action`、`created_at`（DB 預設值）都正確；測試完刪除該筆。
- **`GET /api/recommend`**：帶 `lineUserId`、`limit=5` → 回目前唯一一篇 `ENRICHED` 的文章（`RECOMMENDER=latest`，等同最新新聞，符合 PRD 定義）；不帶 `lineUserId` → 422。
- `GET /openapi.json` 的 `paths` 確認 `/api/recommend` 有掛上。
- `uv run pytest`：`no tests ran`。`uv run ruff check .`：3 個錯誤，跟階段 4 結束時一樣（已知問題，沒有新增）。

## 已知問題 / 後續事項

- 目前只有 1 篇 `ENRICHED` 文章，`/api/recommend` 回傳內容單一，等之後處理更多文章後效果會更明顯。
- `click_event` 目前沒有任何寫入來源——要等階段 7（linebot）使用者點「相關新聞」時才會真的呼叫 `TrackingService.record`。
