import time
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.article.service import ArticleService
from app.config import settings
from app.enrichment.llm import LLMClient


@dataclass
class EnrichStats:
    ok: int = 0
    failed: int = 0


def enrich_pending(db: Session, llm: LLMClient) -> EnrichStats:
    stats = EnrichStats()
    for a in ArticleService(db).claim_pending(settings.enrich_batch_size):
        try:
            r = llm.enrich(a.title, a.content or "")
            a.summary, a.category, a.keywords = r.summary, r.category, r.keywords
            a.embedding = llm.embed(f"{a.title}\n{r.summary}")
            a.status, a.enriched_at = "ENRICHED", datetime.now(UTC)
            stats.ok += 1
        except Exception as e:
            a.retry_count += 1
            a.last_error = str(e)[:500]
            a.status = "FAILED" if a.retry_count >= settings.enrich_max_retry else "PENDING"
            stats.failed += 1
        db.commit()
        time.sleep(0.2)
    return stats
