from app.db import SessionLocal
from app.enrichment.llm import get_llm_client
from app.enrichment.service import enrich_pending


def run_enrich_job() -> None:
    with SessionLocal() as db:
        llm = get_llm_client()
        enrich_pending(db, llm)
