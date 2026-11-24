from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
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
