# 階段實作紀錄

## 規則

- 每完成一個階段，在本資料夾新增一份報告，檔名為 `phase-{N}-{slug}.md`（例如 `phase-1-article.md`）。
- 報告內容依下方範本填寫，完成後再進行下一階段。
- 不覆寫、不刪除舊報告；若階段需要補做或修正，另開 `phase-{N}-{slug}-followup.md` 記錄，保留歷史軌跡。

## 階段對照表

| 階段 | slug | 範圍 |
| --- | --- | --- |
| 0 | bootstrap | 鷹架可運行（migrations/env.py、/healthz、docker compose） |
| 1 | article | `article` 模組（repository/service/router） |
| 2 | ingestion | RSS 抓取、去重、admin 觸發 |
| 3 | enrichment | LLMClient 接上、狀態機與重試 |
| 4 | cache-search | MemoryCache、相關新聞查詢 |
| 5 | tracking-recommendation | click_event、LatestRecommender、/api/recommend |
| 6 | scheduler | APScheduler 排程 job |
| 7 | linebot | CommandRouter、flex、/callback |
| 8 | wrapup | Dockerfile、README、架構圖、驗收清單 |

## 報告範本

```markdown
# Phase {N}：{階段名稱}

- 完成日期：YYYY-MM-DD
- 對應計畫：development-order.md 階段 {N}

## 範圍

（這個階段實作了什麼，對照 development-order.md 的範圍描述）

## 主要變更

- 檔案／模組清單與重點說明

## 驗證結果

- 執行的驗證步驟與結果（對照 development-order.md 的「驗證」段落、PRD 第 11 節驗收標準）
- `uv run pytest` / `uv run ruff check .` 結果

## 已知問題 / 後續事項

（若有未解決的問題、延後處理的項目，或留給下一階段的注意事項）
```
