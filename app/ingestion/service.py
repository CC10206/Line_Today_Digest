import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.article.repository import ArticleRepository
from app.ingestion.fetcher import fetch_all

logger = logging.getLogger(__name__)


@dataclass
class IngestStats:
    fetched: dict[str, int]
    inserted: dict[str, int]


def ingest(db: Session) -> IngestStats:
    repo = ArticleRepository(db)
    fetched_by_source = fetch_all()
    fetched: dict[str, int] = {}
    inserted: dict[str, int] = {}
    for source, rows in fetched_by_source.items():
        fetched[source] = len(rows)
        inserted[source] = repo.upsert_on_conflict(rows)
    logger.info("ingest done: fetched=%s inserted=%s", fetched, inserted)
    return IngestStats(fetched=fetched, inserted=inserted)
