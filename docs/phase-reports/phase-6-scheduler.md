# Phase 6：scheduler

## 範圍

在 FastAPI lifespan 啟動 APScheduler，背景跑 `ingestion`（每 `settings.ingest_interval_minutes`，預設 30 分）跟 `enrichment`（每 60 秒）兩個 job，受 `ENABLE_SCHEDULER` 控制。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `app/ingestion/jobs.py`（新增內容） | `run_ingest_job()`：開一個新的 `SessionLocal`，呼叫 `ingestion.service.ingest(db)`。 |
| `app/enrichment/jobs.py`（新增內容） | `run_enrich_job()`：開一個新的 `SessionLocal`，呼叫 `enrichment.service.enrich_pending(db, llm)`。 |
| `app/main.py` | `lifespan` 補完：`settings.enable_scheduler` 為真時建立 `BackgroundScheduler`，掛上兩個 `interval` trigger 的 job（`id="ingest"`/`id="enrich"`），`yield` 後（app 關閉時）呼叫 `scheduler.shutdown()`。 |

兩個 job 呼叫的是跟 `/api/admin/ingest`、`/api/admin/enrich` 完全相同的 service 函式，沒有重複邏輯。

## 驗證結果

- **排程註冊邏輯**（mock `BackgroundScheduler`，不等真的間隔觸發、不花錢）：
  - `ENABLE_SCHEDULER=true` 時：直接呼叫 `lifespan(app)`，驗證 `BackgroundScheduler` 有被建立、`add_job` 被呼叫 2 次，`id` 分別是 `ingest`/`enrich`，`ingest` 的 trigger 參數是 `minutes=settings.ingest_interval_minutes`、`enrich` 是 `seconds=60`，且 `scheduler.start()`/`shutdown()` 都正確呼叫一次。
  - 暫時把 `settings.enable_scheduler` 設成 `False` 重跑：驗證完全不會建立 `BackgroundScheduler`。
- **真實啟動煙霧測試**：用 `uv run uvicorn` 真的啟動一次 app（`ENABLE_SCHEDULER=true`，預設值），打 `/healthz` 確認 200，立刻關閉——確認 APScheduler 在真實環境下可以正常建立、沒有 import 或啟動期例外，但沒有等到任何 job 真的被觸發（60 秒的 enrich job 會打到真的 Gemini API，故意避開）。
- `uv run pytest`：`no tests ran`。`uv run ruff check .`：3 個錯誤，跟階段 5 結束時一樣（已知問題，沒有新增）。

## 已知問題 / 後續事項

- 這階段沒有驗證「排程真的在 30 分鐘/60 秒後觸發」這個時間層面的行為，只驗證了「設定正確註冊」跟「啟動不出錯」。要驗證真的定時觸發，之後可以把 `ingest_interval_minutes`/enrich 間隔暫時調很短跑一段時間觀察，但這樣 enrich job 會真的打 Gemini API 產生費用，目前先不做。
