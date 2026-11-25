# Phase 7：linebot

## 範圍

`CommandRouter`、`flex.py`、`/callback` 接上真的 `reply_message`，對應 PRD 第 9 節的互動表與第 11 節 F4 驗收標準。

## 主要變更

| 檔案 | 說明 |
| --- | --- |
| `app/linebot/flex.py`（新增內容） | `article_bubble(article)` 組單張卡片（標題/摘要/分類、「看原文」`URIAction`、「相關新聞」`PostbackAction` data=`action=related&id={id}`）；`article_carousel(articles)` 包成 `FlexMessage`；`text_message(text, with_quick_reply)` 一般文字訊息，`with_quick_reply=True` 時附「今日新聞/科技/財經/推薦」快速選項。 |
| `app/linebot/commands.py`（新增內容） | `CommandRouter`：建構子注入 `ArticleService`、`SearchService`、`Recommender`、`TrackingService`（純 DI，不碰 LINE API，可單獨測試）。`on_text(user_id, text)` 依輸入分派「今日新聞/分類名稱/推薦/其他」；`on_postback(user_id, data)` 處理 `action=related` 並寫入 `click_event`。`get_command_router()` 是 FastAPI dependency factory。 |
| `app/linebot/router.py` | `/callback` 補上真的 `await line_api.reply_message(...)`；新增 `init_line_api()`/`close_line_api()` 管理共用的 `AsyncApiClient` 生命週期。 |
| `app/main.py` | `lifespan` 啟動時呼叫 `init_line_api()`、關閉時呼叫 `close_line_api()`；掛上 `linebot_router`。 |

**跟 PRD 第 9 節範例程式碼的差異**：PRD 給的 `/callback` 範例是 `cmd.on_text(ev.message.text.strip())`（不傳 `user_id`），但「推薦」功能需要 `line_user_id` 才能呼叫 `Recommender.recommend(line_user_id, limit)`，所以把 `on_text` 簽名改成 `on_text(user_id, text)`，呼叫端也跟著改。這是範例程式碼的疏漏，不是刻意偏離設計。

## 過程中修掉的兩個真 bug

1. **`on_postback` 的寫入順序錯了**：一開始在確認文章存在「之前」就呼叫 `tracking.record()` 寫 `click_event`。如果 postback 帶的 `id` 根本不存在（例如卡片過期、資料被清掉），`click_event.article_id` 的外鍵會直接炸 `IntegrityError`，變成整個請求 500，而不是 PRD 要的「目前沒有新聞，稍後再試」。改成先呼叫 `search.related()` 確認文章存在，成功才記錄點擊。
2. **`AsyncApiClient` 的建構時機/生命週期**：
   - 一開始在 module 載入時（`import` 階段）就建立 `AsyncApiClient`，但它底層會立刻建 `aiohttp.TCPConnector`，需要「當前有在跑的 event loop」，import 時還沒有 loop，直接炸 `RuntimeError: no running event loop`。
   - 改成用 FastAPI dependency 延遲建立後，又踩到第二個坑：dependency 函式如果宣告成同步 `def`，FastAPI 會丟到另一個 worker thread 執行，那個 thread 也沒有 event loop，一樣炸。改成 `async def` 才解決。
   - 解決上面兩個問題後，發現每個 request 都新建一個 `AsyncApiClient`、用完沒關閉，log 出現「Unclosed client session」洩漏警告。最終改成在 `lifespan` 啟動時建一個共用的 `AsyncApiClient`、關閉時 `await client.close()`，dependency 只回傳包著共用 client 的 `AsyncMessagingApi`。

## 驗證結果

- **`CommandRouter` 邏輯**（直接呼叫，不經 HTTP，不需要真的 LINE 憑證）：
  - 「今日新聞」/分類名稱「國際」/「推薦」都正確回傳 `FlexMessage`
  - 其他文字回 `TextMessage` + `QuickReply`
  - postback `action=related&id=7`（真實存在且 `ENRICHED` 的文章）：正確回應（目前因為只有 1 篇 `ENRICHED`，`related` 結果是空的，所以回「查無資料」文字，不是 bug）
  - 確認 `click_event` 正確寫入（`line_user_id`、`article_id`、`action` 都對），測試完刪除
  - postback `action=related&id=999999`（不存在的文章）：正確回「查無資料」文字、**不拋例外**（這就是上面修的 bug 的回歸驗證）
- **真實 HTTP `/callback` 端點**（簽章用目前 `.env` 的 `LINE_CHANNEL_SECRET` 計算 HMAC-SHA256，手刻一個符合 v3 schema 的 webhook payload）：
  - 錯誤簽章 → `400 {"detail":"invalid signature"}`
  - 正確簽章 → 通過驗證、事件被正確解析、分派到 `CommandRouter`，最後卡在呼叫真的 LINE Reply API 那一步，回 `401 Unauthorized`（因為 `.env` 的 `LINE_CHANNEL_ACCESS_TOKEN` 目前是空的，這是預期中的失敗點，不是我們程式碼的問題——代表簽章驗證、事件解析、command 分派這幾層都是對的）。
  - 確認「Unclosed client session」警告在修完生命週期問題後不再出現。
- `uv run pytest`：`no tests ran`。`uv run ruff check .`：**2 個錯誤**（比階段 6 少一個——`linebot/router.py` 原本的 `F841` 因為現在真的用到 `messages` 變數而自然消失）。

## 真實手機測試（後續補做，已完成）

使用者自己申請了 LINE Developers Console 的 Messaging API channel（`LINE_CHANNEL_SECRET`/`LINE_CHANNEL_ACCESS_TOKEN` 填進 `.env`），用 `ngrok http 8000` 把本機 `/callback` 暴露成公開網址設定到 LINE 的 Webhook URL（注意：Webhook URL 要在 **LINE Developers Console** 的 Messaging API 分頁設定、打開 `Use webhook`，不是在 **LINE Official Account Manager** 那個不同的後台——兩者一開始搞混了一次）。

- **ngrok 免費方案的瀏覽器警告頁**：用瀏覽器打開 ngrok 網址會跳一個「你即將造訪...」的警告頁（`ERR_NGROK_6024`），一開始擔心 LINE 的 webhook 呼叫也會被擋。實測確認這個警告頁只針對瀏覽器 GET 請求，POST 請求（LINE webhook 用的方法）會直接穿透到我們的 app，不受影響。
- 測試期間手動把 `.env` 的 `ENABLE_SCHEDULER` 設成 `false`，避免背景排程在測試這段時間自動打真的 Gemini API（見下方「已知問題」的教訓）。
- **手機實測結果**：
  - 傳「今日新聞」→ 收到 Flex carousel（當時 5 篇 `ENRICHED`）
  - 點卡片「看原文」→ 正確開啟原始新聞網址
  - 點卡片「相關新聞」→ 收到相關新聞卡片，`click_event` 資料庫確認真的寫入（真實 `line_user_id`、正確的 `article_id`、`action='RELATED'`），對兩篇不同文章各點了一次都正確記錄
  - 簽章錯誤 → `400`（這項先前已經用手刻簽章驗證過，這次手機測試沒有另外重複）

## 已知問題 / 後續事項

- **背景排程意外跑了真的 API**：階段 7 前段測 webhook 簽章時忘記把 `ENABLE_SCHEDULER` 設成 `false`，幾次重啟 app 加起來的時間超過 60 秒，背景 enrich job 自動跑了，多處理了 4 篇真實文章（成本可忽略，用的是 `gemini-3.5-flash-lite`）。已記錄為個人習慣修正：以後只要 app 可能跑超過一分鐘，啟動前就先確認 `ENABLE_SCHEDULER=false`。
- **相關新聞的品質問題**（後續發現並修掉）：一開始只有 5 篇 `ENRICHED` 文章時以為「相關新聞」正常，後來把剩下 65 篇 `PENDING` 全部批次跑完 enrichment（共 70 篇，花了幾輪呼叫等 Gemini 免費額度「每分鐘 15 次請求」重置）、人工檢查相似度分數後，發現非常不相關的文章（例如一篇「帕金森氏症治療」的健康新聞）也會被硬湊出 3 篇「相關新聞」，相似度只有 0.52-0.54。修法跟後續記錄在 [phase-4-cache-search-followup.md](phase-4-cache-search-followup.md)。
