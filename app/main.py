from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: 啟動 APScheduler（ingestion 30 分、enrichment 60 秒），受 settings.enable_scheduler 控制
    yield


app = FastAPI(title="TodayDigest", lifespan=lifespan)

# TODO: 掛上各模組 router
# app.include_router(article.router)
# app.include_router(admin.router)
# app.include_router(linebot.router)


@app.get("/healthz")
def healthz():
    # TODO: 檢查 DB 連線狀態
    return {"status": "ok"}
