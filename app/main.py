from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db


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
def healthz(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "error"}
    return {"status": "ok"}
