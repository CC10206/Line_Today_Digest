from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.admin.router import router as admin_router
from app.article.router import router as article_router
from app.common.errors import register_exception_handlers
from app.db import get_db
from app.recommendation.router import router as recommendation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: 啟動 APScheduler（ingestion 30 分、enrichment 60 秒），受 settings.enable_scheduler 控制
    yield


app = FastAPI(title="TodayDigest", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(article_router)
app.include_router(admin_router)
app.include_router(recommendation_router)

# TODO: 掛上剩下的模組 router
# app.include_router(linebot.router)


@app.get("/healthz")
def healthz(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "error"}
    return {"status": "ok"}
