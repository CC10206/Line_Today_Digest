# TodayDigest
- 規格以 docs/PRD.md 為準；與 PRD 衝突時先問，不自行改架構。
- Python 3.12、FastAPI、SQLAlchemy 2（同步 Session）、Alembic、openai SDK、line-bot-sdk v3、uv。
- 模組依功能切；跨模組只呼叫 service.py，不直接用別人的 model/repository。
- 依賴一律用 FastAPI Depends 注入，方便測試替換。
- 新功能先寫測試（TDD）；DB 相關用 testcontainers，LLM 一律用 fake。
- 密鑰只用環境變數，禁止寫進程式或 commit。
- Phase 2 功能不要提前實作，只保留 PRD 第 5.2 節列出的擴充點。
- 指令：uv run pytest、uv run ruff check .、docker compose up -d db、uv run alembic upgrade head、uv run uvicorn app.main:app --reload
