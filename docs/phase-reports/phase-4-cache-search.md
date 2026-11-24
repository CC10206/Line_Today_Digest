# Phase 4：cache-search

## 範圍

`MemoryCache` 實作、相關新聞查詢端點，對應 PRD 第 11 節「`/related` 不含自己、依相似度排序、只含 7 天內文章」驗收標準。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `app/cache/memory.py`（新增內容） | `MemoryCache` 實作 `Cache` Protocol：`dict[key] = (value, expires_at)`，`get()` 過期自動清掉並回 `None`。 |
| `app/cache/factory.py`（新增） | `get_cache()`：依 `settings.cache_backend` 切換（目前只有 `"memory"`，`"redis"` 留給 Phase 2）。`MemoryCache` 用模組層級單例，確保同一份記憶體快取在不同請求間共用，不會每次注入都是新的空字典。 |
| `app/article/router.py` | 新增 `GET /api/articles/{id}/related?limit=3`（`le=10`），接上 `SearchService`；`get_search_service` dependency 組合 `db` + `cache`。`search/service.py` 本身用的是 PRD 第 7 節已經給的程式碼，這階段沒有改它，只是把它接上路由。 |

## 驗證結果

- **手刻 embedding 驗證排序/排除/時間窗**（不用再花錢打 LLM）：建 5 篇測試文章——目標文章、一篇向量相近、一篇向量很不相近、一篇向量相近但發布於 10 天前、一篇向量相近但狀態是 `PENDING`。呼叫 `SearchService.related()` 驗證：
  - 回傳結果不含目標文章自己
  - 10 天前的文章被 7 天窗口排除
  - `PENDING` 狀態的文章被排除
  - 排序正確：最相似的排第一、最不相似的排最後
  - 測試完全部刪除，不留痕跡。
- **真實 HTTP 端點**：`GET /api/articles/7/related?limit=3` → 回空陣列（目前真實資料裡只有這 1 篇 `ENRICHED`，沒有其他候選本來就該是空的，不是 bug）；`GET /api/articles/999/related` → 404 + 錯誤碼；`/openapi.json` 確認 `/api/articles/{article_id}/related` 有掛上。
- `uv run pytest`：`no tests ran`。`uv run ruff check .`：3 個錯誤，跟階段 3 結束時一樣（已知問題，沒有新增）。

## 已知問題 / 後續事項

- 沒有寫 PRD 提到的 testcontainers 自動化測試（跟前面幾個階段一致，這個專案目前走手動驗證，不寫自動化測試）；用手刻向量的腳本涵蓋了同樣的正確性驗證範圍。
- 目前真實資料只有 1 篇 `ENRICHED`，`/related` 的「排序正確」在真實資料上還沒機會被完整驗證過（只在手刻資料上驗證過）；等之後處理更多文章、有多篇 `ENRICHED` 後可以再用真實資料驗證一次。
