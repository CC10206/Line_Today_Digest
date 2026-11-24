from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.enrichment.llm import LLMClient, get_llm_client
from app.enrichment.service import enrich_pending
from app.ingestion.service import ingest

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_token(x_admin_token: str = Header(...)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="invalid admin token")


@router.post(
    "/ingest",
    summary="手動觸發一次 RSS 抓取（demo 用）",
    dependencies=[Depends(verify_admin_token)],
)
def trigger_ingest(db: Session = Depends(get_db)) -> dict:
    stats = ingest(db)
    return {"fetched": stats.fetched, "inserted": stats.inserted}


@router.post(
    "/enrich",
    summary="手動觸發一批 AI 處理（摘要、分類、embedding）",
    dependencies=[Depends(verify_admin_token)],
)
def trigger_enrich(
    db: Session = Depends(get_db), llm: LLMClient = Depends(get_llm_client)
) -> dict:
    stats = enrich_pending(db, llm)
    return {"ok": stats.ok, "failed": stats.failed}
