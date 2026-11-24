from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.admin.router import router as admin_router
from app.article.router import router as article_router
from app.common.errors import register_exception_handlers
from app.config import settings
from app.db import get_db
from app.enrichment.jobs import run_enrich_job
from app.ingestion.jobs import run_ingest_job
from app.recommendation.router import router as recommendation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if settings.enable_scheduler:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            run_ingest_job, "interval", minutes=settings.ingest_interval_minutes, id="ingest"
        )
        scheduler.add_job(run_enrich_job, "interval", seconds=60, id="enrich")
        scheduler.start()
    yield
    if scheduler is not None:
        scheduler.shutdown()


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
