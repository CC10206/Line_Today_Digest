from app.db import SessionLocal
from app.ingestion.service import ingest


def run_ingest_job() -> None:
    with SessionLocal() as db:
        ingest(db)
