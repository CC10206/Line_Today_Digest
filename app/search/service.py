from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.article.models import Article
from app.cache.base import Cache
from app.common.errors import ArticleNotFound
from app.common.schemas import ArticleSummary
from app.config import settings


class SearchService:
    def __init__(self, db: Session, cache: Cache):
        self.db, self.cache = db, cache

    def related(self, id: int, limit: int) -> list[ArticleSummary]:
        key = f"related:{id}:{limit}"
        if (hit := self.cache.get(key)) is not None:
            return hit
        target = self.db.get(Article, id)
        if target is None or target.embedding is None:
            raise ArticleNotFound(id)
        dist = Article.embedding.cosine_distance(target.embedding)
        stmt = (
            select(Article, (1 - dist).label("similarity"))
            .where(
                Article.id != id,
                Article.status == "ENRICHED",
                Article.published_at
                > func.now() - timedelta(days=settings.related_window_days),
                dist <= (1 - settings.related_min_similarity),
            )
            .order_by(dist)
            .limit(limit)
        )
        result = [ArticleSummary.from_row(a, sim) for a, sim in self.db.execute(stmt)]
        self.cache.set(key, result, ttl=600)
        return result
