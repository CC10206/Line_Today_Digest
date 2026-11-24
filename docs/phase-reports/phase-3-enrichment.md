# Phase 3：enrichment

- 完成日期：2026-11-24
- 對應計畫：development-order.md 階段 3

## 範圍

接上真的 `LLMClient`，補狀態機與重試邏輯，對應 PRD 第 11 節 F2 兩項驗收標準。

## 範圍變更：LLM 供應商從 OpenAI 換成 Gemini

PRD 原本指定 OpenAI（`gpt-4o-mini` + `text-embedding-3-small`），但使用者決定改用 Gemini。這個切換點本來就是 PRD 第 5.2 節預留的擴充點（「LLM 供應商｜`enrichment/llm.py` 包一層 `LLMClient`｜換 Gemini 只改這個檔（注意 embedding 維度）」），所以只動了這一個檔案跟相關設定，其他模組（`enrichment/service.py`、`admin/router.py`）完全沒改。

| 檔案 | 說明 |
| --- | --- |
| `pyproject.toml` | 依賴 `openai` 換成 `google-genai`。 |
| `app/config.py` | `openai_api_key` 改名 `gemini_api_key`；`chat_model` 預設改 `gemini-3.5-flash-lite`；`embedding_model` 改 `gemini-embedding-001`；新增 `embedding_dimension: int = 1536`（要跟 migration 的 `vector(1536)` 對齊）。 |
| `.env` / `.env.example` | `OPENAI_API_KEY` 改名 `GEMINI_API_KEY`。 |
| `app/enrichment/llm.py` | 改寫 `LLMClient`：`enrich()` 用 `client.models.generate_content(..., config=GenerateContentConfig(response_mime_type="application/json", response_schema=EnrichResult))`；`embed()` 用 `client.models.embed_content(..., config=EmbedContentConfig(output_dimensionality=settings.embedding_dimension))`，確保輸出維度跟資料庫欄位一致。`get_llm_client()` 改用 `genai.Client(api_key=...)`。 |

**選模型踩的坑**：一開始設的 `gemini-2.5-flash` 直接被 API 回 404（新帳號已停用，官方訊息建議改 `gemini-3.8-flash`）；換了 `gemini-3.8-flash`、`gemini-3.6-flash`、`gemini-2.0-flash` 全部回 503（伺服器忙碌，`2.0-flash` 還額外被標成停用），最後用 `gemini-3.5-flash-lite` 才成功。最終設定選用這個目前實測可用的模型。

## 其他變更

| 檔案 | 說明 |
| --- | --- |
| `app/article/models.py` | `created_at` 補 `server_default=func.now()`。鷹架原本沒設定，導致任何用 `Article(...)` 建構子且沒手動帶 `created_at` 的呼叫都會因違反 NOT NULL 炸掉；階段 1/2 的驗證腳本都手動補了這個欄位才沒被抓到，寫這階段的測試腳本時才踩到。 |
| `app/article/repository.py` | 補 `claim_pending(limit)`：撈 `status='PENDING'`，依 `created_at` 由舊到新，取前 `limit` 筆。 |
| `app/article/service.py` | 補 `claim_pending(limit)`，轉呼叫 repository。 |
| `app/admin/router.py` | 新增 `POST /api/admin/enrich`，`verify_admin_token` 保護，`Depends(get_llm_client)` 注入真的 LLM client，呼叫 `enrichment.service.enrich_pending`。 |

## 驗證結果

- **重試/狀態機（fake LLMClient，不花錢）**：連續 3 次模擬失敗，驗證 `retry_count` 遞增、第 3 次後變 `FAILED`、`last_error` 正確記錄；測試前後都確認階段 2 抓到的真實文章沒被動到。
- **真實 Gemini API happy path**：直接呼叫 `enrich_pending(db, llm)`（跟 `/api/admin/enrich` 底層呼叫同一個函式，為控制成本沒有額外繞一次 HTTP），處理 1 篇真實文章（id=7），結果：
  - `status` → `ENRICHED`
  - `summary`：繁中 3 句摘要
  - `category`：`國際`（合法分類）
  - `keywords`：5 個關鍵字
  - `embedding`：`vector_dims()` 確認正好 1536 維，跟 migration 欄位定義一致
  - `enriched_at` 有正確寫入時間
- **真實 503 錯誤下的 retry 機制**：中途踩到的 503/404 錯誤也順便驗證了一次 retry 邏輯在真實失敗下的行為（`retry_count` 正確遞增、沒有卡住整個流程），每次測試後都把文章重設回乾淨的 `PENDING` 狀態，不留測試痕跡。
- 目前 DB：70 篇文章裡 1 篇 `ENRICHED`、69 篇 `PENDING`（留給之後階段繼續測試/使用）。
- `uv run pytest`：`no tests ran`。`uv run ruff check .`：3 個錯誤，跟階段 2 結束時一樣（已知問題，沒有新增）。

## 已知問題 / 後續事項

- `gemini-3.5-flash-lite` 是目前**實測可用**的選擇，但 Gemini 這幾個 flash 系列模型最近變動頻繁（短時間內 2.0/2.5 被下架、3.6/3.8 滿載），之後正式使用前建議再次確認這個模型是否還可用，或改用當時最穩定的版本。
- 跟階段 0 的 ruff 已知問題一樣：`BLE001`（`enrichment/service.py`、`main.py` 的 `except Exception`）跟 `F841`（`linebot/router.py`）還沒處理，數量沒有增加。
