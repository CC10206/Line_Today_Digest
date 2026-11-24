# Phase 1：article

## 範圍

填好 `article` 模組（repository、service、router、例外處理），讓 PRD 第 7 節的三個端點可用（`GET /api/articles`、`GET /api/articles/{id}`、`GET /api/categories`）。`/related` 屬於階段 4（cache + search）範圍，這階段不做。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `app/common/schemas.py` | `ArticleSummary` 加上 `alias_generator=to_camel` + `populate_by_name=True`，讓 JSON 輸出符合 PRD 第 7 節範例的 camelCase（`imageUrl`、`publishedAt`）；補 `from_row(article, similarity=None)` classmethod；新增 `CategoryCount` schema。 |
| `app/common/errors.py` | `AppError` 加 `status_code` 類別屬性；新增 `register_exception_handlers(app)`，統一把 `AppError` 轉成 `{"code","message"}` JSON。 |
| `app/article/repository.py` | `ArticleRepository`：`list_enriched(category, page, size)`（只回 `ENRICHED`，依 `published_at DESC` 分頁）、`get(id)`、`category_counts()`（`GROUP BY category`）。`claim_pending`/`upsert_on_conflict` 留給階段 3/2。 |
| `app/article/service.py` | `ArticleService`：`list_articles`、`get`（找不到或非 `ENRICHED` 丟 `ArticleNotFound`）、`latest_enriched`（給階段 5 的 `LatestRecommender` 用）、`categories`（固定 10 個分類都回傳，沒文章的補 0）。 |
| `app/article/router.py` | 掛上三個端點，`size` 加 `le=100` 上限；404 走 `responses` 註記。 |
| `app/main.py` | 註冊 `register_exception_handlers`、掛上 `article_router`。 |
| `pyproject.toml` | `[tool.ruff.lint] ignore = ["B008"]`（見「已知問題」）。 |

## 驗證結果

手動插入 4 筆測試資料（3 篇 `ENRICHED`：科技×2、財經×1；1 篇 `PENDING`），啟動 `uv run uvicorn` 後驗證：

- `GET /api/articles` → 回 3 篇 `ENRICHED`（不含 `PENDING` 那篇），依 `published_at` 新到舊排序。
- `GET /api/articles?category=科技` → 只回 2 篇科技新聞。
- `GET /api/articles/1` → 回單篇，JSON key 為 `imageUrl`/`publishedAt`（camelCase），符合 PRD 第 7 節範例格式。
- `GET /api/articles/4`（`PENDING` 狀態）→ `404 {"code":"ARTICLE_NOT_FOUND","message":"article 4 not found"}`
- `GET /api/articles/999`（不存在）→ 同上 404 + 錯誤碼
- `GET /api/categories` → 固定 10 個分類都有回傳，科技=2、財經=1、其餘=0
- `GET /openapi.json` 的 `paths` 包含 `/api/articles`、`/api/articles/{article_id}`、`/api/categories`、`/healthz`，`/docs` 可以打通。
- 驗證完刪除測試資料、關掉測試用 uvicorn 進程。
- `uv run pytest`：`no tests ran`（collected 0 items），符合預期（還沒開始寫自動化測試）。
- `uv run ruff check .`：3 個錯誤，跟階段 0 結束時一樣，都是已知問題（見下）。新寫的檔案沒有引入新的錯誤類型。

## 已知問題 / 後續事項

- **修了 `pyproject.toml` 的 ruff 設定**：`B008`（`Depends()` 寫在參數預設值）在這階段從 3 處變成 7 處，已加 `ignore = ["B008"]`（FastAPI 官方文件本身建議忽略這條規則），之後所有 router 都不會再被這條規則擋。`BLE001`（寬鬆 `except Exception`，2 處：`enrichment/service.py`、`main.py` 的 `/healthz`）跟 `F841`（`linebot/router.py` 的 `messages` 變數，等階段 7 接上真的 `reply_message` 就會用到）維持不動，數量少、之後會自然解決。
- **踩到一個 Python 陷阱**：`ArticleService` 一開始把列表方法命名為 `list`，導致 class body 裡後面方法簽名的 `list[ArticleSummary]`（內建型別）被自己的方法蓋掉，炸出 `TypeError: 'function' object is not subscriptable`。已改名為 `list_articles` 解決；之後新增 service 方法時要避免用 `list`/`dict`/`str` 等內建型別名稱當方法名。
- `/api/recommend` 會用到這裡的 `latest_enriched`，等階段 5 再接上。
