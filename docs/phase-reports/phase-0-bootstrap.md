# Phase 0：bootstrap

- 完成日期：2026-11-24
- 對應計畫：development-order.md 階段 0

## 範圍

讓已經建立好的專案鷹架（目錄、空模組、`config.py`、`db.py`、`docker-compose.yml`、`.env.example`、Alembic `0001_init` migration）真的能跑起來，不涉及新的架構決策：

- 補 `migrations/env.py`，讓 `alembic upgrade head` 能真正連上資料庫執行。
- 讓 `app/main.py` 的 `/healthz` 真的檢查 DB 連線，而不是回固定值。
- 產生 `uv.lock`，確認 `pyproject.toml` 的依賴能裝起來。
- 驗證 `docker compose up -d db` → `alembic upgrade head` 能建出 `article`、`click_event` 兩張表。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `migrations/env.py`（新增） | 連線設定重用 `app.config.settings.database_url`；`target_metadata = app.db.Base.metadata`；用別名匯入 `app.article.models`、`app.tracking.models` 讓模型註冊到 `Base.metadata`，供之後 autogenerate 使用。 |
| `app/main.py`（修改） | `/healthz` 改用 `Depends(get_db)` 跑一次 `SELECT 1`；成功回 200 `{"status":"ok"}`，例外回 503 `{"status":"error"}`。移除了原本沒用到的 `settings` import。 |
| `pyproject.toml`（修改） | 補 `[tool.hatch.build.targets.wheel] packages = ["app"]`——沒有這個設定 `uv run`/`uv sync` 會直接建置失敗（見「已知問題」）。 |
| `uv.lock`（新增） | `uv lock` 解析出 73 個套件。 |
| `.gitignore`（修改） | 加入 `.claude/`、`docs/superpowers/`（本地規劃文件，不進 repo 歷史）。 |

Commit：`79bb2ca` chore: wire up migrations, healthz DB check, and uv build config

## 驗證結果

- **環境準備**：這台機器原本沒裝 `uv`（只有裸 Python 3.12.6），用官方安裝腳本裝好；Docker Desktop 服務原本是 stopped，啟動後等待約數十秒 `docker info` 才有回應。
- **資料庫建表**：`docker compose up -d db` 健康檢查通過 → `uv run alembic upgrade head` 成功 → 用 `psql \dt` / `\d article` / `\d click_event` 確認兩張表、所有索引（含 pgvector 的 `idx_article_embedding` HNSW 索引）、`click_event → article` 外鍵都正確建立。
- **`/healthz` 行為**：
  - DB 正常：`GET /healthz` → `200 {"status":"ok"}`
  - `docker compose stop db` 後再打：`GET /healthz` → `503 {"status":"error"}`
  - 驗證完已恢復 DB 容器、關掉測試用的 uvicorn 進程。
- **`uv run pytest`**：`no tests ran`（collected 0 items）。符合預期——這階段是打通基礎設施，`tests/unit`、`tests/integration` 目前只有 `.gitkeep`，還沒有任何測試。
- **`uv run ruff check .`**：目前 **6 個錯誤**，皆非本階段改動造成：
  - `BLE001`（`except Exception` 太寬）：`app/enrichment/service.py:27`、`app/main.py:28`
  - `B008`（`Depends(...)` 寫在參數預設值）：`app/linebot/router.py:16`、`app/main.py:25`、`app/recommendation/factory.py:11`
  - `F841`（`messages` 變數賦值未使用）：`app/linebot/router.py:28`（因為 reply_message 呼叫還是 TODO，先留著變數）
  - 原本是 8 個，修掉了本階段自己造成的 2 個：`migrations/env.py` 的 `RUF100`（多餘 `noqa`）與 `app/main.py` 的 `F401`（未使用的 `settings` import）。

## 已知問題 / 後續事項

- **ruff 規則與 FastAPI 慣用寫法衝突**：`B008`（`Depends()` 放參數預設值）跟 `BLE001`（寬鬆 `except Exception`）在 PRD 給的程式碼片段（`recommendation/factory.py`、`enrichment/service.py`、`linebot/router.py`）裡本來就是既定寫法，但跟目前啟用的 ruff 規則衝突，會導致 `uv run ruff check .` 永遠不會乾淨。需要在後面某個階段決定要不要在 `pyproject.toml` 的 `[tool.ruff.lint]` 裡 `ignore = ["B008"]`（FastAPI 官方文件本身就建議忽略這條規則）並針對 retry 邏輯的 `except Exception` 加 `# noqa: BLE001` 或調整規則範圍。這不是本階段的範圍，先記錄下來，不擅自改動。
- **`pyproject.toml` 原本缺的 build 設定**：鷹架建立時 `[tool.hatch.build.targets.wheel]` 沒有指定 `packages`，導致 `uv run`/`uv sync` 完全無法執行（連 `import` 都會建置失敗）。這代表如果照 PRD 第 12 節原順序往下走，會在步驟 2 才第一次撞到這個問題；已在本階段修掉，後面階段不會再遇到。
- `.env` 裡的密鑰（`OPENAI_API_KEY`、`LINE_CHANNEL_SECRET` 等）目前是空字串，等到階段 3（enrichment）、階段 7（linebot）才需要填真的值。
