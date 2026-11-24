# PRD｜TodayDigest：AI 新聞摘要 + 相關新聞 + LINE Bot（MVP）

## 1. 概述

TodayDigest 是一個「迷你版 LINE TODAY」後端服務（Python / FastAPI）：自動抓取新聞，用 LLM 產生摘要與分類，以 pgvector 找語意相關新聞，並透過 LINE Bot 讓使用者在手機上瀏覽。用途是作為 LINE 2027 TECH FRESH（LINE TODAY Backend/Applied AI）實習申請的作品。

**互動模式**：這是純後端服務，沒有自製網頁或手機 App。

- **一般使用者**在 LINE 聊天室跟 Bot 互動：傳文字或點卡片按鈕 → LINE 把事件送到後端 webhook → 後端從 PostgreSQL 讀出「已由 AI 預先處理好」的摘要，組成 Flex 卡片回覆。卡片顯示摘要；點「看原文」會開啟新聞來源網站。
- **面試官 / 開發者**開 FastAPI 自動產生的 Swagger UI（`/docs`），直接打 API 看 JSON 回傳。
- LLM 只在背景排程裡呼叫，使用者點擊時不會即時叫 LLM；MVP 的「快取」就是這些存在 DB 的 AI 結果，加上記憶體內的相關新聞快取；Redis 是 Phase 2 才接上。

**目標**

- 一條端到端可 demo 的主線：RSS → AI 處理 → 相關新聞 API → LINE Bot。
- 展示 Python 後端能力（FastAPI、SQLAlchemy、測試、容器化），加上 LLM、Embedding、向量檢索的實際應用。
- 鷹架一次到位：Phase 2 功能（推薦、Redis、監控、CI、部署）都有預留位置，之後只需「填入實作」，不需重構。

**非目標**

- 不爬取 LINE TODAY 網站本身（只用公開 RSS）。
- 不做使用者帳號系統、前端網頁或手機 App。
- 不追求大規模效能，資料量以數百到數千篇新聞為準。
- MVP 不寫 Java；Spring Boot 版本列為 Phase 2 後的選做項目（見第 13 節）。

## 2. 範圍

MVP 只做 F1–F5；Phase 2 的功能在鷹架中只建立介面或設定開關（見第 5 節），不實作。

| ID | 功能 | 階段 | 鷹架內的狀態 |
| --- | --- | --- | --- |
| F1 | RSS 抓取、去重、存檔（排程每 30 分鐘） | MVP | 完整實作 |
| F2 | LLM 摘要、分類、關鍵字 + Embedding | MVP | 完整實作 |
| F3 | 新聞列表 / 單篇 / 相關新聞 API + Swagger UI | MVP | 完整實作 |
| F4 | LINE Bot：「今日新聞」卡片、點擊看相關新聞 | MVP | 完整實作 |
| F5 | Docker Compose 一鍵啟動、README、架構圖 | MVP | 完整實作 |
| P1 | 點擊紀錄 + 個人化推薦 `/recommend` | Phase 2 | 點擊事件已寫入 DB；`Recommender` Protocol + 「最新優先」預設實作 |
| P2 | Redis 快取 | Phase 2 | `Cache` 介面已接上，預設用記憶體實作（`CACHE_BACKEND=memory`） |
| P3 | Prometheus / Grafana 監控 | Phase 2 | `/healthz` 已有，缺 metrics exporter |
| P4 | GitHub Actions CI + 定時抓取 | Phase 2 | `pytest` 可在本地跑，缺 workflow 檔 |
| P5 | Render 部署 | Phase 2 | Dockerfile 已備妥 |
| P6 | Spring Boot 版本（選做） | Phase 2 後 | README 的 Future work 已說明，API 契約共用 |

## 3. 使用者故事

1. 作為 LINE 使用者，我傳「今日新聞」給 Bot，就能看到 5 則最新新聞的 3 句摘要卡片。
2. 作為 LINE 使用者，我點卡片上的「相關新聞」，就能看到 3 則主題相近的報導。
3. 作為 LINE 使用者，我傳「科技」等分類名稱，就能只看該分類的新聞。
4. 作為開發者 / 面試官，我執行 `docker compose up` 後，能在 Swagger UI 呼叫所有 API。
5. 作為系統，我每 30 分鐘抓一次 RSS，新文章在 5 分鐘內完成 AI 處理；失敗的文章會重試，不會卡住整批。

## 4. 系統架構與技術棧

單一 FastAPI 應用 + 一個 PostgreSQL。抓取與 AI 處理在背景排程（APScheduler）執行，彼此透過文章狀態（PENDING → ENRICHED）銅接；API 與 LINE Bot 只讀已處理好的資料，所以 webhook 不會被 LLM 延遲拖慢。

&#91;embedded content: 系統架構 · 1 個應用、5 個模組、1 個資料庫\]

| 層 | 技術 |
| --- | --- |
| 語言 / 框架 | Python 3.12、FastAPI、Uvicorn、uv（套件管理） |
| 設定 | pydantic-settings（讀 `.env`） |
| AI | `openai` SDK（Structured Outputs + Pydantic、embeddings） |
| 資料庫 | PostgreSQL 16 + pgvector、SQLAlchemy 2、`pgvector` Python 套件、Alembic |
| 排程 | APScheduler（與 FastAPI lifespan 一起啟動） |
| RSS / HTML | feedparser、BeautifulSoup |
| LINE | `line-bot-sdk`（v3） |
| API 文件 | FastAPI 內建 Swagger UI（`/docs`） |
| 測試 / 品質 | pytest、testcontainers-python、ruff |
| 執行環境 | Docker、Docker Compose、ngrok（本地 webhook） |

## 5. 專案鷹架

採用「依功能切模組」的單體 FastAPI 專案。每個模組只透過 `service.py` 對外，不直接碰別人的 model 或 repository，Phase 2 可以單獨替換某一塊。

### 5.1 目錄結構

```text
today-digest/
├── CLAUDE.md                  # 給 Claude Code 的專案規則（見第 12 節）
├── README.md                  # 含 Future work：Spring Boot 版本
├── docs/
│   ├── PRD.md                 # 本文件
│   └── architecture.png
├── docker-compose.yml         # db(pgvector) + app；redis/prometheus 以 profile 預留
├── Dockerfile
├── .env.example
├── pyproject.toml             # uv 管理依賴
├── alembic.ini
├── migrations/versions/0001_init.py
├── app/
│   ├── main.py                # FastAPI app、lifespan 啟動排程、掛 router
│   ├── config.py              # Settings（pydantic-settings）
│   ├── db.py                  # engine、SessionLocal、get_db
│   ├── common/                # errors.py（例外處理）、schemas.py（共用 DTO）
│   ├── article/               # models.py、repository.py、service.py、router.py
│   ├── ingestion/             # fetcher.py、service.py、jobs.py
│   ├── enrichment/            # llm.py、service.py、jobs.py、prompts/enrich.txt
│   ├── search/                # service.py（pgvector 查詢）
│   ├── cache/                 # base.py（Cache Protocol）、memory.py
│   ├── tracking/              # models.py、service.py（MVP 就記錄點擊）
│   ├── recommendation/        # base.py（Recommender Protocol）、latest.py、factory.py
│   ├── linebot/               # router.py、commands.py、flex.py
│   └── admin/                 # router.py（手動觸發抓取 / AI 處理）
└── tests/
    ├── unit/                  # mock LLM、解析、指令分派
    └── integration/           # testcontainers + pgvector
```

### 5.2 擴充點（Phase 2 只要填實作）

| 擴充點 | MVP 的樣子 | Phase 2 怎麼接 |
| --- | --- | --- |
| `Recommender` Protocol | `LatestRecommender`：回傳最新已處理新聞 | 新增 `EmbeddingRecommender`，用 `RECOMMENDER=embedding` 切換 |
| `click_event` 表 | LINE postback 點擊時寫入 | 當作使用者興趣向量的資料來源 |
| `Cache` Protocol | `MemoryCache`（TTL dict），已用在相關新聞查詢 | 新增 `RedisCache`，`CACHE_BACKEND=redis`，docker-compose 開 `cache` profile |
| `/healthz` | 回傳 DB 連線狀態 | 加 `prometheus-fastapi-instrumentator` + Grafana |
| 新聞來源 | `Settings.feeds` 清單 | 加來源只改設定 |
| LLM 供應商 | `enrichment/llm.py` 包一層 `LLMClient` | 換 Gemini 只改這個檔（注意 embedding 維度） |
| API 契約 | FastAPI 產生的 OpenAPI（`/openapi.json`） | Spring Boot 版本照同一份契約實作 |

```python
# app/recommendation/base.py
from typing import Protocol
from app.common.schemas import ArticleSummary

class Recommender(Protocol):
    def recommend(self, line_user_id: str, limit: int) -> list[ArticleSummary]: ...

# app/recommendation/latest.py
class LatestRecommender:
    def __init__(self, articles: ArticleService):
        self.articles = articles

    def recommend(self, line_user_id: str, limit: int) -> list[ArticleSummary]:
        return self.articles.latest_enriched(limit)   # Phase 2 由 EmbeddingRecommender 取代

# app/recommendation/factory.py
def get_recommender(db: Session = Depends(get_db)) -> Recommender:
    match settings.recommender:
        case "latest":
            return LatestRecommender(ArticleService(db))
        case other:
            raise ValueError(f"unknown recommender: {other}")   # Phase 2 加 "embedding"
```

## 6. 資料模型

兩張表：`article` 存新聞與 AI 結果，`click_event` 存 LINE 點擊（為 Phase 2 推薦累積資料）。由 Alembic migration `0001_init.py` 建立（用 `op.execute()` 執行下方 SQL），SQLAlchemy model 與此對應。

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE article (
    id              BIGSERIAL PRIMARY KEY,
    url             TEXT        NOT NULL UNIQUE,      -- 去重依據
    source          VARCHAR(64) NOT NULL,             -- 對應 app.feeds[].name
    title           TEXT        NOT NULL,
    content         TEXT,                             -- 已清掉 HTML 的內文/描述
    image_url       TEXT,
    published_at    TIMESTAMPTZ NOT NULL,
    summary         TEXT,
    category        VARCHAR(16),
    keywords        TEXT[],
    embedding       vector(1536),
    status          VARCHAR(16) NOT NULL DEFAULT 'PENDING',  -- PENDING | ENRICHED | FAILED
    retry_count     INT         NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    enriched_at     TIMESTAMPTZ
);

CREATE INDEX idx_article_status    ON article (status, created_at);
CREATE INDEX idx_article_published ON article (published_at DESC);
CREATE INDEX idx_article_category  ON article (category, published_at DESC);
CREATE INDEX idx_article_embedding ON article USING hnsw (embedding vector_cosine_ops);

CREATE TABLE click_event (
    id            BIGSERIAL PRIMARY KEY,
    line_user_id  VARCHAR(64) NOT NULL,
    article_id    BIGINT      NOT NULL REFERENCES article(id),
    action        VARCHAR(16) NOT NULL,   -- RELATED | OPEN
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_click_user ON click_event (line_user_id, created_at DESC);
```

**狀態機**：新文章為 `PENDING` → AI 處理成功變 `ENRICHED`；失敗則 `retry_count + 1`，達 3 次變 `FAILED` 並寫入 `last_error`。只有 `ENRICHED` 的文章會出現在 API 與 Bot。

**分類固定清單**（`app/article/models.py` 的 `class Category(StrEnum)`）：政治、國際、財經、科技、社會、生活、娛樂、運動、健康、其他。

```python
class Article(Base):
    __tablename__ = "article"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str]
    summary: Mapped[str | None]
    category: Mapped[str | None]
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    status: Mapped[str] = mapped_column(default="PENDING")
    # ...其餘欄位同上方 SQL
```

## 7. API 規格

所有 REST API 以 `/api` 為前綴，回傳 JSON。FastAPI 自動產生 Swagger UI（`/docs`）與 OpenAPI 規格（`/openapi.json`），每個端點都要有 `response_model`、`summary` 和範例，讓面試官打開就看得懂。列表類端點只回傳 `ENRICHED` 文章。

| 方法 | 路徑 | 說明 | 階段 |
| --- | --- | --- | --- |
| GET | `/api/articles?category=&page=0&size=20` | 依 `published_at` 新到舊分頁 | MVP |
| GET | `/api/articles/{id}` | 單篇詳情（含摘要、關鍵字） | MVP |
| GET | `/api/articles/{id}/related?limit=3` | 語意相關新聞，預設限最近 7 天 | MVP |
| GET | `/api/categories` | 分類清單 + 各分類文章數 | MVP |
| POST | `/api/admin/ingest` | 手動觸發一次 RSS 抓取（demo 用） | MVP |
| POST | `/api/admin/enrich` | 手動觸發一批 AI 處理 | MVP |
| GET | `/api/recommend?lineUserId=&limit=5` | 經 `Recommender` 回傳；MVP 等同最新新聞 | 鷹架 |
| POST | `/callback` | LINE webhook（驗 `X-Line-Signature`） | MVP |
| GET | `/healthz` | 健康檢查 | MVP |

`/api/admin/*` 以 header `X-Admin-Token` 保護（值來自環境變數）。

**回應範例**（`ArticleSummary`）：

```json
{
  "id": 128,
  "title": "範例新聞標題",
  "summary": "第一句。第二句。第三句。",
  "category": "財經",
  "keywords": ["關鍵字A", "關鍵字B"],
  "source": "cna",
  "url": "https://...",
  "imageUrl": null,
  "publishedAt": "2026-11-24T09:00:00+08:00",
  "similarity": 0.83
}
```

`similarity` 只在 `/related` 出現（= 1 − cosine distance）。錯誤一律回 `{"code": "ARTICLE_NOT_FOUND", "message": "..."}`，由 `app/common/errors.py 的 exception handler` 統一處理。

**相關新聞查詢**：

```sql
SELECT a.*, 1 - (a.embedding <=> t.embedding) AS similarity
FROM article a, (SELECT embedding FROM article WHERE id = :id) t
WHERE a.id <> :id
  AND a.status = 'ENRICHED'
  AND a.published_at > now() - make_interval(days => :days)
ORDER BY a.embedding <=> t.embedding
LIMIT :limit;
```

對應的 FastAPI 端點（SQLAlchemy + pgvector，加上 Cache 介面）：

```python
@router.get("/articles/{id}/related", response_model=list[ArticleSummary],
            summary="語意相關新聞")
def related(id: int, limit: int = Query(3, le=10),
            svc: SearchService = Depends(get_search_service)):
    return svc.related(id, limit)

class SearchService:
    def __init__(self, db: Session, cache: Cache):
        self.db, self.cache = db, cache

    def related(self, id: int, limit: int) -> list[ArticleSummary]:
        key = f"related:{id}:{limit}"
        if (hit := self.cache.get(key)) is not None:
            return hit
        target = self.db.get(Article, id)
        if target is None or target.embedding is None:
            raise ArticleNotFound(id)
        dist = Article.embedding.cosine_distance(target.embedding)
        stmt = (
            select(Article, (1 - dist).label("similarity"))
            .where(Article.id != id, Article.status == "ENRICHED",
                   Article.published_at > func.now() - timedelta(days=settings.related_window_days))
            .order_by(dist).limit(limit)
        )
        result = [ArticleSummary.from_row(a, sim) for a, sim in self.db.execute(stmt)]
        self.cache.set(key, result, ttl=600)
        return result
```

## 8. AI 處理規格

`enrichment/jobs.py` 由 APScheduler 每 60 秒執行，取最多 20 篇 `PENDING`（及 `retry_count < 3` 的失敗文章），逐篇呼叫 LLM 與 Embedding。單篇失敗不影響同批其他文章。同一個函式也由 `POST /api/admin/enrich` 呼叫，方便外部觸發。

| 項目 | 規格 |
| --- | --- |
| Chat 模型 | `gpt-4o-mini`（`Settings.chat_model`，可改），temperature 0.2 |
| Embedding 模型 | `text-embedding-3-small`，1536 維（`Settings.embedding_model`） |
| 輸入 | 標題 + 內文，內文截斷至 3,000 字 |
| 輸出 | Pydantic `EnrichResult`：`summary`（繁中 3 句、共 ≤ 120 字）、`category`（限分類清單）、`keywords`（≤ 5 個） |
| Embedding 輸入 | `title + "\n" + summary` |
| 驗證 | category 不在清單 → `其他`；summary 為空 → 視為失敗 |
| 失敗處理 | 例外時 `retry_count + 1`，寫入 `last_error`；達 3 次設 `FAILED` |
| 速率 | 每篇間隔 200 ms，避免打到 API rate limit |

**Prompt 模板**（`prompts/enrich.st`）：

```text
你是台灣新聞編輯。閱讀以下新聞，只輸出 JSON，不要其他文字。
- summary：繁體中文 3 句摘要，客觀、不加評論，共 120 字以內
- category：只能是 {categories} 其中一個
- keywords：最多 5 個關鍵字

標題：{title}
內文：{content}
```

**核心程式**：

```python
# app/enrichment/llm.py
class EnrichResult(BaseModel):
    summary: str
    category: Category
    keywords: list[str] = Field(max_length=5)

class LLMClient:
    def __init__(self, client: OpenAI):
        self.client = client
        self.prompt = (PROMPT_DIR / "enrich.txt").read_text(encoding="utf-8")

    def enrich(self, title: str, content: str) -> EnrichResult:
        resp = self.client.beta.chat.completions.parse(
            model=settings.chat_model,
            temperature=0.2,
            messages=[{"role": "user", "content": self.prompt.format(
                categories="、".join(Category), title=title, content=content[:3000])}],
            response_format=EnrichResult,
        )
        return resp.choices[0].message.parsed

    def embed(self, text: str) -> list[float]:
        return self.client.embeddings.create(
            model=settings.embedding_model, input=text).data[0].embedding

# app/enrichment/service.py
def enrich_pending(db: Session, llm: LLMClient) -> EnrichStats:
    stats = EnrichStats()
    for a in ArticleService(db).claim_pending(settings.enrich_batch_size):
        try:
            r = llm.enrich(a.title, a.content or "")
            a.summary, a.category, a.keywords = r.summary, r.category, r.keywords
            a.embedding = llm.embed(f"{a.title}\n{r.summary}")
            a.status, a.enriched_at = "ENRICHED", datetime.now(UTC)
            stats.ok += 1
        except Exception as e:
            a.retry_count += 1
            a.last_error = str(e)[:500]
            a.status = "FAILED" if a.retry_count >= settings.enrich_max_retry else "PENDING"
            stats.failed += 1
        db.commit()
        time.sleep(0.2)
    return stats
```

## 9. LINE Bot 互動流程

Bot 只用 reply API（不佔推播額度），每個事件交給 `commands.py` 的 `CommandRouter` 依輸入分派。使用 `line-bot-sdk` v3 的 `WebhookParser` 驗證 `X-Line-Signature`。

| 使用者輸入 | Bot 回覆 | 副作用 |
| --- | --- | --- |
| 「今日新聞」 | Flex carousel：5 則最新新聞（標題、摘要、分類、來源時間） | 無 |
| 分類名稱（如「科技」） | Flex carousel：該分類 5 則最新 | 無 |
| 點卡片「相關新聞」（postback `action=related&id=128`） | Flex carousel：3 則相關新聞 | 寫入 `click_event`（RELATED） |
| 點卡片「看原文」 | 開啟原始新聞網址（uri action） | 無（LINE 不回傳 uri 點擊） |
| 「推薦」 | 經 `Recommender` 回 5 則（MVP = 最新） | 無 |
| 其他文字 / 「說明」 | 文字說明 + Quick Reply（今日新聞、各分類） | 無 |
| 查無資料 | 「目前沒有新聞，稍後再試」 | 無 |

```python
# app/linebot/router.py
parser = WebhookParser(settings.line_channel_secret)

@router.post("/callback", include_in_schema=False)
async def callback(request: Request, x_line_signature: str = Header(...),
                   cmd: CommandRouter = Depends(get_command_router)):
    body = (await request.body()).decode()
    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(400, "invalid signature")

    for ev in events:
        if isinstance(ev, MessageEvent) and isinstance(ev.message, TextMessageContent):
            messages = cmd.on_text(ev.message.text.strip())
        elif isinstance(ev, PostbackEvent):
            messages = cmd.on_postback(ev.source.user_id, ev.postback.data)
        else:
            continue
        await line_api.reply_message(
            ReplyMessageRequest(reply_token=ev.reply_token, messages=messages))
    return "OK"
```

本地開發用 ngrok 暴露 `/callback`，並在 LINE Developers Console 設定 webhook URL。Flex Message 由 `flex.py` 組裝，卡片版型集中在單一函式 `article_bubble()`，方便之後調整。`CommandRouter` 只負責「輸入 → 要回的訊息」，不做網路呼叫，可以單獨做單元測試。

## 10. 設定與非功能需求

所有密鑰只從環境變數讀取，`.env` 列入 `.gitignore`，repo 只放 `.env.example`。

```bash
# .env.example
OPENAI_API_KEY=
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
ADMIN_TOKEN=change-me
DATABASE_URL=postgresql+psycopg://todaydigest:todaydigest@localhost:5432/todaydigest
CACHE_BACKEND=memory        # Phase 2: redis
RECOMMENDER=latest          # Phase 2: embedding
ENABLE_SCHEDULER=true       # 部署到 Render 時可關掉，改由外部呼叫 admin API
```

```python
# app/config.py
class Feed(BaseModel):
    name: str
    url: str

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    line_channel_secret: str
    line_channel_access_token: str
    admin_token: str
    database_url: str

    chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    enrich_batch_size: int = 20
    enrich_max_retry: int = 3
    ingest_interval_minutes: int = 30
    related_window_days: int = 7
    cache_backend: Literal["memory", "redis"] = "memory"
    recommender: Literal["latest"] = "latest"      # Phase 2 加 "embedding"
    enable_scheduler: bool = True
    feeds: list[Feed] = [
        Feed(name="cna", url="<RSS 網址，開發時確認>"),
        Feed(name="<第二個來源>", url="<RSS 網址>"),
    ]

settings = Settings()
```

**非功能需求**

- `docker compose up` 後 2 分鐘內可用；容器啟動時先跑 `alembic upgrade head`，不需手動建表。
- `/related` 在 5,000 篇文章內回應時間目標 < 300 ms（HNSW 索引）。
- LINE webhook 需在 1 秒內回覆；不在 webhook 內呼叫 LLM，只讀 DB。
- RSS 來源連線失敗只記 log，不中斷其他來源。
- 使用 `logging`（JSON 格式），每批抓取 / AI 處理記錄成功與失敗篇數。
- 程式碼通過 `ruff check` 與 `ruff format`；公開函式都有 type hints。

## 11. 驗收標準

以下全部勾選才算 MVP 完成；每項都應有對應的自動測試或可重現的手動步驟（寫在 README）。

- [ ] F1：`POST /api/admin/ingest` 後 DB 出現文章；重複執行不產生重複 `url`
- [ ] F1：其中一個 RSS 來源無法連線時，其他來源仍正常抓取
- [ ] F2：`POST /api/admin/enrich` 後文章變 `ENRICHED`，有 3 句摘要、合法分類、embedding
- [ ] F2：LLM 拋例外時 `retry_count` 遞增，3 次後變 `FAILED`（用 fake `LLMClient` 測試）
- [ ] F3：`/api/articles` 分頁、分類篩選正確；不存在的 id 回 404 + 錯誤碼
- [ ] F3：`/related` 不含自己、依相似度排序、只含 7 天內文章（testcontainers + pgvector 測試）
- [ ] F3：`/docs` 可以直接打所有 `/api` 端點，每個端點都有說明與回應範例
- [ ] F4：手機傳「今日新聞」收到 5 張卡片；點「相關新聞」收到 3 張並寫入 `click_event`
- [ ] F4：簽章錯誤的 webhook 請求回 400
- [ ] F5：乾淨環境 `cp .env.example .env` → 填密鑰 → `docker compose up` 即可運作
- [ ] F5：README 含架構圖、啟動步驟、API 清單、demo 影片連結、Future work（推薦、Redis、監控、Spring Boot 版本）
- [ ] 鷹架：`uv run pytest` 全綠、`ruff check` 無錯誤；`CACHE_BACKEND` 與 `RECOMMENDER` 可切換且有預設值

## 12. 給 Claude Code 的開發指引

把本文件匯出成 `docs/PRD.md` 放進 repo，再用 superpowers 的 brainstorming → writing-plans → executing-plans 流程開發。brainstorming 階段只確認本 PRD 未定的細節（RSS 來源、卡片版型），不重新設計架構。

**實作順序**（每步完成就 commit，並讓測試保持綠燈）

1. 用 uv 建專案、模組結構、`config.py`、`db.py`、`docker-compose.yml`（`pgvector/pgvector:pg16`）、Alembic `0001_init`、`.env.example`、`/healthz`
2. `article` 模組：model、repository、service、router、例外處理，確認 `/docs` 正常
3. `ingestion`：feedparser 解析 RSS、BeautifulSoup 清 HTML、以 `url` 去重（`ON CONFLICT DO NOTHING`）、admin 觸發
4. `enrichment`：`LLMClient`、狀態機與重試（測試用 fake `LLMClient`）
5. `cache` + `search`：`MemoryCache`、相關新聞查詢，testcontainers 整合測試
6. `tracking` + `recommendation`：`click_event`、`Recommender` Protocol 與 `LatestRecommender`、`/api/recommend`
7. APScheduler：在 lifespan 啟動抓取（30 分）與 AI 處理（60 秒）兩個 job，受 `ENABLE_SCHEDULER` 控制
8. `linebot`：`/callback`、`CommandRouter`、`flex.py`
9. Dockerfile（multi-stage、啟動前 `alembic upgrade head`）、README、架構圖，跑完第 11 節驗收清單

**建議的 `CLAUDE.md`**

```markdown
# TodayDigest
- 規格以 docs/PRD.md 為準；與 PRD 衝突時先問，不自行改架構。
- Python 3.12、FastAPI、SQLAlchemy 2（同步 Session）、Alembic、openai SDK、line-bot-sdk v3、uv。
- 模組依功能切；跨模組只呼叫 service.py，不直接用別人的 model/repository。
- 依賴一律用 FastAPI Depends 注入，方便測試替換。
- 新功能先寫測試（TDD）；DB 相關用 testcontainers，LLM 一律用 fake。
- 密鑰只用環境變數，禁止寫進程式或 commit。
- Phase 2 功能不要提前實作，只保留 PRD 第 5.2 節列出的擴充點。
- 指令：uv run pytest、uv run ruff check .、docker compose up -d db、uv run alembic upgrade head、uv run uvicorn app.main:app --reload
```

**README 的 Future work 範本**

```markdown
## Future work
- 個人化推薦：以使用者點擊過的文章 embedding 平均當興趣向量，搭配時間衰減排序（`Recommender` 介面已預留）。
- Redis 快取、Prometheus/Grafana 監控、GitHub Actions CI。
- Spring Boot 版本：本專案的 API 以 OpenAPI（`/openapi.json`）定義，計畫用 Java 21 + Spring Boot 3 + Spring AI
  依同一份契約重寫（從 `linebot` 或 `search` 模組開始），比較兩種生態在開發速度、記憶體與啟動時間上的差異。
```

**啟動用 prompt**：

```text
請讀 docs/PRD.md 與 CLAUDE.md。依第 12 節的實作順序用 writing-plans 產出計畫，
每個步驟對應第 11 節的驗收項目。只做 MVP（F1–F5）與第 5.2 節的擴充點，
不要實作 Phase 2。計畫完成後先給我看。
```

## 13. Phase 2 擴充規劃

履歷繳交後用 2–3 天完成 1–5，依序逐項交給 Claude Code；每項只動「改動位置」欄列出的地方。第 6 項是有時間再做的選做項目。

| 順序 | 項目 | 改動位置 | 做法 | 預估 |
| --- | --- | --- | --- | --- |
| 1 | P1 個人化推薦 | `recommendation/embedding.py`、`factory.py` | 取使用者最近 20 次點擊文章的 embedding 平均當興趣向量；分數 = 相似度 × exp(−小時數 / 24)；無點擊時退回最新 | 1 天 |
| 2 | P2 Redis 快取 | `cache/redis.py`、`docker-compose.yml` | 用 `redis-py` 實作 `Cache` Protocol，`CACHE_BACKEND=redis`，TTL 10 分鐘 | 0.5 天 |
| 3 | P4 GitHub Actions | `.github/workflows/ci.yml`、`ingest.yml` | push / PR 跑 `ruff` + `pytest`；另一個 schedule workflow 每 30 分鐘呼叫 admin API 抓取與 AI 處理 | 0.5 天 |
| 4 | P3 監控 | `main.py`、`docker-compose.yml` | `prometheus-fastapi-instrumentator` + 自訂指標（抓取篇數、AI 成功 / 失敗數、LLM 延遲）；Grafana 一張儀表板 | 0.5 天 |
| 5 | P5 Render 部署 | `render.yaml` | 免費 web service + 免費 Render Postgres（啟用 pgvector，30 天後到期需重建）；`ENABLE_SCHEDULER=false`，改由第 3 項的 schedule workflow 觸發；webhook 改指向正式網址 | 0.5 天 |
| 6 | P6 Spring Boot 版本（選做） | 新資料夾 `spring/` | 依 `/openapi.json` 的契約，用 Java 21 + Spring Boot 3 + Spring AI 重寫一個模組（建議從 `search` 開始），共用同一個 PostgreSQL | 2–3 天 |

推薦效果可以做一個簡單的離線評估：保留每個使用者最後一次點擊，看它是否出現在推薦結果前 5 名（Hit@5），結果寫進 README。
